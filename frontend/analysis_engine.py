import json
import openai
# config.py에서 설정 정보 로드
from config import AppConfig

class AnalysisEngine:
    """
    LLM 통신, 프롬프트 구성, JSON 파싱 등 핵심 비즈니스 로직을 담당합니다.
    """
    def __init__(self):
        self.api_key = AppConfig.OPENAI_API_KEY
        self.llm_model = AppConfig.LLM_MODEL
        
        if self.api_key:
            # API Key가 있으면 클라이언트 초기화
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None

    def _get_kpi_instruction(self, business_sector):
        """분야별 KPI 도출 지침을 반환합니다."""
        if business_sector == "subscription service":
            return "제공된 원시 데이터를 기반으로 **구독/반복 활동 및 위험(Risk) 관련 핵심 지표** 6가지 (예: 전체 유지/이탈 지표, 사용 빈도, 구독 플랜별 성과, 계약 기간별 패턴, 지원 호출 리스크, 결제 지연 리스크 등)를 도출합니다."
        elif business_sector == "online commerce":
            return "제공된 원시 데이터를 기반으로 **거래 및 고객 행동 관련 핵심 지표** 6가지 (예: 객단가, 전환율, 장바구니 포기율, 재구매율, 평균 배송 시간 관련 지표 등)를 도출합니다."
        elif business_sector == "contents":
            return "제공된 원시 데이터를 기반으로 **콘텐츠 소비 및 참여 관련 핵심 지표** 6가지 (예: 카테고리별 평균 성과, 제목 길이 vs 조회수 패턴, 업로드 시간 vs 성과, 태그 수 vs 조회수 패턴, 평균 시청 시간, 월간 활동 사용자(MAU), 유료 전환율, 이탈률, 좋아요/공유 지표 등)를 도출합니다."
        elif business_sector == "fintech":
            return "제공된 원시 데이터를 기반으로 **금융 거래 및 리스크 관리 관련 핵심 지표** 6가지 (예: 거래 빈도, 평균 거래 금액, 사기 탐지율, 신용 점수 변화, 대출 상환율, 사용자 활동 지표 등)를 도출합니다."
        else:
            return "제공된 원시 데이터를 기반으로 **해당 분야에 가장 적합한 핵심 지표** 6가지를 도출합니다."

    def run_analysis(self, strategy_data, raw_data_input):
        """
        GPT 모델을 호출하여 전략 타당성을 검증하고 분석 결과를 반환합니다.
        """
        if not self.client:
            return None, None
        
        business_sector = strategy_data['business_sector']
        kpi_instruction = self._get_kpi_instruction(business_sector)
        
        # 시스템 프롬프트 구성 (🌟 JSON 구조 강제 지시 및 비판적 검토 지시 추가 🌟)
        system_prompt = (
            f"당신은 {business_sector} 비즈니스 전략 전문가입니다. 제공된 '원시 데이터(Raw Data)'를 활용하여 전략 분석을 수행하세요. "
            "분석 단계: "
            f"1) 원시 데이터 내용을 기반으로 **{business_sector} 분야에 가장 적합한 핵심 지표** 6가지를 도출하고 **'derived_kpis'** 항목에 JSON 형태로 정리합니다. 이 지표들은 다음의 지침을 따르세요: {kpi_instruction} "
            f"2) 도출된 KPI를 근거로 **'입력 전략'**의 타당성 점수, 성공 확률, 분석 요약, 대안 전략을 제시합니다. 이때 {strategy_data['target_column']} 컬럼을 **개선 타겟 지표**로 설정하고, 이 지표를 증가/감소시키는 전략이 KPI와 얼마나 부합하는지 중점적으로 분석하세요. "
            f"특히, 입력된 '전략 목표 기간'({strategy_data['contract_type']})이 단기(Monthly), 중기(Quarterly), 장기(Annual) 중 어디에 해당하는지 판단하고, 전략의 효과와 리스크(예: 고객 이탈, 단기 비용)를 해당 기간의 관점에서 분석하여 타당성과 성공 확률을 평가해야 합니다. "
            
            "**[성공 확률 검증 강화] 성공 확률을 평가할 때는, 제공된 '원시 데이터'에서 전략을 직접적으로 뒷받침하거나 혹은 반박하는 구체적인 데이터 패턴(예: 특정 시간대 업로드 시 낮은 성과, 특정 속성을 가진 고객층의 예상치 못한 행동 등)을 반드시 찾아 이를 근거로 점수를 부여해야 합니다. 단순히 일반적인 이론이 아닌, 데이터에 기반한 엄격한 비판적 검토를 수행하고, 모순되는 패턴이 있다면 점수를 낮추고 분석 요약에 그 이유를 명시해야 합니다.**"
            "**[중요] 최종 결과는 반드시 다음 [출력 형식]에 맞춘 단일 JSON 문자열로 반환해야 합니다. 분석이 어렵더라도 'validity_score'와 'success_probability_percent'는 0 이상의 정수(int)로, 'analysis_summary'는 최소 한 문장으로, 'alternative_strategies'는 최소 1개 이상의 대안을 포함하는 배열로 필수로 채워야 합니다.**"
            "**[중요] () 안에 들어가있는 예시는 참고용일 뿐, 실제 출력 시 똑같이 따라하지 말고, 해당 비즈니스 분야와 데이터에 맞게 적절히 변형하여 생각하세요.**"
        )
        
        # 사용자 프롬프트 구성
        user_prompt = f"""
        [원시 데이터 (Raw Data)]
        {raw_data_input}

        [입력 전략]
        - 비즈니스 분야: {business_sector}
        - 개선 타겟 컬럼: {strategy_data['target_column']} 
        - 핵심 기능: {strategy_data['key_feature']}
        - 전략 목표 기간: {strategy_data['contract_type']}  
        - 전략: {strategy_data['ai_strategy']}

        [출력 형식]
        결과는 반드시 다음 구조를 가진 JSON 문자열로만 반환해야 합니다:
        {{
          "derived_kpis": {{
            "KPI_1_이름": "KPI 1 설명",
            "KPI_2_이름": "KPI 2 설명",
            "KPI_3_이름": "KPI 3 설명",
            "KPI_4_이름": "KPI 4 설명",
            "KPI_5_이름": "KPI 5 설명",
            "KPI_6_이름": "KPI 6 설명" 
          }},
          "strategy_analysis": {{
            "validity_score": (int, 0부터 100 사이),
            "success_probability_percent": (int, 0부터 100 사이),
            "analysis_summary": (string),
            "alternative_strategies": [
              (string: 대안 전략 1),
              (string: 대안 전략 2)
            ]
          }}
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model, 
                response_format={"type": "json_object"}, 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            )
            
            json_string = response.choices[0].message.content
            full_analysis_result = json.loads(json_string)
            analysis_result = full_analysis_result.get("strategy_analysis")
            
            return analysis_result, json_string

        except Exception as e:
            # 오류 발생 시 외부로 None 전달
            print(f"LLM 분석 중 오류가 발생했습니다. 오류: {e}")
            return None, None