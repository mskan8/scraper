from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
import sys

def get_latest_business_day():
    """
    최근 영업일을 구하는 함수입니다.
    삼성전자(005930)의 OHLCV 데이터를 조회하여 실제 장이 열렸던 가장 최근 날짜를 찾습니다.
    """
    try:
        # 오늘부터 최근 10일간의 데이터를 조회
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d")

        # get_market_ohlcv는 비교적 안정적으로 동작합니다.
        df = stock.get_market_ohlcv(start_date, end_date, "005930")

        if not df.empty:
            # 가장 최근 날짜를 YYYYMMDD 형식으로 반환
            return df.index[-1].strftime("%Y%m%d")
    except Exception as e:
        print(f"영업일 확인 중 오류 발생: {e}")

    # 실패 시 어제 날짜 반환 (최후의 수단)
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

def fetch_stock_data():
    print("대한민국 상장주(KOSPI, KOSDAQ) 데이터를 가져오는 중입니다...")

    # 1. 최근 영업일 확인
    date = get_latest_business_day()
    print(f"조회 기준일: {date}")

    try:
        # 2. KOSPI, KOSDAQ 종목 정보 가져오기
        # pykrx 내부에서 KeyError가 발생할 수 있으므로 각각 시도하고 예외 처리를 합니다.

        results = []
        for market in ["KOSPI", "KOSDAQ"]:
            print(f"{market} 데이터를 가져오는 중...", end=" ", flush=True)
            try:
                # 시가총액 및 상장주식수 정보
                df = stock.get_market_cap_by_ticker(date, market=market)

                if df.empty:
                    print("데이터 없음")
                    continue

                # 종목명 추가
                df['종목명'] = [stock.get_market_ticker_name(ticker) for ticker in df.index]
                df = df.reset_index()

                # 필요한 컬럼만 추출 (종목코드, 종목명, 시가총액, 상장주식수)
                # pykrx의 get_market_cap_by_ticker 결과 컬럼: '종가', '시가총액', '거래량', '거래대금', '상장주식수'
                df = df[['티커', '종목명', '시가총액', '상장주식수']]
                df.columns = ['종목코드', '종목명', '시가총액', '발행주식수']
                results.append(df)
                print(f"완료 ({len(df)} 종목)")

            except KeyError as e:
                print(f"\n오류 발생: {e}")
                print(f"해당 날짜({date})에 {market} 데이터를 가져오는 데 실패했습니다.")
                print("이는 pykrx 라이브러리가 KRX 웹사이트에서 데이터를 읽어오는 과정에서 발생하는 문제입니다.")
                print("날짜를 변경하거나 잠시 후 다시 시도해 주세요.")
            except Exception as e:
                print(f"\n기타 오류 발생: {e}")

        if not results:
            print("\n데이터를 하나도 가져오지 못했습니다. 프로그램을 종료합니다.")
            return

        # 3. 데이터 통합 및 저장
        final_df = pd.concat(results, ignore_index=True)
        output_file = "stock_data.csv"

        # utf-8-sig 인코딩으로 저장하여 엑셀 한글 깨짐 방지
        final_df.to_csv(output_file, index=False, encoding="utf-8-sig")

        print("-" * 50)
        print(f"파일 저장 완료: {output_file}")
        print(f"총 수집 종목: {len(final_df)} 개")
        print("-" * 50)

    except Exception as e:
        print(f"\n처리 중 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    fetch_stock_data()
