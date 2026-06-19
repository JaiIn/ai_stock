# 02. 토스증권 Open API 레퍼런스 요약

## 1. 공통 정보

| 항목 | 값 |
|---|---|
| Base URL | `https://openapi.tossinvest.com` |
| 인증 | OAuth 2.0 Client Credentials Grant |
| Token endpoint | `POST /oauth2/token` |
| 공통 인증 헤더 | `Authorization: Bearer {access_token}` |
| 계좌 API 추가 헤더 | `X-Tossinvest-Account: {accountSeq}` |
| 성공 envelope | `{ "result": ... }` |
| 실패 envelope | `{ "error": { "requestId", "code", "message", "data"? } }` |

## 2. 인증

### `POST /oauth2/token`

- 목적: access token 발급
- 인증 헤더: 없음
- Content-Type: `application/x-www-form-urlencoded`
- Body:
  - `grant_type=client_credentials`
  - `client_id`
  - `client_secret`
- 응답:
  - `access_token`
  - `token_type=Bearer`
  - `expires_in`

주의:

- refresh token은 제공되지 않는 것으로 설계한다.
- 만료 전 자동 갱신한다.
- token 재발급 시 이전 token이 무효화될 수 있으므로 다중 프로세스에서는 token cache lock이 필요하다.

## 3. Market Data

| Method | Path | Operation | 주요 파라미터 | 용도 |
|---|---|---|---|---|
| GET | `/api/v1/orderbook` | `getOrderbook` | `symbol` | 호가 조회 |
| GET | `/api/v1/prices` | `getPrices` | `symbols` 최대 200개 | 현재가 다건 조회 |
| GET | `/api/v1/trades` | `getTrades` | `symbol`, `count<=50` | 최근 체결 조회 |
| GET | `/api/v1/price-limits` | `getPriceLimit` | `symbol` | 상/하한가 조회 |
| GET | `/api/v1/candles` | `getCandles` | `symbol`, `interval`, `count`, `before`, `adjusted` | 캔들 조회 |

### Candles

- `interval`: 문서상 `1m`, `1d` 중심으로 확인
- `count`: 최대 200
- `before`: exclusive timestamp, pagination에 사용
- `nextBefore`: 다음 페이지 커서

## 4. Stock Info

| Method | Path | Operation | 주요 파라미터 | 용도 |
|---|---|---|---|---|
| GET | `/api/v1/stocks` | `getStocks` | `symbols` 최대 200개 | 종목 기본 정보 |
| GET | `/api/v1/stocks/{symbol}/warnings` | `getStockWarnings` | `symbol` | 매수 유의사항/VI/투자경고 |

주의:

- `symbols`는 콤마 구분.
- KRX는 6자리 숫자, US는 ticker.
- warning이 없으면 빈 배열이 정상 응답이다.
- 종목이 없으면 `404 stock-not-found` 가능.

## 5. Market Info

| Method | Path | Operation | 주요 파라미터 | 용도 |
|---|---|---|---|---|
| GET | `/api/v1/exchange-rate` | `getExchangeRate` | `baseCurrency`, `quoteCurrency`, `dateTime?` | KRW/USD 환율 |
| GET | `/api/v1/market-calendar/KR` | `getKrMarketCalendar` | `date?` | 국내 장 운영 정보 |
| GET | `/api/v1/market-calendar/US` | `getUsMarketCalendar` | `date?` | 미국 장 운영 정보 |

주의:

- 환율은 표시/참고용이며 실제 주문 환율과 다를 수 있다.
- KR 장은 KRX/NXT 통합 세션 구조를 고려한다.
- US 장은 데이마켓/프리/정규/애프터마켓 구조를 고려한다.

## 6. Account / Asset

| Method | Path | Operation | 추가 헤더 | 용도 |
|---|---|---|---|---|
| GET | `/api/v1/accounts` | `getAccounts` | 없음 | 계좌 목록 조회 |
| GET | `/api/v1/holdings` | `getHoldings` | `X-Tossinvest-Account` | 보유 주식 조회 |

`GET /api/v1/accounts` 응답의 `accountSeq`를 이후 계좌 관련 API의 `X-Tossinvest-Account` 헤더로 사용한다.

## 7. Order History

| Method | Path | Operation | 주요 파라미터 | 용도 |
|---|---|---|---|---|
| GET | `/api/v1/orders` | `getOrders` | `status`, `symbol?`, `from?`, `to?`, `cursor?`, `limit?` | 주문 목록 조회 |
| GET | `/api/v1/orders/{orderId}` | `getOrder` | `orderId` | 주문 상세 조회 |

주의:

- `status=OPEN`은 진행 중 주문.
- `status=CLOSED` 지원 여부는 스펙 버전별로 달라질 수 있으므로 최신 OpenAPI로 검증한다.

## 8. Order Info

| Method | Path | Operation | 주요 파라미터 | 용도 |
|---|---|---|---|---|
| GET | `/api/v1/buying-power` | `getBuyingPower` | `currency` | 매수 가능 금액 |
| GET | `/api/v1/sellable-quantity` | `getSellableQuantity` | `symbol` | 판매 가능 수량 |
| GET | `/api/v1/commissions` | `getCommissions` | 없음 | 매매 수수료율 |

주의:

- 일부 사용자 문서 URL은 `order-info#getbuyingpower` 형태이지만 실제 path는 OpenAPI JSON으로 최종 확인한다.
- 모든 endpoint에 `X-Tossinvest-Account`가 필요하다.

## 9. Order mutation — v0.1 구현 금지

| Method | Path | Operation | 설명 |
|---|---|---|---|
| POST | `/api/v1/orders` | `createOrder` | 주문 생성 |
| POST | `/api/v1/orders/{orderId}/modify` | `modifyOrder` | 주문 정정 |
| POST | `/api/v1/orders/{orderId}/cancel` | `cancelOrder` | 주문 취소 |

v0.1에서는 client 메서드를 만들더라도 `ENABLE_LIVE_TRADING=false`면 무조건 예외를 발생시켜야 한다.

## 10. 주요 enum

### Currency

- `KRW`
- `USD`

### MarketCountry

- `KR`
- `US`

### Side

- `BUY`
- `SELL`

### OrderType

- `LIMIT`
- `MARKET`

### TimeInForce

- `DAY`
- `CLS`

### OrderStatus

- `PENDING`
- `PENDING_CANCEL`
- `PENDING_REPLACE`
- `PARTIAL_FILLED`
- `FILLED`
- `CANCELED`
- `REJECTED`
- `CANCEL_REJECTED`
- `REPLACE_REJECTED`
- `REPLACED`

## 11. 설계상 필수 구현

- token refresh
- 401 발생 시 1회 token 재발급 후 재시도
- 429 발생 시 `Retry-After` 기반 대기 후 재시도
- 모든 응답의 `X-Request-Id` 또는 `error.requestId` 저장
- unknown enum 허용
- Decimal 파싱
- Secret masking
