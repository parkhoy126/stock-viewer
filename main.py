"""주가 조회기: 종목 코드를 넣으면 최근 종가와 이동평균선 차트를 보여준다.

사용 예:
    python main.py AAPL                    # 애플 (미국) 최근 5거래일 종가
    python main.py 005930.KS 10            # 삼성전자 (코스피) 최근 10거래일
    python main.py 005930.KS --chart       # 종가 + 이동평균선 차트 저장
    python main.py AAPL --chart --months 12
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 창을 띄우지 않고 파일로만 저장
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from matplotlib.ticker import FuncFormatter

MA_WINDOWS = (20, 60)  # 이동평균선 기간(거래일)
CHART_DIR = Path("charts")

# 차트 색상: 종가는 파랑, 20일선은 주황, 60일선은 청록
COLORS = {"close": "#2a78d6", 20: "#eb6834", 60: "#1baf7a"}
INK = "#0b0b0b"
INK_MUTED = "#52514e"
GRID = "#e4e3df"


def get_history(ticker: str, period: str = "1mo"):
    """종목의 일봉 데이터와 거래 통화(예: USD, KRW)를 가져온다."""
    stock = yf.Ticker(ticker)
    history = stock.history(period=period)
    if history.empty:
        raise ValueError(f"'{ticker}' 데이터를 찾을 수 없습니다. 종목 코드를 확인하세요.")
    currency = stock.history_metadata.get("currency", "")
    return history, currency


# 소수점 없이 표시하는 통화 (원, 엔)
ZERO_DECIMAL = {"KRW", "JPY"}
SYMBOLS = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", "HKD": "HK$"}


def format_price(value: float, currency: str) -> str:
    """통화에 맞는 형식으로 가격을 문자열로 만든다. 예: $336.64, 262,000원"""
    if currency == "KRW":
        return f"{value:,.0f}원"
    digits = 0 if currency in ZERO_DECIMAL else 2
    number = f"{value:,.{digits}f}"
    if currency in SYMBOLS:
        return f"{SYMBOLS[currency]}{number}"
    return f"{number} {currency}".strip()


def add_moving_averages(close, windows=MA_WINDOWS):
    """종가에 이동평균을 계산해 DataFrame으로 돌려준다. (앞쪽 기간은 NaN)"""
    df = close.to_frame("close")
    for w in windows:
        df[f"ma{w}"] = close.rolling(window=w).mean()
    return df


def plot_chart(ticker: str, df, path: Path, currency: str = ""):
    """종가와 이동평균선을 그려 PNG로 저장한다."""
    plt.rcParams["font.family"] = ["AppleGothic", "sans-serif"]  # 한글 (macOS)
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.plot(df.index, df["close"], color=COLORS["close"], linewidth=1.5, label="종가")
    for w in MA_WINDOWS:
        series = df[f"ma{w}"].dropna()
        if not series.empty:
            ax.plot(series.index, series, color=COLORS[w], linewidth=1.5, label=f"{w}일 이동평균")

    unit = f" ({currency})" if currency else ""
    ax.set_title(f"{ticker} 종가와 이동평균선{unit}", loc="left", color=INK, fontsize=13)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_MUTED, length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(frameon=False, labelcolor=INK_MUTED, loc="upper center", bbox_to_anchor=(0.5, -0.07), ncol=3)

    fig.tight_layout()
    path.parent.mkdir(exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def print_prices(ticker: str, close, days: int, currency: str = ""):
    prices = close.tail(days)
    print(f"[{ticker}] 최근 {len(prices)}거래일 종가 ({currency or '통화 정보 없음'})")
    for date, price in prices.items():
        print(f"  {date:%Y-%m-%d}  {format_price(price, currency)}")
    change = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    print(f"기간 등락률: {change:+.2f}%")


def ask(prompt: str, default: str = "") -> str:
    """질문을 출력하고 입력을 받는다. 그냥 Enter를 치면 기본값을 쓴다."""
    suffix = f" (기본 {default})" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def ask_int(prompt: str, default: int) -> int:
    """정수를 입력받는다. 숫자가 아니거나 1보다 작으면 다시 묻는다."""
    while True:
        answer = ask(prompt, str(default))
        if answer.isdigit() and int(answer) >= 1:
            return int(answer)
        print("1 이상의 숫자를 입력하세요.")


def ask_inputs():
    """터미널에서 하나씩 물어보고 조회 설정을 돌려준다."""
    print("주가 조회기 (종료: Ctrl+C)")
    print("종목 코드 예시: AAPL (미국), 005930.KS (코스피), 086520.KQ (코스닥)")
    ticker = ""
    while not ticker:
        ticker = ask("종목 코드").upper()
    days = ask_int("출력할 거래일 수", 5)
    chart = ask("이동평균선 차트도 저장할까요? (y/n)", "n").lower() in ("y", "yes")
    months = ask_int("차트 기간(개월)", 6) if chart else 6
    return ticker, days, chart, months


def parse_args():
    parser = argparse.ArgumentParser(description="간단한 주가 조회기 (인자 없이 실행하면 질문을 받습니다)")
    parser.add_argument("ticker", nargs="?", help="종목 코드 (예: AAPL, 005930.KS, 086520.KQ)")
    parser.add_argument("days", nargs="?", type=int, default=5, help="출력할 거래일 수 (기본 5)")
    parser.add_argument("--chart", action="store_true", help="이동평균선 차트를 charts/ 에 저장")
    parser.add_argument("--months", type=int, default=6, help="차트 기간(개월, 기본 6)")
    args = parser.parse_args()

    if args.ticker:
        return args.ticker, args.days, args.chart, args.months
    return ask_inputs()


def main():
    try:
        ticker, days, chart, months = parse_args()
    except (KeyboardInterrupt, EOFError):
        print("\n종료합니다.")
        return

    # 이동평균(60일)이 차트 첫날부터 나오도록, 요청 기간 + 약 4개월을 더 받아 계산한 뒤 자른다
    # 차트가 없으면 요청한 거래일 수를 채울 만큼만 받는다 (한 달 약 20거래일)
    fetch_months = months + 4 if chart else max(1, -(-days // 20) + 1)
    try:
        history, currency = get_history(ticker, f"{fetch_months}mo")
    except ValueError as e:
        print(e)
        return

    close = history["Close"]
    print_prices(ticker, close, days, currency)

    if chart:
        df = add_moving_averages(close)
        df = df[df.index >= df.index[-1] - pd.DateOffset(months=months)]
        path = CHART_DIR / f"{ticker}.png"
        plot_chart(ticker, df, path, currency)
        print(f"차트 저장: {path}")


if __name__ == "__main__":
    main()
