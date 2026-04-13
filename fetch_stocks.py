import FinanceDataReader as fdr
import pandas as pd

def fetch_stock_data():
    """
    FinanceDataReader를 사용하여 KOSPI와 KOSDAQ 종목의 시가총액 및 발행주식수를 수집합니다.
    """
    print("데이터를 수집하는 중입니다. 잠시만 기다려 주세요...")

    try:
        # 1. KOSPI 및 KOSDAQ 종목 리스트 가져오기
        # StockListing은 현재 시점의 시장 정보를 데이터프레임으로 반환합니다.
        print("KOSPI 종목 정보를 가져오는 중...")
        df_kospi = fdr.StockListing('KOSPI')

        print("KOSDAQ 종목 정보를 가져오는 중...")
        df_kosdaq = fdr.StockListing('KOSDAQ')

        # 2. 데이터 통합
        df = pd.concat([df_kospi, df_kosdaq], ignore_index=True)

        if df.empty:
            print("데이터를 가져오는 데 실패했습니다.")
            return

        # 3. 필요한 컬럼 선택 및 정리
        # FinanceDataReader의 컬럼명:
        # 'Code' (종목코드), 'Name' (종목명), 'Marcap' (시가총액), 'Stocks' (발행주식수)
        # 등락률, 거래량 등 다른 정보도 포함되어 있습니다.

        result_df = df[['Code', 'Name', 'Marcap', 'Stocks']]

        # 컬럼명 한글로 변경
        result_df.columns = ['종목코드', '종목명', '시가총액', '발행주식수']

        # 4. CSV 파일로 저장 (UTF-8-sig로 저장하여 엑셀에서 한글 깨짐 방지)
        output_file = "stock_data.csv"
        result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

        print("-" * 50)
        print(f"성공적으로 데이터를 가져와 '{output_file}'에 저장했습니다.")
        print(f"총 {len(result_df)} 개의 종목 정보가 수집되었습니다.")
        print("-" * 50)

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        print("인터넷 연결을 확인하거나 라이브러리 설치 상태를 점검해 주세요.")

if __name__ == "__main__":
    fetch_stock_data()
