# stock-viewer

종목 코드를 입력하면 최근 종가와 기간 등락률을 보여주는 간단한 주가 조회기입니다.
Python과 Git/GitHub를 익히기 위한 첫 프로젝트입니다.

## 실행 방법

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py AAPL           # 애플 최근 5거래일
python main.py 005930.KS 10   # 삼성전자(코스피) 최근 10거래일
```

종목 코드 형식: 미국은 `AAPL`, 코스피는 `005930.KS`, 코스닥은 `035720.KQ`

## 출력 예시

```
[AAPL] 최근 5거래일 종가
  2026-10-05  332.89
  ...
기간 등락률: +1.13%
```

## 사용 기술
- Python 3
- [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance 데이터)

## 다음 계획
- [ ] 이동평균선 계산
- [ ] 차트 그리기 (matplotlib)
- [ ] 여러 종목 한 번에 조회
