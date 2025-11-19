import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class AppConfig:
    """
    앱 실행에 필요한 모든 전역 설정과 상수를 관리하는 클래스입니다.
    """
    
    # 1. API Key
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # 2. 파일 경로 및 매핑 딕셔너리
    BUSINESS_FILE_MAPPING = {
        "subscription service": "Subscription_service/Subscription_service_customer_behavior.csv",
        "online commerce": "e-commerce/E_commerce_customer_behavior.csv",
        "contents": "Contents/KR_youtube_trending_data.csv",
        "fintech": "Fintech/Fintech_data.csv"
    }
    
    # 데이터셋 폴더의 기본 경로
    BASE_DATA_DIR = "example_dataset"

    # 3. LLM 모델 설정
    LLM_MODEL = "gpt-4-turbo-preview"