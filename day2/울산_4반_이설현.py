"""
- 작성자 : 이설현
- 소속 : 울산캠퍼스_4반
- 파일명 : 울산_4반_이설현.py
- 목적 : Pandas, Polars, DuckDB를 활용한 데이터 집계 및 성능 비교 실습
- 변경 내역: 
  * 2026.07.16: 1단계(EDA 및 이상치 처리, 2단계(pandas 집계), 3단계(polars Lazy API 집계), 4단계(DuckDB SQL 동일 집계 SQL로 작성 후 , timeit으로 세 도구의 실행시간 비교)
"""

import pandas as pd
import polars as pl
import duckdb
import timeit

def step1_pandas_eda(file_path):
    # csv 파일을 읽어와 기본 EDA를 수행하고 IQR 방식으로 이상치를 제거하는 함수
    
    try:
        # 1. 데이터 로딩
        print("=== [1단계] Pandas EDA 및 이상치 처리 시작 ===")
        df = pd.read_csv(file_path)
        
        # 2. 기초 탐색 (EDA)
        print("\n[기초 탐색] 데이터 정보 (df.info):")
        df.info()
        
        print("\n[기초 탐색] 결측치 확인 (isnull().sum):")
        print(df.isnull().sum())
        
        # 제거 전 행 수 저장 및 출력
        before_rows = len(df)
        print(f"\n▶ 이상치 제거 전 데이터 행 수: {before_rows:,}행")
        
        # 3. 이상치 처리 (IQR 방식)
        # 'amount' 컬럼을 기준으로 집계하므로, 이상치 타겟을 'amount'로 가정 
        target_col = 'amount' 
        
        Q1 = df[target_col].quantile(0.25)
        Q3 = df[target_col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # between() 메서드를 사용하여 정상 범위 필터링
        df_clean = df[df[target_col].between(lower_bound, upper_bound)]
        
        # 4. 결과 출력
        after_rows = len(df_clean)
        print(f" 이상치 제거 후 데이터 행 수: {after_rows:,}행")
        print(f" 제거된 이상치 개수: {before_rows - after_rows:,}개")
        
        return df_clean, lower_bound, upper_bound

    except FileNotFoundError:
        print(f"[오류] '{file_path}' 파일을 찾을 수 없습니다. 경로를 확인 요.")
        return None, None, None # 에러 시에도 3개 변환
    except KeyError:
        print(f"[오류] 데이터 내에 기준 컬럼('{target_col}')이 존재하지 않음.")
        return None, None, None
    except Exception as e:
        print(f"[알 수 없는 오류 발생]: {e}")
        return None, None, None
def step2_pandas_groupby(df):
    """
    [함수/기능 설명]
    1단계에서 정제된 데이터를 받아 region과 category별 총매출, 평균, 건수를
    named aggregation 방식으로 집계하고 총매출 기준 내림차순으로 정렬.
    """
    try:
        print("\n=== Pandas Groupby Named Aggregation 시작 ===")
        
        # named aggregation 사용 
        agg_df = df.groupby(['region', 'category']).agg(
            total=('amount', 'sum'),
            mean=('amount', 'mean'),
            count=('amount', 'count')
        ).reset_index()
        
        # 총매출(total) 기준 내림차순 정렬
        sorted_df = agg_df.sort_values(by='total', ascending=False)
        
        print("[결과 출력] 2단계 집계 완료 데이터 (상위 5개):")
        print(sorted_df.head()) # 결과가 잘 나왔는지 앞부분만 출력해서 확인
        
        return sorted_df

    except KeyError as e:
        print(f"[오류] 집계에 필요한 컬럼이 데이터에 없습니다: {e}")
    except Exception as e:
        print(f"[알 수 없는 오류 발생]: {e}")

def step3_polars_lazy(file_path, lower_bound, upper_bound):
    """
    [함수/기능 설명]
    2번 실습과 동일한 집계를 Polars Lazy API로 작성.
    scan_csv -> filter -> group_by -> agg -> sort -> collect 순서 준수.
    """
    try:
        print("\n=== [3단계] Polars Lazy API 집계 시작 ===")
        
        # 1. Lazy 체인 작성 및 collect 실행
        lazy_query = (
            pl.scan_csv(file_path)
            .filter(pl.col('amount').is_between(lower_bound, upper_bound))
            .group_by(['region', 'category'])
            .agg([
                pl.col('amount').sum().alias('total'),
                pl.col('amount').mean().alias('mean'),
                pl.col('amount').count().alias('count')
            ])
            .sort('total', descending=True)
        )
        
        polars_df = lazy_query.collect()
        
        # 2. 결과 출력
        print("[결과 출력] 3단계 집계 완료 데이터 (상위 5개):")
        print(polars_df.head(5))
        
        return polars_df

    except Exception as e:
        print(f"[알 수 없는 오류 발생]: {e}")


def step4_duckdb_compare(file_path, lower_bound, upper_bound):
    """
    [함수/기능 설명]
    DuckDB로 동일 집계를 SQL로 작성하고, 
    timeit으로 세 도구(Pandas, Polars, DuckDB)의 실행 시간을 공정하게 비교.
    """
    try:
        print("\n=== [4단계] DuckDB SQL 및 성능 비교 시작 ===")
        
        # 1. DuckDB SQL 작성 및 실행
        query = f"""
            SELECT region, category,
                   SUM(amount) AS total,
                   AVG(amount) AS mean,
                   COUNT(amount) AS count
            FROM '{file_path}'
            WHERE amount BETWEEN {lower_bound} AND {upper_bound}
            GROUP BY region, category
            ORDER BY total DESC
        """
        duck_df = duckdb.query(query).to_df()
        
        print("[결과 출력] 4단계 DuckDB 집계 완료 데이터 (상위 5개):")
        print(duck_df.head())
        
        # 2. timeit으로 세 도구 실행 시간 비교 (반복 횟수 통일)
        print("\n[성능 비교] 각 도구별로 10회씩 측정 중...")
        
        # 측정용 글로벌 변수 세팅
        env = {'pd': pd, 'pl': pl, 'duckdb': duckdb, 'file_path': file_path, 
               'lower_bound': lower_bound, 'upper_bound': upper_bound, 'query': query}
        
        pandas_code = """
df = pd.read_csv(file_path)
df_clean = df[df['amount'].between(lower_bound, upper_bound)]
df_clean.groupby(['region', 'category']).agg(
    total=('amount', 'sum'), mean=('amount', 'mean'), count=('amount', 'count')
).reset_index().sort_values(by='total', ascending=False)
"""
        polars_code = """
pl.scan_csv(file_path).filter(pl.col('amount').is_between(lower_bound, upper_bound)) \\
  .group_by(['region', 'category']).agg([
      pl.col('amount').sum().alias('total'), pl.col('amount').mean().alias('mean'), pl.col('amount').count().alias('count')
  ]).sort('total', descending=True).collect()
"""
        duckdb_code = "duckdb.query(query).to_df()"
        
        # 반복 횟수(number)를 10으로 모두 통일
        runs = 10
        pd_time = timeit.timeit(pandas_code, globals=env, number=runs)
        pl_time = timeit.timeit(polars_code, globals=env, number=runs)
        db_time = timeit.timeit(duckdb_code, globals=env, number=runs)
        
        print(f"▶ Pandas 실행 시간  : {pd_time:.4f} 초")
        print(f"▶ Polars 실행 시간  : {pl_time:.4f} 초")
        print(f"▶ DuckDB 실행 시간  : {db_time:.4f} 초")

    except Exception as e:
        print(f"[알 수 없는 오류 발생]: {e}")

if __name__ == "__main__":
    # 파일 경로 변수 지정
    target_file = 'sales_100k.csv'

    # EDA 및 이상치 처리 (경계값 받아오기)
    df_cleaned, lower_b, upper_b = step1_pandas_eda(target_file)

    if df_cleaned is not None:
        step2_pandas_groupby(df_cleaned)
        step3_polars_lazy(target_file, lower_b, upper_b)
        step4_duckdb_compare(target_file, lower_b, upper_b)
    
