import os
# config.py에서 설정 정보 로드
from config import AppConfig

class DataLoader:
    """
    파일 로드, 샘플링, 컬럼 추출 등 데이터 관련 처리를 담당합니다.
    """
    def __init__(self):
        self.BASE_DATA_DIR = AppConfig.BASE_DATA_DIR
        self.BUSINESS_FILE_MAPPING = AppConfig.BUSINESS_FILE_MAPPING

    def load_raw_data(self, business_sector, max_lines=100): 
        """
        선택된 비즈니스 분야에 따라 원시 데이터를 로드하고 컬럼 목록을 추출합니다.
        (토큰 한도 초과 방지를 위해 max_lines만큼 샘플링합니다.)
        """
        relative_file_path = self.BUSINESS_FILE_MAPPING.get(business_sector) 
        
        if not relative_file_path:
            return f"Error: {business_sector}에 대한 매핑 파일이 없습니다.", None, None
            
        normalized_relative_path = relative_file_path.replace('/', os.sep)
        file_path = os.path.join(self.BASE_DATA_DIR, normalized_relative_path)
        
        try:
            raw_data_lines = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i < max_lines: 
                        raw_data_lines.append(line.strip())
                    else:
                        break
            
            raw_data = '\n'.join(raw_data_lines)
            lines = raw_data_lines
            
            if not lines or not lines[0].strip():
                columns = ["Error: 파일 내용이 비어 있거나 첫 줄(컬럼)이 비어 있습니다."]
            else:
                first_line = lines[0]
                columns = []
                
                # 구분자(쉼표 또는 탭)에 따라 컬럼 분리
                if ',' in first_line:
                    columns = [col.strip() for col in first_line.split(',') if col.strip()]
                elif '\t' in first_line:
                    columns = [col.strip() for col in first_line.split('\t') if col.strip()]
                else:
                    columns = ["Error: 유효한 구분자(쉼표 또는 탭)를 찾을 수 없습니다."]
                    
                if not columns or (len(columns) == 1 and columns[0].startswith("Error:")):
                     columns = ["Error: 유효한 컬럼 이름을 추출하지 못했습니다. (데이터 확인 필요)"]
                     
            return raw_data, columns, relative_file_path
        
        except FileNotFoundError:
            abs_file_path = os.path.abspath(file_path)
            return f"Error: 파일 '{file_path}'를 찾을 수 없습니다. (절대 경로: {abs_file_path}) example_dataset 폴더 구조 및 파일명을 확인해주세요.", None, None
        except Exception as e:
            return f"Error: 파일 로드 중 오류 발생: {e}", None, None