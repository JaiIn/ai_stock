# 07. Market Data Pipeline

## 1. 목적

추천 엔진과 모의투자 엔진이 사용할 수 있도록 토스증권 API 데이터를 안정적으로 수집·정규화·저장한다.

## 2. 수집 대상

| 데이터 | Endpoint | 저장 여부 | 캐시 TTL |
|---|---|---|---|
| 현재가 | `/api/v1/prices` | Yes | 5~30초 |
| 캔들 | `/api/v1/candles` | Yes | 1m: 60초, 1d: 1일 |
| 종목정보 | `/api/v1/stocks` | Yes | 1일 |
| 경고정보 | `/api/v1/stocks/{symbol}/warnings` | Yes | 1~5분 |
| 환율 | `/api/v1/exchange-rate` | Yes | 1분 |
| 장 운영 | `/api/v1/market-calendar/{KR|US}` | Yes | 1일 |
| 호가 | `/api/v1/orderbook` | Optional | 1~5초 |
| 체결 | `/api/v1/trades` | Optional | 1~5초 |

## 3. 수집 플로우

```text
watchlist
  → split symbols into batches of <= 200
  → getPrices
  → getStocks cache miss only
  → getWarnings per symbol
  → getCandles per symbol
  → normalize decimals
  → save snapshots
  → emit data quality report
```

## 4. 데이터 품질 검증

- 현재가가 0 이하이면 invalid
- 캔들 high < low이면 invalid
- close가 high/low 범위 밖이면 invalid
- timestamp timezone 누락 시 invalid
- currency가 KRW/USD 외 값이면 warning만 기록하고 처리

## 5. Indicator v0.1

- 1일 수익률
- 5일/20일 이동평균
- 이동평균 괴리율
- 최근 N봉 변동성
- 거래량 변화율
- 추세 점수
- 리스크 점수

## 6. 캐싱 정책

- API 호출량을 줄이기 위해 DB cache 우선
- UI refresh 버튼을 눌렀을 때만 강제 갱신
- 429 발생 시 해당 rate group 쿨다운

## 7. 장애 대응

- Toss API 장애: 마지막 정상 snapshot 사용 + stale 표시
- 종목 일부 실패: 전체 실패 처리하지 말고 실패 종목만 warning
- 환율 실패: 미국 주식 원화 환산 비활성화
