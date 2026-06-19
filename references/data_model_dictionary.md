# Data Model Dictionary

## 1. API 주요 모델

### Account

| Field | Type | 설명 |
|---|---|---|
| `accountNo` | string | 계좌번호. 화면/로그에서는 마스킹 |
| `accountSeq` | int64 | API 호출용 계좌 식별자 |
| `accountType` | string | 계좌 유형. unknown enum 허용 |

### PriceResponse

| Field | Type | 설명 |
|---|---|---|
| `symbol` | string | 종목 심볼 |
| `timestamp` | datetime | 시세 시각 |
| `lastPrice` | decimal string | 현재가 |
| `currency` | enum | KRW/USD |

### Candle

| Field | Type | 설명 |
|---|---|---|
| `timestamp` | datetime | 봉 시작 시각 |
| `openPrice` | decimal string | 시가 |
| `highPrice` | decimal string | 고가 |
| `lowPrice` | decimal string | 저가 |
| `closePrice` | decimal string | 종가 |
| `volume` | decimal string | 거래량 |
| `currency` | enum | 통화 |

### StockInfo

| Field | Type | 설명 |
|---|---|---|
| `symbol` | string | 종목 코드/티커 |
| `name` | string | 종목명 |
| `englishName` | string | 영문명 |
| `isinCode` | string | ISIN |
| `market` | string | KOSPI/NASDAQ 등 |
| `securityType` | string | STOCK/ETF 등 |
| `status` | string | ACTIVE 등 |
| `currency` | enum | KRW/USD |
| `koreanMarketDetail` | object/null | 국내 종목 상세 |

### StockWarning

| Field | Type | 설명 |
|---|---|---|
| `warningType` | string | 투자경고/VI/정리매매 등 |
| `exchange` | string | KRX 등 |
| `startDate` | date | 시작일 |
| `endDate` | date/null | 종료일 |

### HoldingItem

| Field | Type | 설명 |
|---|---|---|
| `symbol` | string | 종목 |
| `name` | string | 종목명 |
| `marketCountry` | enum | KR/US |
| `currency` | enum | KRW/USD |
| `quantity` | decimal string | 보유 수량 |
| `lastPrice` | decimal string | 현재가 |
| `averagePurchasePrice` | decimal string | 평균 매입가 |
| `marketValue` | object | 평가금액 |
| `profitLoss` | object | 손익 |
| `dailyProfitLoss` | object | 일간 손익 |
| `cost` | object | 수수료/세금 |

### Order

| Field | Type | 설명 |
|---|---|---|
| `orderId` | string | 주문 식별자 |
| `symbol` | string | 종목 |
| `side` | enum | BUY/SELL |
| `orderType` | enum | LIMIT/MARKET |
| `timeInForce` | enum | DAY/CLS |
| `status` | enum | 주문 상태 |
| `price` | decimal string/null | 주문 가격 |
| `quantity` | decimal string/null | 주문 수량 |
| `orderAmount` | decimal string/null | 금액 주문 |
| `currency` | enum | KRW/USD |
| `orderedAt` | datetime | 주문 시각 |
| `execution` | object | 체결 정보 |

## 2. 내부 DB 모델

### watchlists

| Column | Type | 설명 |
|---|---|---|
| `id` | integer | PK |
| `symbol` | string | 종목 |
| `market_country` | string | KR/US |
| `memo` | text | 사용자 메모 |
| `is_active` | bool | 활성 여부 |
| `created_at` | datetime | 생성일 |

### price_snapshots

| Column | Type | 설명 |
|---|---|---|
| `id` | integer | PK |
| `symbol` | string | 종목 |
| `timestamp` | datetime | 시세 시각 |
| `last_price` | decimal | 현재가 |
| `currency` | string | 통화 |
| `raw_json` | json | 원본 응답 |

### recommendation_runs

| Column | Type | 설명 |
|---|---|---|
| `id` | integer | PK |
| `run_at` | datetime | 실행 시각 |
| `strategy_version` | string | scoring 버전 |
| `llm_model` | string/null | 사용 모델 |
| `input_symbols` | json | 입력 종목 |
| `summary` | text | 실행 요약 |

### recommendations

| Column | Type | 설명 |
|---|---|---|
| `id` | integer | PK |
| `run_id` | FK | recommendation_runs |
| `symbol` | string | 종목 |
| `rating` | string | BUY_CANDIDATE/WATCH/HOLD/REDUCE/BLOCKED |
| `score` | decimal | 점수 |
| `risk_score` | decimal | 위험 점수 |
| `reasons_json` | json | 근거 |
| `ai_explanation` | text | AI 설명 |

### paper_orders

| Column | Type | 설명 |
|---|---|---|
| `id` | integer | PK |
| `portfolio_id` | FK | portfolio |
| `symbol` | string | 종목 |
| `side` | string | BUY/SELL |
| `order_type` | string | MARKET/LIMIT |
| `quantity` | decimal | 수량 |
| `limit_price` | decimal/null | 지정가 |
| `status` | string | PENDING/FILLED/CANCELED/REJECTED |
| `created_at` | datetime | 생성 시각 |
| `filled_at` | datetime/null | 체결 시각 |
| `filled_price` | decimal/null | 체결가 |

### audit_logs

| Column | Type | 설명 |
|---|---|---|
| `id` | integer | PK |
| `event_type` | string | 예: API_CALL, PAPER_ORDER, RECOMMENDATION |
| `level` | string | INFO/WARN/ERROR |
| `message` | text | 마스킹된 메시지 |
| `request_id` | string/null | Toss request id |
| `metadata_json` | json | 부가 정보 |
| `created_at` | datetime | 생성 시각 |
