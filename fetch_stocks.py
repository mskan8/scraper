import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from io import StringIO
from datetime import datetime, timedelta
import argparse
import sys
import FinanceDataReader as fdr
from pykrx import stock

def get_last_page(sosok):
    """네이버 금융 시가총액 페이지의 마지막 페이지 번호를 가져옵니다."""
    url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'lxml')
        last_page_tag = soup.find('td', class_='pgRR')
        if last_page_tag:
            return int(last_page_tag.find('a')['href'].split('page=')[-1])
        else:
            pages = soup.find('table', class_='Nnavi').find_all('a')
            if pages:
                return max([int(p.text) for p in pages if p.text.isdigit()])
            return 1
    except:
        return 1

def scrape_naver_market_cap(sosok, market_name):
    """현재 시점의 시가총액 데이터를 네이버 금융에서 스크래핑합니다."""
    last_page = get_last_page(sosok)
    print(f"{market_name} 현재 데이터 수집 중...")

    market_data = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for page in range(1, last_page + 1):
        url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}&page={page}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            # pandas 2.2.0+ requires StringIO
            tables = pd.read_html(StringIO(res.text), encoding='euc-kr')
            df = tables[1]
            df = df.dropna(subset=['종목명']).copy()

            # 네이버 금융 단위 변환: 시가총액(억) -> 원, 상장주식수(천주) -> 주
            # (데이터 수집 시점의 시세를 정확히 반영하기 위함)
            df['시가총액'] = (df['시가총액'] * 100000000).astype(int)
            df['상장주식수'] = (df['상장주식수'] * 1000).astype(int)

            soup = BeautifulSoup(res.text, 'lxml')
            links = soup.find_all('a', class_='tltle')
            codes = [link['href'].split('code=')[-1] for link in links]
            df['종목코드'] = codes

            market_data.append(df)
            print(f"  {page}/{last_page} 페이지 완료", end='\r')
            time.sleep(0.1)
        except Exception as e:
            print(f"\n페이지 {page} 수집 중 오류: {e}")
            continue

    print(f"\n{market_name} 수집 완료")
    return pd.concat(market_data, ignore_index=True) if market_data else pd.DataFrame()

def fetch_historical_data(date_str):
    """pykrx를 사용하여 특정 과거 날짜의 전종목 시가총액 데이터를 가져옵니다."""
    print(f"{date_str} 기준 데이터 수집 시도 중...")

    try:
        # pykrx의 get_market_cap_by_ticker는 특정 날짜의 시장 스냅샷을 가져오는 가장 표준적인 방법입니다.
        df = stock.get_market_cap_by_ticker(date_str, market="ALL")

        if df.empty:
            print(f"{date_str}일은 휴장일이거나 데이터가 없습니다.")
            return pd.DataFrame()

        # 종목명 매칭
        df['종목명'] = [stock.get_market_ticker_name(ticker) for ticker in df.index]
        df = df.reset_index()

        # 컬럼 표준화 (종목코드, 종목명, 시가총액, 발행주식수, 날짜)
        df = df[['티커', '종목명', '시가총액', '상장주식수']]
        df.columns = ['종목코드', '종목명', '시가총액', '발행주식수']
        df['날짜'] = date_str

        return df
    except KeyError:
        print(f"{date_str} 데이터 수집 중 오류: KRX 응답 형식이 올바르지 않습니다 (휴장일 가능성).")
        return pd.DataFrame()
    except Exception as e:
        print(f"{date_str} 데이터 수집 중 오류: {e}")
        return pd.DataFrame()

def fetch_stock_data():
    parser = argparse.ArgumentParser(description='대한민국 상장주 시가총액 데이터 수집기')
    parser.add_argument('--date', type=str, help='조회 날짜 (YYYYMMDD). 미지정시 현재 데이터 수집.')
    parser.add_argument('--start', type=str, help='시작 날짜 (YYYYMMDD)')
    parser.add_argument('--end', type=str, help='종료 날짜 (YYYYMMDD)')

    args = parser.parse_args()

    results = []

    # 1. 기간 조회 (start, end 지정 시)
    if args.start and args.end:
        start_dt = datetime.strptime(args.start, "%Y%m%d")
        end_dt = datetime.strptime(args.end, "%Y%m%d")
        current = start_dt
        while current <= end_dt:
            # 주말 제외 (토:5, 일:6)
            if current.weekday() < 5:
                d_str = current.strftime("%Y%m%d")
                df = fetch_historical_data(d_str)
                if not df.empty:
                    results.append(df)
            current += timedelta(days=1)

    # 2. 특정 날짜 조회
    elif args.date:
        df = fetch_historical_data(args.date)
        if not df.empty:
            results.append(df)

    # 3. 기본값: 현재 데이터 수집
    else:
        print("조회 날짜가 지정되지 않아 현재 데이터를 수집합니다.")
        # 현재 데이터는 FinanceDataReader가 가장 빠릅니다.
        try:
            df_kospi = fdr.StockListing('KOSPI')
            df_kosdaq = fdr.StockListing('KOSDAQ')
            df = pd.concat([df_kospi, df_kosdaq], ignore_index=True)

            if not df.empty:
                df = df[['Code', 'Name', 'Marcap', 'Stocks']]
                df.columns = ['종목코드', '종목명', '시가총액', '발행주식수']
                df['날짜'] = datetime.now().strftime("%Y%m%d")
                results.append(df)
        except Exception as e:
            print(f"라이브러리 수집 실패 ({e}), 네이버 금융 스크래핑을 시도합니다.")
            df_kospi = scrape_naver_market_cap(0, "KOSPI")
            df_kosdaq = scrape_naver_market_cap(1, "KOSDAQ")
            df = pd.concat([df_kospi, df_kosdaq], ignore_index=True)

            if not df.empty:
                df = df[['종목코드', '종목명', '시가총액', '상장주식수']]
                df.columns = ['종목코드', '종목명', '시가총액', '발행주식수']
                df['날짜'] = datetime.now().strftime("%Y%m%d")
                results.append(df)

    if not results:
        print("수집된 데이터가 없습니다. 날짜를 확인해 주세요 (주말/공휴일 제외).")
        return

    # 데이터 통합 및 저장
    final_df = pd.concat(results, ignore_index=True)
    output_file = "stock_data.csv"
    final_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("-" * 50)
    print(f"저장 완료: {output_file}")
    print(f"총 레코드 수: {len(final_df)}")
    print("-" * 50)

if __name__ == "__main__":
    fetch_stock_data()
