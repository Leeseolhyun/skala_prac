import json
import sys
from collections import Counter, defaultdict

# 데이터 읽어오기
try:
    with open('Python_Practice1_Data.json', 'r', encoding='utf-8') as f:
        sales = json.load(f)
except FileNotFoundError:
    print("데이터 파일을 찾을 수 없습니다.")
    sales = []

# ----------------------------------------------------
# 1) 리스트/딕셔너리 컴프리헨션
# ----------------------------------------------------
try:
    # 리스트 컴프리헨션으로 1000 이상 거래 필터링
    filtered_sales = [item for item in sales if item.get('amount', 0) >= 1000]
    
    # 집합 컴프리헨션으로 중복 지역 제거
    unique_regions = {item['region'] for item in filtered_sales}
    
    # 딕셔너리 컴프리헨션으로 지역별 매출 총액 계산
    region_total = {
        region: sum(item['amount'] for item in filtered_sales if item['region'] == region)
        for region in unique_regions
    }
except Exception as e:
    print("1번 오류 발생:", e)

# ----------------------------------------------------
# 2) Counter + defaultdict
# ----------------------------------------------------
try:
    # Counter로 지역별 거래 건수 세기 (루프 대신 사용)
    region_counts = Counter(item['region'] for item in sales)
    
    # defaultdict로 카테고리별 amount 묶기 (if문 생략)
    category_amounts = defaultdict(list)
    for item in sales:
        category_amounts[item['category']].append(item['amount'])
except Exception as e:
    print("2번 오류 발생:", e)

# ----------------------------------------------------
# 3) 제너레이터 — 메모리 비교
# ----------------------------------------------------
try:
    # 1000 초과인 행 필터링 (리스트 방식 vs 제너레이터 방식)
    list_data = [item for item in sales if item.get('amount', 0) > 1000]
    gen_data = (item for item in sales if item.get('amount', 0) > 1000) # 괄호만 다름!
    
    # sys 모듈로 메모리 크기 비교
    list_size = sys.getsizeof(list_data)
    gen_size = sys.getsizeof(gen_data)
except Exception as e:
    print("3번 오류 발생:", e)

# ----------------------------------------------------
# 4) 종합 - 월별 카테고리 매출 집계
# ----------------------------------------------------
try:
    # 월과 카테고리를 합쳐서 키 생성 (예: '2024-01_전자')
    month_cat_sales = defaultdict(list)
    for item in sales:
        key = f"{item['month']}_{item['category']}"
        month_cat_sales[key].append(item['amount'])
        
    # 컴프리헨션으로 그룹핑된 총매출 계산
    month_cat_total = {k: sum(v) for k, v in month_cat_sales.items()}
    
    # top3 금액 내림차순 정렬 (체크포인트)
    top3_sales = sorted(month_cat_total.items(), key=lambda x: x[1], reverse=True)[:3]
except Exception as e:
    print("4번 오류 발생:", e)


# ====================================================
# 최종 결과 출력
# ====================================================
if sales:
    print("--- 1) 지역별 총 매출 ---")
    print(region_total)
    
    print("\n--- 2) 지역별 거래 건수 (많은 순) ---")
    print(region_counts.most_common())
    
    print("\n--- 3) 메모리 비교 결과 ---")
    print(f"리스트 메모리: {list_size} bytes")
    print(f"제너레이터 메모리: {gen_size} bytes")
    print(f"-> 제너레이터가 더 가벼운가? {gen_size < list_size}")
    
    print("\n--- 4) 월별_카테고리 매출 ---")
    print(top3_sales)