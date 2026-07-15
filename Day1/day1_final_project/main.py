import asyncio
import httpx
import time
import pandas as pd

# 1. API 주소 
URLS = {
    "weather": "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&hourly=temperature_2m",
    "country": "https://countries.dev/alpha/KOR",
    "ip_info": "http://ip-api.com/json/8.8.8.8"
}

# 2. 비동기 수집 함수 (걸린 시간 측정 추가)
async def fetch(client, name, url):
    start_time = time.perf_counter()
    try:
        response = await client.get(url, timeout=10.0)
        elapsed_time = time.perf_counter() - start_time
        
        if response.status_code == 200:
            return {"api_name": name, "status": "Success", "response_time(sec)": round(elapsed_time, 3)}
        else:
            return {"api_name": name, "status": f"Fail({response.status_code})", "response_time(sec)": round(elapsed_time, 3)}
            
    except Exception as e:
        return {"api_name": name, "status": "Error", "response_time(sec)": 0}

# 3. 메인 실행 및 파일 저장 파이프라인
async def main():
    async with httpx.AsyncClient() as client:
        # 비동기 데이터 수집 시작
        tasks = [fetch(client, name, url) for name, url in URLS.items()]
        results = await asyncio.gather(*tasks)
        
        # [핵심] 수집된 결과를 Pandas DataFrame(표)으로 변환
        df = pd.DataFrame(results)
        
        print("\n=== [데이터 수집 요약표] ===")
        print(df)
        print("============================\n")

        # [핵심] CSV와 Parquet 파일로 저장
        # index=False는 앞에 번호표를 빼고 깔끔하게 저장하라는 뜻임
        df.to_csv("api_results.csv", index=False)
        print("✅ CSV 파일 저장 완료 (api_results.csv)")
        
        df.to_parquet("api_results.parquet", index=False)
        print("✅ Parquet 파일 저장 완료 (api_results.parquet)")

if __name__ == "__main__":
    total_start = time.perf_counter()
    asyncio.run(main())
    total_end = time.perf_counter()
    print(f"\n프로그램 총 소요 시간: {total_end - total_start:.2f}초")