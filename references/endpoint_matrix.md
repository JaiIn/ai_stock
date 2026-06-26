# Endpoint Matrix

MS-05.01 공식 schema 재검증, MS-05.02 mock alignment, MS-05.03 safety gate
결정을 반영한 문서입니다.

- 공식 확인 출처: `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`
- 공식 문서 버전: OpenAPI 3.1.0 / API version 1.1.5
- 확인 방식: read-only 문서 확인
- 금지 준수: 실제 API 호출, OAuth token 발급, credential/accountSeq 요청 없음

## Confidence level

- High: 공식 OpenAPI에서 path, method, auth/account header, 주요 schema를 확인함
- Medium: 공식 schema는 확인했으나 현재 프로젝트 mock/model/parser와 일부 정합성 보완 필요
- Low: 프로젝트 미구현 또는 후속 구현 범위에서 상세 재검증 필요

## Matrix

| API category | Endpoint name | Method | Path | Auth required | accountSeq required | Read-only | Project support status | Current implementation status | Schema confidence | Recheck notes | Source reference |
|---|---|---:|---|---|---|---|---|---|---|---|---|
| Auth / OAuth | issueOAuth2Token | POST | `/oauth2/token` | No | No | No; auth token issuance only | Approved smoke-test-only path | Fixed endpoint provider and offline contract tests implemented; live execution requires local credentials and safety flags | High | Form body uses `grant_type`, `client_id`, `client_secret`; token remains memory-only and output is masked | Official OpenAPI `/oauth2/token` |
| Stock Info | getStocks | GET | `/api/v1/stocks` | Yes | No | Yes | Schema-aligned; future single live candidate | Required 1~200 symbols validation, full official StockInfo parser, safe error parser implemented | High | Symbol pattern allows letters, digits, `.`, `-`; next candidate is one official example `005930`, not executed in MS-05.09 | Official OpenAPI 1.1.5 `/api/v1/stocks` |
| Stock Info | getStockWarnings | GET | `/api/v1/stocks/{symbol}/warnings` | Yes | No | Yes | Schema-aligned; not selected for next live smoke | Required path symbol validation, warning array/empty array parser, safe error parser implemented | High | 404 `stock-not-found`; warning fields other than warningType are nullable; no live execution in MS-05.09 | Official OpenAPI 1.1.5 `/api/v1/stocks/{symbol}/warnings` |
| Market Data | getOrderbook | GET | `/api/v1/orderbook` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Result object includes timestamp, currency, asks, bids; each level has price and volume | Official OpenAPI `/api/v1/orderbook` |
| Market Data | getPrices | GET | `/api/v1/prices` | Yes | No | Yes | MS-05.12 schema-aligned; future single live candidate | Required 1~200 symbol validation, official PriceResponse parser, and safe error metadata implemented | High | Required `symbols`; symbol characters are letters, digits, `.`, `-`; nullable timestamp; Decimal lastPrice; next candidate is `symbols=005930` and was not executed in MS-05.12 | Official OpenAPI 1.1.5 `/api/v1/prices` |
| Market Data | getTrades | GET | `/api/v1/trades` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Query `symbol`; optional `count` max 50; result is recent trade array | Official OpenAPI `/api/v1/trades` |
| Market Data | getPriceLimit | GET | `/api/v1/price-limits` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Result includes timestamp, upperLimitPrice, lowerLimitPrice, currency; US limit fields can be null | Official OpenAPI `/api/v1/price-limits` |
| Market Data | getCandles | GET | `/api/v1/candles` | Yes | No | Yes | Supported mock/request-definition scope | Request definition and object-root parser aligned; `CandlePage` preserves `candles` and optional `nextBefore` | High | Fake official payload tests cover populated and missing `nextBefore`; no network transmission | Official OpenAPI `/api/v1/candles` |
| Market Info | getExchangeRate | GET | `/api/v1/exchange-rate` | Yes | No | Yes | MS-05.07 schema realigned; no live call | Required `baseCurrency`/`quoteCurrency`, optional `dateTime`, full official response parser, safe error metadata, and safety-gated smoke defaults implemented | High | API 1.1.5 requires currency pair; MS-05.06 HTTP 400 was likely caused by omitted required query; next approved retry prepared as USD/KRW | Official OpenAPI `/api/v1/exchange-rate` |
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

## MS-05.02 alignment 결과와 후속 후보

1. `getExchangeRate` request/query와 response model/parser 정렬을 완료했습니다.
2. `getCandles` parser의 `candles`와 optional `nextBefore` object-root 처리를 완료했습니다.
3. `orderbook`, `trades`, `price-limits` response model/parser 지원 여부를 별도 Micro Stage에서 결정합니다.
4. `stocks` optional fields 확장 여부를 별도 Micro Stage에서 결정합니다.
5. Account/Asset/Order History/Order Info read-only endpoint는 accountSeq와 계좌 정보가 필요하므로 별도 사용자 승인 전까지 구현하지 않습니다.
6. Order Mutation endpoint는 write/order denylist에 유지합니다.

## MS-05.03 Live API Safety Status

| Endpoint 또는 범주 | accountSeq required | Read-only allowlist | Write/order denylist | Current stage decision |
|---|---:|---:|---:|---|
| `GET /api/v1/stocks` | No | Yes | No | Dry-run metadata evaluation allowed |
| `GET /api/v1/stocks/{symbol}/warnings` | No | Yes | No | Dry-run metadata evaluation allowed |
| `GET /api/v1/prices` | No | Yes | No | Dry-run metadata evaluation allowed |
| `GET /api/v1/candles` | No | Yes | No | Dry-run metadata evaluation allowed |
| `GET /api/v1/exchange-rate` | No | Yes | No | Dry-run metadata evaluation allowed |
| `GET /api/v1/orderbook`, `/trades`, `/price-limits` | No | Pending | No | Default blocked pending separate approval |
| Account/Asset/Order read-only APIs | Yes or sensitive | No | No | Default blocked pending accountSeq approval |
| `POST /api/v1/orders` | Yes | No | Yes | Always blocked |
| `POST /api/v1/orders/{orderId}/modify` | Yes | No | Yes | Always blocked |
| `POST /api/v1/orders/{orderId}/cancel` | Yes | No | Yes | Always blocked |
| Unknown endpoint | Unknown | No | No | Fail-closed |

`ALLOW_LIVE_API=false`, `ALLOW_REAL_ORDER=true`, 또는 `DRY_RUN_ONLY=true` 상태의
send 후보는 차단합니다. 이 표의 allowlist는 실제 network send 승인이 아니라
metadata-only dry-run decision 범위입니다.

OAuth token endpoint는 업무 API allowlist와 분리된 MS-05.04 제한 경로입니다.
실제 호출은 `/oauth2/token` 한 번만 허용하며 credential이 없으면 실행하지 않습니다.

MS-05.05에서 실제 업무 API 호출 후보는 `GET /api/v1/exchange-rate` 한 개로
제한합니다. 기존 allowlist의 다른 GET endpoint는 이 smoke script에서 호출할 수
없으며 account-scoped 및 order/write endpoint는 계속 차단합니다.

최초 live 시도 실패 후 phase/status 진단만 보강했으며 추가 live 호출은 수행하지
않았습니다. 재시도는 별도 사용자 승인이 있어야 합니다.

MS-05.06에서 별도 승인된 smoke script를 정확히 한 번 실행했습니다. OAuth token
단계는 통과했고 `GET /api/v1/exchange-rate`가 HTTP 400, safe error code
`invalid-request`로 종료되었습니다. Raw response는 저장하지 않았고 추가 재시도는
수행하지 않았습니다.

MS-05.07 공식 OpenAPI API version 1.1.5 재확인 결과, `baseCurrency`와
`quoteCurrency`는 required query이고 `dateTime`만 optional입니다. Currency enum은
KRW/USD이며 성공 응답에는 `rate`, `midRate`, `basisPoint`, `rateChangeType`,
`validFrom`, `validUntil`이 포함됩니다. MS-05.06 HTTP 400은 required currency
query 누락이 원인일 가능성이 높습니다. 이번 정렬 단계에서는 실제 API와 OAuth
endpoint를 호출하지 않았습니다.

MS-05.08에서 별도 승인된 smoke script를 정확히 한 번 실행했습니다. OAuth token
endpoint 1회와 `GET /api/v1/exchange-rate?baseCurrency=USD&quoteCurrency=KRW`
1회만 호출했고 `dateTime`은 생략했습니다. 응답은 HTTP 200이었으며 USD/KRW,
`rate`, `midRate`, `basisPoint`, `rateChangeType`, `validFrom`, `validUntil`을
안전한 parser 결과로 확인했습니다. raw response와 credential/token/header
원문은 저장하지 않았고 추가 업무 API 호출도 수행하지 않았습니다.

MS-05.09에서 공식 OpenAPI 3.1.0 / API 1.1.5의 Stock Info schema를 정적으로
재확인했습니다. `getStocks`의 `symbols`는 required 1~200개이고,
`getStockWarnings`의 path `symbol`도 required입니다. 두 endpoint는 OAuth2
read-only이며 accountSeq가 필요 없습니다. 다음 live smoke 후보는 공식 예시
심볼 하나를 사용한 `GET /api/v1/stocks?symbols=005930`으로 제한했으며 이번
단계에서는 OAuth와 업무 API를 실제 호출하지 않았습니다.

MS-05.10에서 별도 승인된 Stock Info smoke script를 정확히 한 번 실행했습니다.
OAuth token endpoint 1회와 `GET /api/v1/stocks?symbols=005930` 1회만
호출했고 응답은 HTTP 200, result 1건이었습니다. 요청 symbol `005930`과
symbol/name/market/currency/sharesOutstanding 필드 존재를 안전한 parser
결과로 확인했습니다. warnings endpoint와 다른 업무 API는 호출하지 않았으며,
raw response와 credential/token/header 원문은 저장하지 않았습니다.

MS-05.11에서 별도 승인된 Stock Warnings smoke script를 정확히 한 번
실행했습니다. OAuth token endpoint 1회와
`GET /api/v1/stocks/005930/warnings` 1회만 호출했고 응답은 HTTP 200,
warning 0건의 정상 빈 배열이었습니다. 빈 warning 배열과 optional field 처리
경로가 정상 동작했으며 getStocks와 다른 업무 API는 호출하지 않았습니다.
raw response와 credential/token/header 원문은 저장하지 않았습니다.

MS-05.12에서 공식 OpenAPI 3.1.0 / API 1.1.5의 `getPrices` schema를 실제 API
호출 없이 재검증했습니다. `symbols`는 required 1~200개이고 각 symbol은 영문,
숫자, `.`, `-`만 허용합니다. 성공 응답은 required `symbol`, `lastPrice`,
`currency`와 nullable `timestamp`를 가진 배열이며 `lastPrice`는 `Decimal`로
처리합니다. 400/404/429/500 error는 safe metadata만 추출합니다. Safety Gate의
read-only/account-free 정책을 유지하며 다음 live 후보는 별도 승인 대상인
`GET /api/v1/prices?symbols=005930`입니다.
