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
    """종목의 일봉 데이터를 가져온다."""
    history = yf.Ticker(ticker).history(period=period)
    if history.empty:
        raise ValueError(f"'{ticker}' 데이터를 찾을 수 없습니다. 종목 코드를 확인하세요.")
    return history


def add_moving_averages(close, windows=MA_WINDOWS):
    """종가에 이동평균을 계산해 DataFrame으로 돌려준다. (앞쪽 기간은 NaN)"""
    df = close.to_frame("close")
    for w in windows:
        df[f"ma{w}"] = close.rolling(window=w).mean()
    return df


def plot_chart(ticker: str, df, path: Path):
    """종가와 이동평균선을 그려 PNG로 저장한다."""
    plt.rcParams["font.family"] = ["AppleGothic", "sans-serif"]  # 한글 (macOS)
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.plot(df.index, df["close"], color=COLORS["close"], linewidth=1.5, label="종가")
    for w in MA_WINDOWS:
        series = df[f"ma{w}"].dropna()
        if not series.empty:
            ax.plot(series.index, series, color=COLORS[w], linewidth=1.5, label=f"{w}일 이동평균")

    ax.set_title(f"{ticker} 종가와 이동평균선", loc="left", color=INK, fontsize=13)
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


def print_prices(ticker: str, close, days: int):
    prices = close.tail(days)
    print(f"[{ticker}] 최근 {len(prices)}거래일 종가")
    for date, price in prices.items():
        print(f"  {date:%Y-%m-%d}  {price:,.2f}")
    change = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
    print(f"기간 등락률: {change:+.2f}%")


def main():
    parser = argparse.ArgumentParser(description="간단한 주가 조회기")
    parser.add_argument("ticker", help="종목 코드 (예: AAPL, 005930.KS, 035720.KQ)")
    parser.add_argument("days", nargs="?", type=int, default=5, help="출력할 거래일 수 (기본 5)")
    parser.add_argument("--chart", action="store_true", help="이동평균선 차트를 charts/ 에 저장")
    parser.add_argument("--months", type=int, default=6, help="차트 기간(개월, 기본 6)")
    args = parser.parse_args()

    # 이동평균(60일)이 차트 첫날부터 나오도록, 요청 기간 + 약 3개월을 더 받아 계산한 뒤 자른다
    fetch_months = args.months + 4 if args.chart else 1
    try:
        history = get_history(args.ticker, f"{fetch_months}mo")
    except ValueError as e:
        print(e)
        return

    close = history["Close"]
    print_prices(args.ticker, close, args.days)

    if args.chart:
        df = add_moving_averages(close)
        df = df[df.index >= df.index[-1] - pd.DateOffset(months=args.months)]
        path = CHART_DIR / f"{args.ticker}.png"
        plot_chart(args.ticker, df, path)
        print(f"차트 저장: {path}")


if __name__ == "__main__":
    main()
