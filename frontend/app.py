import os
import streamlit as st
import json
import time
import openai
from dotenv import load_dotenv


st.set_page_config(
    page_title="SaaS 전략 타당성 검증 서비스",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("OpenAI API Key가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

# --- 1. LLM 분석을 위한 기준 데이터 (이전 단계에서 도출된 KPI) ---
# 이 JSON 데이터가 '우리만의 데이터베이스' 역할을 하며, LLM 호출 시 프롬프트에 포함됩니다.
CUSTOM_DATABASE_KPI_JSON = """
{
  "Overall_Churn_Metrics": {
    "Overall_Retention_Rate": "50.11%",
    "Overall_Churn_Rate": "49.89%"
  },
  "Usage_Frequency_Retention": [
    {"Frequency_Group": "Low (0-7)", "Retention_Rate": "33.72%"},
    {"Frequency_Group": "Medium (8-15)", "Retention_Rate": "49.98%"},
    {"Frequency_Group": "High (16-23)", "Retention_Rate": "62.40%"},
    {"Frequency_Group": "Highest (24-31)", "Retention_Rate": "83.91%"}
  ],
  "Subscription_Performance": [
    {"Type": "Basic", "Retention_Rate": "49.61%", "Avg_Total_Spend": 498.44},
    {"Type": "Standard", "Retention_Rate": "49.90%", "Avg_Total_Spend": 501.07},
    {"Type": "Premium", "Retention_Rate": "50.81%", "Avg_Total_Spend": 498.92}
  ],
  "Contract_Length_Retention": [
    {"Length": "Monthly", "Retention_Rate": "37.56%"},
    {"Length": "Quarterly", "Retention_Rate": "50.08%"},
    {"Length": "Annual", "Retention_Rate": "62.77%"}
  ],
  "Support_Calls_Risk": [
    {"Call_Count": "0-3 Calls (Low)", "Churn_Rate": "38.50%"},
    {"Call_Count": "4-7 Calls (Medium)", "Churn_Rate": "49.98%"},
    {"Call_Count": "8-10 Calls (High)", "Churn_Rate": "85.87%"}
  ],
  "Payment_Delay_Risk": [
    {"Delay_Days": "0-10 Days", "Churn_Rate": "45.10%"},
    {"Delay_Days": "11-20 Days", "Churn_Rate": "49.97%"},
    {"Delay_Days": "21+ Days", "Churn_Rate": "55.10%"}
  ]
}
"""

# --- 2. LLM 분석 함수 (API 호출 로직) ---

def run_llm_analysis(strategy_data, kpi_data):
    """
    OpenAI GPT 모델을 호출하여 비즈니스 전략의 타당성을 검증하고 결과를 반환하는 실제 함수.
    """
    if not openai.api_key:
        # API 키가 없으면 분석을 수행하지 않고 에러를 반환
        return None, None
        
        
    client = openai.OpenAI()
    # 1. 상세 프롬프트 구성
    system_prompt = (
        "당신은 SaaS 비즈니스 전략 전문가입니다. 제공된 '빅데이터 KPI'를 근거로 '입력 전략'을 분석하고, "
        "요청된 '타당성 점수(100점 만점)', '성공 확률(%)', '분석 요약', '대안 전략'을 **반드시 JSON 형식**으로 반환해야 합니다. "
        "분석 시, 특히 Usage Frequency (고사용량 기능 유도), Contract Length (Monthly), Subscription Performance (Standard 업셀) KPI를 중점적으로 활용하십시오."
    )
    
    user_prompt = f"""
    [빅데이터 KPI (JSON)]
    {kpi_data}

    [입력 전략]
    - 대상 타겟: {strategy_data['target_audience']}
    - 핵심 기능: {strategy_data['key_feature']}
    - 계약 형태: {strategy_data['contract_type']}
    - 전략: {strategy_data['ai_strategy']}

    [출력 형식]
    결과는 반드시 다음 구조를 가진 JSON 문자열로만 반환해야 합니다:
    {{
      "validity_score": (int, 0부터 100 사이),
      "success_probability_percent": (int, 0부터 100 사이),
      "analysis_summary": (string),
      "alternative_strategies": [
        (string: 대안 전략 1),
        (string: 대안 전략 2)
      ]
    }}
    """
    
    try:
        # 2. LLM 호출
        response = client.chat.completions.create(
            # 분석의 정확성을 위해 gpt-4-turbo 등 최신 모델을 추천합니다.
            model="gpt-4-turbo-preview",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        
        )
        
        # 3. 결과 파싱
        json_string = response.choices[0].message.content
        analysis_result = json.loads(json_string)
        
        return analysis_result, json_string

    except Exception as e:
        # API 호출 또는 JSON 파싱 오류 처리
        st.error(f"LLM 분석 중 오류가 발생했습니다. OpenAI API Key, 네트워크 연결, 또는 반환된 JSON 형식(파싱 오류)을 확인해주세요: {e}")
        # 오류 발생 시 빈 결과 반환
        return None, None

# --- 3. Streamlit UI 레이아웃 설정 ---


st.title("🌟 AI 비즈니스 전략 타당성 검증 서비스")
st.markdown("---")

# 레이아웃을 2개의 컬럼으로 분할 (입력 / 결과)
col_input, col_result = st.columns([1, 2])

# ==================================
# 1. 입력 섹션
# ==================================
with col_input:
    st.header("1. 전략 입력")
    
    # 입력 필드
    with st.form("strategy_form"):
        st.subheader("비즈니스 환경")
        business_sector = st.selectbox("비즈니스 분야", ["SaaS", "e-Commerce", "Contents", "Fintech"])
        target_audience = st.selectbox("대상 타겟", ["SMB (Small to Midsize Business)", "1인 기업", "Enterprise", "개인 사용자"])
        
        st.subheader("AI 추천 전략 상세")
        ai_strategy = st.text_input(
            "AI 추천 핵심 전략 (예: Freemium → Standard 업셀)", 
            value="Freemium → Standard 업셀"
        )
        key_feature = st.text_area(
            "핵심 기능 요약 (예: AI 자동화 + 고사용량 기능 유도)", 
            value="AI 자동화 기능을 통한 생산성 증대, 고사용량 기능 유도"
        )
        contract_type = st.selectbox("추천 계약 형태", ["Monthly", "Quarterly", "Annual"])

        # 숨겨진 데이터베이스 필드 (정보 전달용)
        st.caption("※ 전략 평가는 사전 정의된 빅데이터 KPI를 기반으로 LLM이 진행합니다.")
        
        # 폼 제출 버튼
        submit_button = st.form_submit_button("🚀 전략 타당성 검증 시작")

# ==================================
# 2. 결과 섹션
# ==================================
with col_result:
    st.header("2. 분석 결과")
    
    # 검증 버튼 클릭 시 로직
    if submit_button:
        if not openai.api_key:
            st.error("OpenAI API Key가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        else:   
            
            with st.spinner('OpenAI LLM을 호출하고, 기준 데이터를 기반으로 전략 타당성을 검증 중입니다...'):
                time.sleep(1) # 시연을 위한 대기 시간
            
            # 입력 데이터 구조화
                input_data = {
                    "business_sector": business_sector,
                    "target_audience": target_audience,
                    "ai_strategy": ai_strategy,
                    "key_feature": key_feature,
                    "contract_type": contract_type
                }
            
            # LLM 분석 실행 (Placeholder 함수 호출)
                analysis_result, raw_json_report = run_llm_analysis(input_data, CUSTOM_DATABASE_KPI_JSON)
            
        # **--- 이 부분이 수정됩니다 ---**
            if analysis_result: # 분석 결과가 성공적으로 반환되었을 때만 출력
                st.success("✅ 전략 검증 완료!")

                # 3. 핵심 결과 출력 (KPI Dashboard 형태)
                st.subheader("핵심 지표")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="타당성 점수 (100점 만점)", value=f"{analysis_result['validity_score']} 점")
                with col2:
                    st.metric(label="예상 성공 확률", value=f"{analysis_result['success_probability_percent']} %")
                with col3:
                    st.markdown(f"**기준 데이터**")
                    st.write("SaaS Churn Dataset 기반 KPI")
                st.subheader("분석 요약")
                st.info(analysis_result['analysis_summary'])
        
                st.subheader("대안 전략 (리스크 완화)")
                for i, alt in enumerate(analysis_result['alternative_strategies']):
                    st.markdown(f"**대안 {i+1}:** {alt}")
        
                st.markdown("---")

        # 4. 보고서 형식 선택 및 다운로드
                st.subheader("3. 결과 보고서 다운로드")
        
                output_format = st.radio(
                    "원하는 보고서 형식을 선택하세요:", 
                    ("텍스트 파일 (TXT)", "리포트 (JSON 파일)", "엑셀 파일 (CSV 형식)")
                )

        # 다운로드 버튼 (실제 파일 생성 로직 필요)
                if output_format == "리포트 (JSON 파일)":
                    st.download_button(
                        label="JSON 파일 다운로드",
                        data=raw_json_report,
                        file_name="strategy_validation_report.json",
                        mime="application/json"
                    )
                elif output_format == "텍스트 파일 (TXT)":
                    # 텍스트 보고서 생성 로직 (요약 정보 포함)
                    text_report = f"""
        [SaaS 비즈니스 전략 타당성 검증 리포트]

--- 입력 정보 ---
전략: {input_data['ai_strategy']}
타겟: {input_data['target_audience']}
계약 형태: {input_data['contract_type']}

--- 분석 결과 ---
타당성 점수: {analysis_result['validity_score']}점
예상 성공 확률: {analysis_result['success_probability_percent']}%

[요약]
{analysis_result['analysis_summary']}

[대안 전략]
{'\n'.join([f'- {alt}' for alt in analysis_result['alternative_strategies']])}
"""
                    st.download_button(
                        label="텍스트 파일 다운로드",
                        data=text_report,
                        file_name="strategy_validation_report.txt",
                        mime="text/plain"
                    )
                elif output_format == "엑셀 파일 (CSV 형식)":
                    # 엑셀/CSV 데이터 생성 로직 (주요 지표만 요약)
                    csv_data = f"""
지표,값
전략, {input_data['ai_strategy']}
타겟, {input_data['target_audience']}
타당성 점수, {analysis_result['validity_score']}
성공 확률, {analysis_result['success_probability_percent']}%
대안 1, "{analysis_result['alternative_strategies'][0]}"
대안 2, "{analysis_result['alternative_strategies'][1]}"
"""
                    st.download_button(
                    label="CSV 파일 다운로드",
                    data=csv_data,
                    file_name="strategy_validation_summary.csv",
                    mime="text/csv"
                    )
    else:
        st.info("왼쪽에서 비즈니스 전략을 입력하고 '검증 시작' 버튼을 눌러주세요.")