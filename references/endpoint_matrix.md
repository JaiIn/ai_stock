# Endpoint Matrix

MS-05.01 기준 재검증 문서입니다.

- 공식 확인 출처: `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`
- 공식 문서 버전: OpenAPI 3.1.0 / API version 1.1.1
- 확인 방식: read-only 문서 확인
- 금지 준수: 실제 API 호출, OAuth token 발급, credential/accountSeq 요청 없음

## Confidence level

- High: 공식 OpenAPI에서 path, method, auth/account header, 주요 schema를 확인함
- Medium: 공식 schema는 확인했으나 현재 프로젝트 mock/model/parser와 일부 정합성 보완 필요
- Low: 프로젝트 미구현 또는 후속 구현 범위에서 상세 재검증 필요

## Matrix

| API category | Endpoint name | Method | Path | Auth required | accountSeq required | Read-only | Project support status | Current implementation status | Schema confidence | Recheck notes | Source reference |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| Auth / OAuth | issueOAuth2Token | POST | `/oauth2/token` | No | No | No token mutation only | Mock only | Token request/response model and mock provider exist; live token request blocked | High | Form body uses `grant_type`, `client_id`, `client_secret`; response uses OAuth fields, not common `result` envelope | Official OpenAPI `/oauth2/token` |
| Stock Info | getStocks | GET | `/api/v1/stocks` | Yes | No | Yes | Supported mock/request-definition scope | Mock client request definition and response parsing exist | High | Query `symbols` is comma-separated and limited to 200; current model covers minimal required/optional fields only | Official OpenAPI `/api/v1/stocks` |
| Stock Info | getStockWarnings | GET | `/api/v1/stocks/{symbol}/warnings` | Yes | No | Yes | Supported mock/request-definition scope | Mock client request definition and response parsing exist | High | Response is an array; no warning returns an empty array; missing stock can return 404 | Official OpenAPI `/api/v1/stocks/{symbol}/warnings` |
| Market Data | getOrderbook | GET | `/api/v1/orderbook` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Result object includes timestamp, currency, asks, bids; each level has price and volume | Official OpenAPI `/api/v1/orderbook` |
| Market Data | getPrices | GET | `/api/v1/prices` | Yes | No | Yes | Supported mock/request-definition scope | Mock client request definition and response parsing exist | High | Query `symbols` is comma-separated and limited to 200; result is an array of price snapshots | Official OpenAPI `/api/v1/prices` |
| Market Data | getTrades | GET | `/api/v1/trades` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Query `symbol`; optional `count` max 50; result is recent trade array | Official OpenAPI `/api/v1/trades` |
| Market Data | getPriceLimit | GET | `/api/v1/price-limits` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Result includes timestamp, upperLimitPrice, lowerLimitPrice, currency; US limit fields can be null | Official OpenAPI `/api/v1/price-limits` |
| Market Data | getCandles | GET | `/api/v1/candles` | Yes | No | Yes | Supported mock/request-definition scope with parser follow-up | Request definition exists; parser requires schema alignment | Medium | Official result root is an object with `candles` and `nextBefore`; current parser assumption must be rechecked/aligned | Official OpenAPI `/api/v1/candles` |
| Market Info | getExchangeRate | GET | `/api/v1/exchange-rate` | Yes | No | Yes | Supported mock/request-definition scope with required correction | Request/model assumptions require schema alignment | Medium | Official query only has optional `dateTime`; result fields include `baseCurrency`, `quoteCurrency`, `rate`, `validFrom`, `validUntil` | Official OpenAPI `/api/v1/exchange-rate` |
| Market Info | getKrMarketCalendar | GET | `/api/v1/market-calendar/KR` | Yes | No | Yes | Future read-only candidate | Not implemented | Low | Calendar support is outside current mock clients; keep as future read-only candidate | Official OpenAPI `/api/v1/market-calendar/KR` |
| Market Info | getUsMarketCalendar | GET | `/api/v1/market-calendar/US` | Yes | No | Yes | Future read-only candidate | Not implemented | Low | Calendar support is outside current mock clients; keep as future read-only candidate | Official OpenAPI `/api/v1/market-calendar/US` |
| Account | getAccounts | GET | `/api/v1/accounts` | Yes | No | Yes | Future approval required | Not implemented | Low | Read-only but returns `accountSeq`; not part of current local/mock-only implementation | Official OpenAPI `/api/v1/accounts` |
| Asset | getHoldings | GET | `/api/v1/holdings` | Yes | Yes | Yes | Future approval required | Not implemented | Low | Read-only but account-scoped; requires `X-Tossinvest-Account`; excluded from current scope | Official OpenAPI `/api/v1/holdings` |
| Order History | getOrders | GET | `/api/v1/orders` | Yes | Yes | Yes | Future approval required | Not implemented | Low | Read-only order history; account-scoped and outside current implementation scope | Official OpenAPI `/api/v1/orders` GET |
| Order History | getOrder | GET | `/api/v1/orders/{orderId}` | Yes | Yes | Yes | Future approval required | Not implemented | Low | Read-only order detail; account-scoped and outside current implementation scope | Official OpenAPI `/api/v1/orders/{orderId}` GET |
| Order Info | getBuyingPower | GET | `/api/v1/buying-power` | Yes | Yes | Yes | Future approval required | Not implemented | Low | Read-only but account/order-adjacent; excluded from current scope | Official OpenAPI `/api/v1/buying-power` |
| Order Info | getSellableQuantity | GET | `/api/v1/sellable-quantity` | Yes | Yes | Yes | Future approval required | Not implemented | Low | Read-only but account/order-adjacent; excluded from current scope | Official OpenAPI `/api/v1/sellable-quantity` |
| Order Info | getCommissions | GET | `/api/v1/commissions` | Yes | Yes | Yes | Future approval required | Not implemented | Low | Read-only but order-adjacent; excluded from current scope | Official OpenAPI `/api/v1/commissions` |
| Order Mutation | createOrder | POST | `/api/v1/orders` | Yes | Yes | No | Denylisted | Not implemented | High | Real order mutation; must remain blocked unless explicitly re-scoped by user | Official OpenAPI `/api/v1/orders` POST |
| Order Mutation | modifyOrder | POST | `/api/v1/orders/{orderId}/modify` | Yes | Yes | No | Denylisted | Not implemented | High | Real order mutation; must remain blocked unless explicitly re-scoped by user | Official OpenAPI `/api/v1/orders/{orderId}/modify` |
| Order Mutation | cancelOrder | POST | `/api/v1/orders/{orderId}/cancel` | Yes | Yes | No | Denylisted | Not implemented | High | Real order mutation; must remain blocked unless explicitly re-scoped by user | Official OpenAPI `/api/v1/orders/{orderId}/cancel` |

## MS-05.02 이후 code alignment 후보

1. `getExchangeRate` request/query와 response model/parser를 공식 schema에 맞게 정렬합니다.
2. `getCandles` parser가 공식 result object의 `candles`와 `nextBefore`를 처리하도록 보완합니다.
3. `orderbook`, `trades`, `price-limits` response model/parser 지원 여부를 별도 Micro Stage에서 결정합니다.
4. `stocks` optional fields 확장 여부를 별도 Micro Stage에서 결정합니다.
5. Account/Asset/Order History/Order Info read-only endpoint는 accountSeq와 계좌 정보가 필요하므로 별도 사용자 승인 전까지 구현하지 않습니다.
6. Order Mutation endpoint는 write/order denylist에 유지합니다.
