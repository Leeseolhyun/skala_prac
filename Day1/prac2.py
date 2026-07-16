import json
import logging
import csv
from pydantic import BaseModel, Field, ValidationError
from typing import Optional

# [프로그램 설명]
# 실습 2: 파일 I/O, 예외 처리 및 Pydantic을 활용한 데이터 검증 파이프라인 구축

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================
# 1) 예외 처리 + 파일 읽기
# ====================================================
def safe_load_csv(file_path):
    try:
        # utf-8-sig: 파일 앞부분의 숨은 기호(BOM) 제거
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            logger.info(f"{file_path} 로딩 성공")
            return data
    except FileNotFoundError:
        logger.error(f"{file_path} 파일 없음")
        return None
    finally:
        print(f"--- {file_path} 읽기 종료 ---")

# Checkpoint: 없는 파일 예외 처리 확인 (None 반환)
assert safe_load_csv('없는파일.json') is None

# 원본 데이터 로드
raw_data = safe_load_csv('Python_Practice2_Data.json')


# ====================================================
# 2) Pydantic v2 스키마 정의
# ====================================================
class SalesRecord(BaseModel):
    month: str = Field(..., min_length=1)  # 빈 문자열 불가
    region: str = Field(..., min_length=1) # 빈 문자열 불가
    amount: int = Field(..., gt=0)         # 0 초과
    category: Optional[str] = None         # 생략 가능 (기본값 None)


# ====================================================
# 3) 검증 파이프라인 (valid / errors 분리)
# ====================================================
valid = []   
errors = []  

if raw_data:
    for row in raw_data:
        try:
            # 데이터 검증 및 딕셔너리 변환
            record = SalesRecord(**row)
            valid.append(record.model_dump())
        except ValidationError as e:
            # 오류 발생 시 사유 기록
            errors.append({'row': row, 'error': str(e)})

    print(f"검증 완료 (정상: {len(valid)}건, 오류: {len(errors)}건)")


# ====================================================
# 4) 결과 파일 저장 + 재로딩 확인
# ====================================================
# 정상 데이터 -> CSV 저장
if valid:
    with open('valid_sales.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=valid[0].keys())
        writer.writeheader()
        writer.writerows(valid)

# 오류 데이터 -> JSON 저장 (한글 깨짐 방지)
if errors:
    with open('errors.json', 'w', encoding='utf-8') as f:
        json.dump(errors, f, ensure_ascii=False, indent=4)

# 저장된 CSV 파일 재로딩 및 건수 확인
try:
    with open('valid_sales.csv', 'r', encoding='utf-8') as f:
        reloaded = list(csv.DictReader(f))
        
    print(f"CSV 재로딩 완료 (총 {len(reloaded)}건)")
    
    # Checkpoint: 재로딩 건수 검증
    assert len(reloaded) == 100, "데이터 건수 불일치"
    
except FileNotFoundError:
    print("CSV 파일이 없습니다.")