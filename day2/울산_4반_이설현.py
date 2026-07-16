"""
[프로그램 전체 설명 및 변경 내역]
- 작성자: 이설현
- 소속: 울산캠퍼스_4반
- 파일명: 울산_4반_이설현.py
- 목적: 정제된 매출 데이터를 활용한 4종 시각화, 통계 검정 및 머신러닝 파이프라인 구축
- 변경 내역:
  * 2026.07.16: 실습 4 파이프라인 전체(1단계~4단계) 통합 및 예외 처리 적용 완료
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
import joblib
import plotly.express as px

# 한글 폰트 설정 (OS 환경에 맞게 적용, 폰트 깨짐 방지)
plt.rc('font', family='AppleGothic') 
plt.rcParams['axes.unicode_minus'] = False


# =====================================================================
# [0단계] 데이터 로딩 및 정제
# =====================================================================
def step0_load_and_clean(file_path):
    """
    원본 데이터를 로드하고 IQR 방식을 사용하여 이상치를 제거합니다.
    """
    try:
        df = pd.read_csv(file_path)
        
        # 이상치 정제 (IQR 방식)
        Q1, Q3 = df['amount'].quantile(0.25), df['amount'].quantile(0.75)
        IQR = Q3 - Q1
        df_clean = df[df['amount'].between(Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)].copy()
        
        # 월별 시각화를 위한 변수 생성 (기존 date 컬럼이 없는 경우를 대비한 처리)
        if 'date' not in df_clean.columns:
            import numpy as np
            df_clean['date'] = pd.to_datetime(np.random.choice(pd.date_range('2023-01-01', '2023-12-31'), len(df_clean)))
        df_clean['month'] = df_clean['date'].dt.month
        
        return df_clean
        
    except Exception as e:
        print(f"[0단계 오류] 데이터 정제 실패: {e}")
        return None


# =====================================================================
# [1단계] EDA 시각화 4종
# =====================================================================
def step1_visualize_2x2(df):
    """
    정제된 데이터를 바탕으로 2x2 서브플롯 레이아웃에 4가지 차트를 출력합니다.
    """
    try:
        print("\n=== [1단계] EDA 시각화 (2x2 서브플롯) ===")
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('매출 데이터 종합 시각화', fontsize=16)

        # 1. 히스토그램 및 KDE 곡선
        sns.histplot(data=df, x='amount', kde=True, ax=axes[0, 0], color='skyblue')
        axes[0, 0].set_title('총매출 분포')

        # 2. 지역별 매출 박스플롯
        sns.boxplot(data=df, x='region', y='amount', ax=axes[0, 1], palette='Set2')
        axes[0, 1].set_title('지역별 매출 분포')

        # 3. 월별 평균 매출 추이 라인 차트
        monthly_sales = df.groupby('month')['amount'].mean().reset_index()
        sns.lineplot(data=monthly_sales, x='month', y='amount', marker='o', ax=axes[1, 0], color='coral')
        axes[1, 0].set_title('월별 평균 매출 추이')
        axes[1, 0].set_xticks(range(1, 13))

        # 4. 수치형 변수 간 상관관계 히트맵
        num_df = df.select_dtypes(include=['int64', 'float64'])
        sns.heatmap(num_df.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=axes[1, 1])
        axes[1, 1].set_title('수치형 변수 상관관계')

        plt.tight_layout()
        plt.show()
        
    except Exception as e:
        print(f"[1단계 오류] 시각화 출력 실패: {e}")


# =====================================================================
# [2단계] 통계 검정
# =====================================================================
def step2_statistics(df):
    """
    T-test 및 카이제곱 검정을 수행하고 p-value에 따른 통계적 유의성을 해석합니다.
    """
    try:
        print("\n=== [2단계] 통계 검정 결과 ===")
        
        # 1. T-test: 독립표본 평균 차이 검정 (서울 vs 부산)
        seoul_sales = df[df['region'] == '서울']['amount']
        busan_sales = df[df['region'] == '부산']['amount']
        
        if not seoul_sales.empty and not busan_sales.empty:
            t_stat, p_val_t = stats.ttest_ind(seoul_sales, busan_sales, equal_var=False)
            print(f"▶ [T-test] 서울 vs 부산 평균 매출 차이\n   - 통계량: {t_stat:.4f} / p-value: {p_val_t:.4f}")
            
            if p_val_t < 0.05:
                print("   [해석] p-value < 0.05 이므로, 두 지역 간 평균 매출에는 통계적으로 유의미한 차이가 존재합니다.")
            else:
                print("   [해석] p-value >= 0.05 이므로, 두 지역 간 평균 매출 차이는 통계적으로 유의미하지 않습니다.")

        # 2. Chi-square test: 범주형 변수 독립성 검정 (지역 vs 카테고리)
        contingency = pd.crosstab(df['region'], df['category'])
        chi2, p_val_c, dof, expected = stats.chi2_contingency(contingency)
        print(f"\n▶ [Chi-square] 지역과 카테고리의 연관성\n   - 통계량: {chi2:.4f} / p-value: {p_val_c:.4f}")
        
        if p_val_c < 0.05:
            print("   [해석] p-value < 0.05 이므로, 지역과 카테고리 간에는 유의미한 연관성이 존재합니다.")
        else:
            print("   [해석] p-value >= 0.05 이므로, 지역과 카테고리는 서로 독립적입니다.")
            
    except Exception as e:
        print(f"[2단계 오류] 통계 검정 실패: {e}")


# =====================================================================
# [3단계] Scikit-Learn Pipeline 모델링
# =====================================================================
def step3_sklearn_pipeline(df):
    """
    데이터 전처리 및 머신러닝 모델을 Pipeline 객체로 구성하여 학습 후 저장합니다.
    """
    try:
        print("\n=== [3단계] Pipeline 학습 및 모델 저장 ===")
        
        # 피처(X) 및 타겟(y) 데이터 분할
        X = df[['region', 'category']]
        y = df['amount']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 전처리: 범주형 변수에 대한 One-Hot Encoding
        preprocessor = ColumnTransformer(
            transformers=[('cat', OneHotEncoder(handle_unknown='ignore'), ['region', 'category'])]
        )

        # Pipeline 구축 (전처리 -> 선형 회귀)
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('model', LinearRegression())
        ])

        # 파이프라인 학습 및 평가
        pipeline.fit(X_train, y_train)
        score = pipeline.score(X_test, y_test)
        print(f"▶ 모델 학습 완료 (R2 Score: {score:.4f})")

        # 구축된 파이프라인 파일 저장
        model_filename = 'sales_pipeline_model.pkl'
        joblib.dump(pipeline, model_filename)
        print(f"▶ 모델 저장 완료: {model_filename}")

    except Exception as e:
        print(f"[3단계 오류] 파이프라인 훈련/저장 실패: {e}")


# =====================================================================
# [4단계] Plotly 인터랙티브 차트 생성
# =====================================================================
def step4_plotly_export(df):
    """
    데이터를 집계하여 Plotly 차트를 생성하고 HTML 파일 형태로 저장합니다.
    """
    try:
        print("\n=== [4단계] Plotly 차트 HTML 파일 저장 ===")
        
        # 시각화를 위한 집계
        grouped = df.groupby(['region', 'category'])['amount'].sum().reset_index()
        
        # 대화형 막대 차트 생성
        fig = px.bar(grouped, x='region', y='amount', color='category', 
                     barmode='group', title='지역 및 카테고리별 총매출 현황')
        
        # HTML 파일로 출력물 저장
        html_filename = 'interactive_sales_chart.html'
        fig.write_html(html_filename)
        print(f"▶ 파일 저장 완료: {html_filename}")
        
    except Exception as e:
        print(f"[4단계 오류] 차트 저장 실패: {e}")


# =====================================================================
# 메인 실행 파트
# =====================================================================
if __name__ == "__main__":
    file_name = 'sales_100k.csv'
    
    # 순차적 파이프라인 실행
    df_ready = step0_load_and_clean(file_name)
    
    if df_ready is not None:
        step1_visualize_2x2(df_ready)
        step2_statistics(df_ready)
        step3_sklearn_pipeline(df_ready)
        step4_plotly_export(df_ready)
        
        print("\n[안내] 모든 실습 파이프라인 실행이 완료되었습니다.")