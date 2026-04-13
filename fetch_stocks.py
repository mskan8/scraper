import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from io import StringIO

def get_last_page(sosok):
    """각 시장의 마지막 페이지 번호를 가져옵니다."""
    url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')

    try:
        last_page_tag = soup.find('td', class_='pgRR')
        if last_page_tag:
            return int(last_page_tag.find('a')['href'].split('page=')[-1])
        else:
            pages = soup.find('table', class_='Nnavi').find_all('a')
            return max([int(p.text) for p in pages if p.text.isdigit()])
    except:
        return 1

def scrape_market(sosok, market_name):
    """네이버 금융에서 특정 시장의 주식 데이터를 긁어옵니다."""
    last_page = get_last_page(sosok)
    print(f"{market_name} 데이터 수집 중 (총 {last_page}페이지)...")

    market_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for page in range(1, last_page + 1):
        url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}"
        res = requests.get(url, headers=headers)

        # pandas 2.2.0 이상에서는 StringIO를 권장합니다.
        tables = pd.read_html(StringIO(res.text), encoding='euc-kr')
        df = tables[1]

        # 구분선 등 불필요한 행 제거
        df = df.dropna(subset=['종목명']).copy()

        # 종목코드 추출
        soup = BeautifulSoup(res.text, 'lxml')
        links = soup.find_all('a', class_='tltle')
        codes = [link['href'].split('code=')[-1] for link in links]

        df['종목코드'] = codes

        # 시가총액과 상장주식수 단위 조정
        # 네이버 금융: 시가총액(억), 상장주식수(천주)
        # 초보자가 보기 편하도록 단위를 명시하거나 원 단위로 변환할 수 있습니다.
        # 여기서는 원본 수치(억, 천주)를 유지하되 컬럼명을 명확히 합니다.

        market_data.append(df)
        print(f"  {page}/{last_page} 완료", end='\r')
        time.sleep(0.1)

    print(f"\n{market_name} 수집 완료!")
    return pd.concat(market_data, ignore_index=True)

def fetch_stock_data():
    print("네이버 금융에서 데이터를 수집합니다 (라이브러리 장애 우회)...")

    try:
        df_kospi = scrape_market(0, "KOSPI")
        df_kosdaq = scrape_market(1, "KOSDAQ")

        df = pd.concat([df_kospi, df_kosdaq], ignore_index=True)

        # 필요한 컬럼 선택 및 이름 변경
        result_df = df[['종목코드', '종목명', '시가총액', '상장주식수']]
        result_df.columns = ['종목코드', '종목명', '시가총액(억)', '상장주식수(천주)']

        output_file = "stock_data.csv"
        result_df.to_csv(output_file, index=False, encoding="utf-8-sig")

        print("-" * 50)
        print(f"성공적으로 데이터를 가져와 '{output_file}'에 저장했습니다.")
        print(f"총 {len(result_df)} 개의 종목 정보가 수집되었습니다.")
        print("-" * 50)

    except Exception as e:
        print(f"\n오류가 발생했습니다: {e}")
        print("인터넷 연결을 확인하거나 나중에 다시 시도해 주세요.")

if __name__ == "__main__":
    fetch_stock_data()
