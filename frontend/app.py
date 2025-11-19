import streamlit as st
import time
import json 
import os   
from datetime import datetime 

# 정의한 모듈 및 클래스 로드
from data_loader import DataLoader
from analysis_engine import AnalysisEngine
from config import AppConfig

# ----------------------------------------------------
# 📌 0. 전역 설정 및 세션 상태 초기화
# ----------------------------------------------------
st.set_page_config(
    page_title="AI 비즈니스 전략 타당성 검증 서비스",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Streamlit 세션 상태를 초기화합니다."""
    if 'analysis_ran' not in st.session_state:
        st.session_state['analysis_ran'] = False
        st.session_state['analysis_result'] = None
        st.session_state['raw_json_report'] = None
        st.session_state['input_data'] = None
        st.session_state['file_name_for_display'] = None
        st.session_state['output_format'] = "텍스트 파일 (TXT)" 

# ----------------------------------------------------
# 📌 1. Streamlit 앱 클래스 (View & Controller)
# ----------------------------------------------------
class StreamlitAppView:
    def __init__(self):
        self.data_loader = DataLoader()
        self.analysis_engine = AnalysisEngine()
        self.BUSINESS_FILE_MAPPING = AppConfig.BUSINESS_FILE_MAPPING
        
        initialize_session_state()

        if not AppConfig.OPENAI_API_KEY:
            st.error("🚨 OpenAI API Key가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    def run(self):
        """앱의 메인 실행 흐름을 정의합니다."""
        st.title("🌟 AI 비즈니스 전략 타당성 검증 서비스")
        st.markdown("---")

        col_input, col_result = st.columns([1, 2])

        with col_input:
            self._render_input_form()

        with col_result:
            # 🚨 이 부분의 메서드가 클래스 내부에 정의되어 있어야 합니다. 🚨
            self._render_result_section()
    
    def _render_input_form(self):
        """전략 입력 폼을 렌더링합니다."""
        st.header("1. 전략 입력")
        
        current_business_sector = st.selectbox(
            "비즈니스 분야", 
            list(self.BUSINESS_FILE_MAPPING.keys()),
            key="sector_select"
        )
        
        # 데이터 로더를 통해 컬럼 목록 로드
        raw_data_on_load, column_list, _ = self.data_loader.load_raw_data(current_business_sector)
        
        # 오류 처리 로직 (컬럼 로드 실패 시)
        is_load_error = column_list is None or not column_list or "Error:" in column_list[0]
        if is_load_error:
            error_detail = raw_data_on_load.replace("Error: ", "") if raw_data_on_load.startswith("Error:") else (column_list[0].replace("Error: ", "") if column_list else "알 수 없는 오류")
            target_columns = ["컬럼 로드 실패 (파일 확인 필요)", "Error"]
            st.error(f"컬럼 로드 오류: {error_detail}")
        else:
            target_columns = column_list
        
        with st.form("strategy_form"):
            st.subheader("AI 추천 전략 상세")
            
            target_column = st.selectbox(
                "개선 타겟 컬럼 (KPI)", 
                target_columns,
                index=0 
            )
            
            # 🌟 Placeholder 텍스트 변수 정의 🌟
            strategy_placeholder = f"예시: {target_column}을(를) 높이기 위해 30일 이내 해지 고객에게 맞춤형 쿠폰을 발송합니다."
            key_feature_placeholder = "예시: AI 기반 이탈 예측 모델을 활용하여 이탈 징후 고객을 실시간 식별 및 자동화된 마케팅 캠페인 실행"
            
            ai_strategy = st.text_input(
                "AI 추천 핵심 전략", 
                placeholder=strategy_placeholder, 
                key="strategy_input"
            )
            
            key_feature = st.text_area(
                "핵심 기능 요약", 
                placeholder=key_feature_placeholder,
                key="key_feature_input"
            )
            
            contract_type = st.selectbox("전략 목표 기간", ["Monthly", "Quarterly", "Annual"])

            st.caption(f"※ 분석 시 LLM은 **{target_column}** 컬럼을 개선 대상으로 가정하고 타당성을 검증합니다.")
            
            submit_button = st.form_submit_button("🚀 전략 타당성 검증 시작")
            
            if submit_button:
                self._handle_submit(current_business_sector, target_column, ai_strategy, key_feature, contract_type, strategy_placeholder, key_feature_placeholder)

    def _handle_submit(self, business_sector, target_column, ai_strategy, key_feature, contract_type, strategy_placeholder, key_feature_placeholder):
        """폼 제출 시 분석을 실행하고 결과를 세션 상태에 저장하고, 로그를 저장합니다."""
        
        if not AppConfig.OPENAI_API_KEY:
            return

        with st.spinner(f"'{business_sector}' 분야 원시 데이터를 로드하고 LLM이 분석 중입니다..."):
            
            # 🌟 입력값 검증 및 기본값 설정: 빈 값일 경우 placeholder 사용 🌟
            final_ai_strategy = ai_strategy if ai_strategy else strategy_placeholder
            final_key_feature = key_feature if key_feature else key_feature_placeholder
            
            input_data = {
                "business_sector": business_sector,
                "target_column": target_column,
                "ai_strategy": final_ai_strategy, 
                "key_feature": final_key_feature, 
                "contract_type": contract_type
            }
            
            raw_data, _, file_name_for_display = self.data_loader.load_raw_data(input_data['business_sector'])
            
            if raw_data.startswith("Error:") or target_column in ["컬럼 로드 실패 (파일 확인 필요)", "Error"]:
                st.error(f"데이터 또는 컬럼 로드 오류로 인해 분석을 시작할 수 없습니다. 오류: {raw_data.replace('Error: ', '')}")
                st.session_state['analysis_ran'] = False
            else:
                # AnalysisEngine 호출
                analysis_result_temp, raw_json_report_temp = self.analysis_engine.run_analysis(input_data, raw_data)
                time.sleep(1) 
                
                if analysis_result_temp:
                    # 🌟🌟🌟 자동 로컬 디렉토리 저장 로직 시작 🌟🌟🌟
                    self._save_analysis_log(input_data, analysis_result_temp, raw_json_report_temp)
                    # 🌟🌟🌟 자동 로컬 디렉토리 저장 로직 끝 🌟🌟🌟

                    # 결과 세션 상태에 저장
                    st.session_state['analysis_ran'] = True
                    st.session_state['analysis_result'] = analysis_result_temp
                    st.session_state['raw_json_report'] = raw_json_report_temp
                    st.session_state['input_data'] = input_data
                    st.session_state['file_name_for_display'] = file_name_for_display
                else:
                    st.session_state['analysis_ran'] = False
                    st.error("LLM 분석에 실패했습니다. API 키 또는 네트워크 상태를 확인하세요.")


    def _save_analysis_log(self, input_data, analysis_result, raw_json_report):
        """
        분석 결과를 'analysis_logs/YYYYMMDD_HHMMSS' 폴더에 저장합니다.
        """
        # 1. 파일 이름 및 폴더 이름 생성
        timestamp_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name_base = input_data['business_sector'].replace(' ', '_')
        
        # 2. 로그 디렉토리 경로 설정
        base_log_dir = "analysis_logs"
        full_log_dir = os.path.join(base_log_dir, timestamp_folder)
        
        # 3. 폴더 생성 (analysis_logs와 날짜/시간 폴더 모두 없으면 생성)
        try:
            os.makedirs(full_log_dir, exist_ok=True) 
        except Exception as e:
            st.error(f"로그 디렉토리 생성 실패 ({full_log_dir}): {e}")
            return
        
        # LLM 분석 결과에서 안전하게 값 추출 (로그 파일 생성을 위해)
        validity_score_dl = analysis_result.get('validity_score', 'N/A')
        success_probability_dl = analysis_result.get('success_probability_percent', 'N/A')
        alternative_strategies_list = analysis_result.get('alternative_strategies', ['N/A'])
        alt_1_dl = alternative_strategies_list[0] if len(alternative_strategies_list) > 0 else 'N/A'
        alt_2_dl = alternative_strategies_list[1] if len(alternative_strategies_list) > 1 else 'N/A'
        analysis_summary_dl = analysis_result.get('analysis_summary', '분석 요약 정보를 불러오지 못했습니다.')


        # --- 4. JSON 파일 저장 ---
        try:
            json_file_path = os.path.join(full_log_dir, f"{file_name_base}.json")
            with open(json_file_path, 'w', encoding='utf-8') as f:
                f.write(raw_json_report)
        except Exception as e:
            st.error(f"JSON 로그 저장 실패: {e}")

        # --- 5. TXT 파일 저장 ---
        text_report = f"""
[AI 비즈니스 전략 타당성 검증 리포트 - {input_data['business_sector']}]

--- 입력 정보 ---
비즈니스 분야: {input_data['business_sector']}
개선 타겟 컬럼: {input_data['target_column']} 
AI 추천 핵심 전략: {input_data['ai_strategy']}
핵심 기능 요약: {input_data['key_feature']}
전략 목표 기간: {input_data['contract_type']} 
--- 분석 결과 ---
타당성 점수: {validity_score_dl}점
예상 성공 확률: {success_probability_dl}%

[요약]
{analysis_summary_dl}

[대안 전략]
- {alt_1_dl}
- {alt_2_dl}
"""
        try:
            txt_file_path = os.path.join(full_log_dir, f"{file_name_base}.txt")
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(text_report.strip())
        except Exception as e:
            st.error(f"TXT 로그 저장 실패: {e}")

        # --- 6. CSV 파일 저장 ---
        csv_data = f"""
지표,값
비즈니스 분야, "{input_data['business_sector']}"
개선 타겟 컬럼, "{input_data['target_column']}"
AI 추천 핵심 전략, "{input_data['ai_strategy']}"
핵심 기능 요약, "{input_data['key_feature']}"
전략 목표 기간, {input_data['contract_type']}
타당성 점수, {validity_score_dl}
성공 확률, {success_probability_dl}
대안 1, "{alt_1_dl}"
대안 2, "{alt_2_dl}"
"""
        try:
            csv_file_path = os.path.join(full_log_dir, f"{file_name_base}.csv")
            with open(csv_file_path, 'w', encoding='utf-8') as f:
                f.write(csv_data.strip())
            
            # 저장 성공 시 Streamlit Toast 알림
            st.toast(f"✅ 분석 결과가 analysis_logs/{timestamp_folder}/{file_name_base}.* 파일로 저장되었습니다.", icon="💾")
        except Exception as e:
            st.error(f"CSV 로그 저장 실패: {e}")

    # 📌 필수 메서드: _render_result_section 
    def _render_result_section(self):
        """분석 결과 및 다운로드 섹션을 렌더링합니다."""
        st.header("2. 분석 결과")
        
        if st.session_state['analysis_ran']:
            # 세션 상태에서 데이터 언팩
            analysis_result = st.session_state['analysis_result']
            input_data = st.session_state['input_data']
            raw_json_report = st.session_state['raw_json_report']
            file_name_for_display = st.session_state['file_name_for_display']

            st.success("✅ 전략 검증 완료! (원시 데이터 기반 동적 분석)")

            # 🌟 키가 누락될 경우를 대비해 .get() 사용 (KeyError 방지) 🌟
            validity_score = analysis_result.get('validity_score', 'N/A')
            success_probability = analysis_result.get('success_probability_percent', 'N/A')
            analysis_summary = analysis_result.get('analysis_summary', '분석 요약 정보를 불러오지 못했습니다.')
            alternative_strategies = analysis_result.get('alternative_strategies', [])

            st.subheader("핵심 지표")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # 안전하게 추출한 값 사용
                st.metric(label="타당성 점수 (100점 만점)", value=f"{validity_score}{' 점' if validity_score != 'N/A' else ''}")
            with col2:
                # 안전하게 추출한 값 사용
                st.metric(label="예상 성공 확률", value=f"{success_probability}{' %' if success_probability != 'N/A' else ''}")
            with col3:
                st.markdown(f"**기준 데이터**")
                st.write(f"{input_data['business_sector']} 분야 ({file_name_for_display}) 기반 KPI")

            st.subheader("분석 요약")
            # 안전하게 추출한 값 사용
            st.info(analysis_summary)
            
            st.subheader(f"대안 전략 (타겟 컬럼 '{input_data['target_column']}' 개선 관점)")
            
            # 안전하게 추출한 리스트 사용
            if alternative_strategies:
                for i, alt in enumerate(alternative_strategies):
                    st.markdown(f"**대안 {i+1}:** {alt}")
            else:
                st.markdown("대안 전략을 불러오지 못했습니다.")
            
            st.markdown("---")

            # 다운로드 섹션 렌더링
            self._render_download_section(analysis_result, input_data, raw_json_report)
                
        elif AppConfig.OPENAI_API_KEY:
            st.info("왼쪽에서 전략을 입력하고 '전략 타당성 검증 시작' 버튼을 눌러주세요.")
        else:
            st.warning("분석을 시작하려면 OpenAI API Key를 설정해야 합니다.")

    # 📌 필수 메서드: _render_download_section 
    def _render_download_section(self, analysis_result, input_data, raw_json_report):
        """결과 다운로드 옵션을 렌더링합니다."""
        st.subheader("3. 결과 보고서 다운로드")
        
        st.radio(
            "원하는 보고서 형식을 선택하세요:", 
            ("텍스트 파일 (TXT)", "리포트 (JSON 파일)", "엑셀 파일 (CSV 형식)"),
            key='output_format'
        )
        
        output_format = st.session_state['output_format']

        # LLM 분석 결과에서 안전하게 값 추출 (다운로드 시에도 적용)
        validity_score_dl = analysis_result.get('validity_score', 'N/A')
        success_probability_dl = analysis_result.get('success_probability_percent', 'N/A')
        alternative_strategies_list = analysis_result.get('alternative_strategies', ['N/A'])
        alt_1_dl = alternative_strategies_list[0] if len(alternative_strategies_list) > 0 else 'N/A'
        alt_2_dl = alternative_strategies_list[1] if len(alternative_strategies_list) > 1 else 'N/A'
        analysis_summary_dl = analysis_result.get('analysis_summary', '분석 요약 정보를 불러오지 못했습니다.')

        # 1. JSON 파일 다운로드
        if output_format == "리포트 (JSON 파일)":
            st.download_button(
                label="JSON 파일 다운로드 (KPI + 전략)",
                data=raw_json_report,
                file_name=f"strategy_report_{input_data['business_sector']}.json",
                mime="application/json"
            )
        
        # 2. 텍스트 파일 (TXT) 다운로드: 모든 입력값 포함
        elif output_format == "텍스트 파일 (TXT)":
            text_report = f"""
[AI 비즈니스 전략 타당성 검증 리포트 - {input_data['business_sector']}]

--- 입력 정보 ---
비즈니스 분야: {input_data['business_sector']}
개선 타겟 컬럼: {input_data['target_column']} 
AI 추천 핵심 전략: {input_data['ai_strategy']}
핵심 기능 요약: {input_data['key_feature']}
전략 목표 기간: {input_data['contract_type']} 
--- 분석 결과 ---
타당성 점수: {validity_score_dl}점
예상 성공 확률: {success_probability_dl}%

[요약]
{analysis_summary_dl}

[대안 전략]
- {alt_1_dl}
- {alt_2_dl}
"""
            st.download_button(
                label="텍스트 파일 다운로드",
                data=text_report,
                file_name=f"strategy_report_{input_data['business_sector']}.txt",
                mime="text/plain"
            )
        
        # 3. 엑셀 파일 (CSV 형식) 다운로드: 모든 입력값 포함
        elif output_format == "엑셀 파일 (CSV 형식)":
            csv_data = f"""
지표,값
비즈니스 분야, "{input_data['business_sector']}"
개선 타겟 컬럼, "{input_data['target_column']}"
AI 추천 핵심 전략, "{input_data['ai_strategy']}"
핵심 기능 요약, "{input_data['key_feature']}"
전략 목표 기간, {input_data['contract_type']}
타당성 점수, {validity_score_dl}
성공 확률, {success_probability_dl}
대안 1, "{alt_1_dl}"
대안 2, "{alt_2_dl}"
"""
            st.download_button(
                label="CSV 파일 다운로드",
                data=csv_data,
                file_name=f"strategy_summary_{input_data['business_sector']}.csv",
                mime="text/csv"
            )

# ----------------------------------------------------
# 📌 2. 메인 실행 블록
# ----------------------------------------------------
if __name__ == "__main__":
    app = StreamlitAppView()
    app.run()