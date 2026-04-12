from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta

def get_latest_business_day():
    """
    최근 영업일을 구하는 함수입니다.
    오늘부터 최대 10일 전까지 거슬러 올라가며 데이터가 존재하는 가장 최근 날짜를 찾습니다.
    """
    target_date = datetime.now()
    for _ in range(10):
        date_str = target_date.strftime("%Y%m%d")
        try:
            # 해당 날짜에 티커 리스트가 존재하는지 확인
            tickers = stock.get_market_ticker_list(date_str, market="KOSPI")
            if len(tickers) > 0:
                return date_str
        except Exception:
            # 오류 발생 시(보통 휴장일) 이전 날짜로 넘어감
            pass
        target_date -= timedelta(days=1)

    # 모든 시도가 실패할 경우 어제 날짜를 반환 (최후의 수단)
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

def fetch_stock_data():
    print("데이터를 가져오는 중입니다. 잠시만 기다려 주세요...")

    try:
        # 1. 최근 영업일 확인
        date = get_latest_business_day()
        print(f"조회 기준일: {date}")

        # 2. KOSPI, KOSDAQ 종목의 시가총액 정보 가져오기
        # market="ALL"은 KOSPI, KOSDAQ, KONEX를 모두 포함하므로,
        # 필요에 따라 각각 가져와서 합치는 방식을 사용합니다.
        print("KOSPI 데이터를 가져오는 중...")
        df_kospi = stock.get_market_cap_by_ticker(date, market="KOSPI")

        print("KOSDAQ 데이터를 가져오는 중...")
        df_kosdaq = stock.get_market_cap_by_ticker(date, market="KOSDAQ")

        # 두 데이터프레임 합치기
        df = pd.concat([df_kospi, df_kosdaq])

        if df.empty:
            print(f"죄송합니다. {date} 날짜의 데이터를 가져오지 못했습니다.")
            print("휴장일이거나 KRX 서버 응답에 문제가 있을 수 있습니다.")
            return

        # 3. 종목명(Company Name) 추가
        # df의 인덱스는 종목코드(Ticker)입니다.
        print("종목명을 매칭하고 있습니다...")
        df['종목명'] = [stock.get_market_ticker_name(ticker) for ticker in df.index]

        # 4. 필요한 컬럼만 선택 및 정리
        # '상장주식수'가 발행주식수와 동일한 의미로 사용됩니다.
        result_df = df[['종목명', '시가총액', '상장주식수']]

        # 인덱스(종목코드)를 컬럼으로 포함시키고 컬럼명 변경
        result_df = result_df.reset_index()
        result_df.columns = ['종목코드', '종목명', '시가총액', '발행주식수']

        # 5. CSV 파일로 저장
        # utf-8-sig 인코딩은 엑셀에서 한글이 깨지는 것을 방지합니다.
        output_file = "stock_data.csv"
        result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

        print("-" * 50)
        print(f"축하합니다! 성공적으로 데이터를 가져왔습니다.")
        print(f"저장된 파일: {output_file}")
        print(f"총 종목 수: {len(result_df)} 개 (KOSPI + KOSDAQ)")
        print("-" * 50)

    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        print("네트워크 연결을 확인하거나 나중에 다시 시도해 주세요.")

if __name__ == "__main__":
    fetch_stock_data()
