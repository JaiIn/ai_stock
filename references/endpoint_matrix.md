# Endpoint Matrix

## Auth

| Endpoint | Method | Auth | Account header | Rate group | 구현 우선순위 |
|---|---:|---|---|---|---|
| `/oauth2/token` | POST | No | No | AUTH | P0 |

## Market Data

| Endpoint | Method | Auth | Account header | Rate group | v0.1 사용 |
|---|---:|---|---|---|---|
| `/api/v1/orderbook` | GET | Yes | No | MARKET_DATA | 선택 |
| `/api/v1/prices` | GET | Yes | No | MARKET_DATA | 필수 |
| `/api/v1/trades` | GET | Yes | No | MARKET_DATA | 선택 |
| `/api/v1/price-limits` | GET | Yes | No | MARKET_DATA | 필수 |
| `/api/v1/candles` | GET | Yes | No | MARKET_DATA_CHART | 필수 |

## Stock Info

| Endpoint | Method | Auth | Account header | Rate group | v0.1 사용 |
|---|---:|---|---|---|---|
| `/api/v1/stocks` | GET | Yes | No | STOCK | 필수 |
| `/api/v1/stocks/{symbol}/warnings` | GET | Yes | No | STOCK | 필수 |

## Market Info

| Endpoint | Method | Auth | Account header | Rate group | v0.1 사용 |
|---|---:|---|---|---|---|
| `/api/v1/exchange-rate` | GET | Yes | No | MARKET_INFO | 필수 |
| `/api/v1/market-calendar/KR` | GET | Yes | No | MARKET_INFO | 필수 |
| `/api/v1/market-calendar/US` | GET | Yes | No | MARKET_INFO | 필수 |

## Account / Asset

| Endpoint | Method | Auth | Account header | Rate group | v0.1 사용 |
|---|---:|---|---|---|---|
| `/api/v1/accounts` | GET | Yes | No | ACCOUNT | 필수 |
| `/api/v1/holdings` | GET | Yes | Yes | ASSET | 필수 |

## Order History / Info

| Endpoint | Method | Auth | Account header | Rate group | v0.1 사용 |
|---|---:|---|---|---|---|
| `/api/v1/orders` | GET | Yes | Yes | ORDER_HISTORY | 선택 |
| `/api/v1/orders/{orderId}` | GET | Yes | Yes | ORDER_HISTORY | 선택 |
| `/api/v1/buying-power` | GET | Yes | Yes | ORDER_INFO | 필수 |
| `/api/v1/sellable-quantity` | GET | Yes | Yes | ORDER_INFO | 필수 |
| `/api/v1/commissions` | GET | Yes | Yes | ORDER_INFO | 필수 |

## Order Mutation — v0.1 차단

| Endpoint | Method | Auth | Account header | Rate group | v0.1 정책 |
|---|---:|---|---|---|---|
| `/api/v1/orders` | POST | Yes | Yes | ORDER | 코드 레벨 차단 |
| `/api/v1/orders/{orderId}/modify` | POST | Yes | Yes | ORDER | 코드 레벨 차단 |
| `/api/v1/orders/{orderId}/cancel` | POST | Yes | Yes | ORDER | 코드 레벨 차단 |
