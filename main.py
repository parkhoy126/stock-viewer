"""주가 조회기: 종목 코드를 넣으면 최근 종가를 보여준다.

사용 예:
    python main.py AAPL          # 애플 (미국)
    python main.py 005930.KS     # 삼성전자 (코스피)
    python main.py 035720.KQ 10  # 카카오 (코스닥), 최근 10일
"""
import sys

import yfinance as yf


def get_recent_prices(ticker: str, days: int = 5):
    """최근 days 거래일의 종가를 반환한다."""
    # 주말/휴일이 끼므로 넉넉히 가져온 뒤 자른다
    history = yf.Ticker(ticker).history(period="1mo")
    if history.empty:
        raise ValueError(f"'{ticker}' 데이터를 찾을 수 없습니다. 종목 코드를 확인하세요.")
    return history["Close"].tail(days)


def main():
    if len(sys.argv) < 2:
        print("사용법: python main.py <종목코드> [일수]")
        return

    ticker = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    try:
        prices = get_recent_prices(ticker, days)
    except ValueError as e:
        print(e)
        return

    print(f"[{ticker}] 최근 {len(prices)}거래일 종가")
    for date, price in prices.items():
        print(f"  {date:%Y-%m-%d}  {price:,.2f}")

    change = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    print(f"기간 등락률: {change:+.2f}%")


if __name__ == "__main__":
    main()
