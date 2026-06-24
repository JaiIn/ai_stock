# 02. Toss Open API reference

MS-05.01에서 공식 Toss OpenAPI 문서를 read-only로 재확인하고, MS-05.02에서
`getExchangeRate`와 `getCandles` mock schema를 정렬한 기준 문서입니다.

- 공식 OpenAPI: `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`
- 개발자 문서: `https://developers.tossinvest.com/`
- 확인 기준일: 2026-06-24
- 공식 문서 버전: OpenAPI 3.1.0 / API version 1.1.1
- 이번 단계 금지 사항: 실제 API 호출, 실제 OAuth token 발급, 실제 Client ID / Client Secret / Access Token / accountSeq 요청

## 1. 프로젝트 지원 범위

현재 프로젝트의 우선 범위는 로컬 전용, mock 기반, read-only 데이터 흐름입니다.

지원 또는 후보 범위:

- Auth/OAuth: token request/response model, mock token provider, live token request 차단
- Stock Info: `getStocks`, `getStockWarnings`
- Market Data: `getPrices`, `getCandles`, 그리고 후속 검토 대상 `getOrderbook`, `getTrades`, `getPriceLimit`
- Market Info: `getExchangeRate`
- Account/Asset/Order History/Order Info: read-only라도 accountSeq 또는 계좌 정보가 필요하므로 별도 승인 전까지 구현하지 않음

명시적 금지 범위:

- 실제 주문 생성, 정정, 취소 API
- 실계좌 주문 전송 함수
- 실주문/실체결/실잔고/실계좌 자동화
- API Key, token, client secret, accountSeq 저장

## 2. 공통 인증 및 응답 구조

| 항목 | 공식 재검증 결과 |
|---|---|
| Base URL | `https://openapi.tossinvest.com` |
| Auth 방식 | OAuth 2.0 Client Credentials |
| API 인증 header | `Authorization: Bearer <access_token>` |
| account-scoped API header | `X-Tossinvest-Account: <accountSeq>` |
| 일반 API 성공 envelope | `{ "result": ... }` |
| 일반 API 실패 envelope | `{ "error": { "requestId", "code", "message", "data"? } }` |
| OAuth token endpoint envelope | OAuth 표준 response이며 일반 `result` envelope가 아님 |

## 3. Auth / OAuth

### `POST /oauth2/token`

- 목적: OAuth access token 발급
- 인증 header: 없음
- Content-Type: `application/x-www-form-urlencoded`
- Body:
  - `grant_type=client_credentials`
  - `client_id`
  - `client_secret`
- Response:
  - `access_token`
  - `token_type`
  - `expires_in`
- OAuth error:
  - `error`
  - `error_description`

프로젝트 현재 상태:

- token model과 mock provider만 구현되어 있습니다.
- 실제 token 발급 HTTP 호출은 구현하지 않았고, `ALLOW_LIVE_API=false` 상태에서 live token request를 차단합니다.
- MS-05.01에서 실제 OAuth token 발급은 수행하지 않았습니다.

## 4. Stock Info

| Operation | Method | Path | 주요 parameter | 공식 response 요약 | 현재 상태 |
|---|---|---|---|---|---|
| getStocks | GET | `/api/v1/stocks` | `symbols` comma-separated, max 200 | `result` array; `symbol`, `name`, `market`, `currency`, `englishName`, `isinCode`, `securityType`, `status` 등 | Mock request/parsing 구현됨; optional field 확장 후보 |
| getStockWarnings | GET | `/api/v1/stocks/{symbol}/warnings` | path `symbol` | `result` array; `warningType`, `exchange`, `startDate`, `endDate`; 경고 없음은 empty array | Mock request/parsing 구현됨 |

재검증 메모:

- 공식 필드명은 `symbol` 중심입니다.
- `stockCode` 같은 별도 필드명은 현재 확인 범위에서 기본 필드로 두지 않습니다.
- 현재 프로젝트 모델은 최소 필드 위주이며, 모든 optional official field를 아직 반영하지 않았습니다.

## 5. Market Data

| Operation | Method | Path | 주요 parameter | 공식 response 요약 | 현재 상태 |
|---|---|---|---|---|---|
| getOrderbook | GET | `/api/v1/orderbook` | `symbol` | `timestamp`, `currency`, `asks[]`, `bids[]`; level은 `price`, `volume` | Request definition 후보; parser/model 후속 |
| getPrices | GET | `/api/v1/prices` | `symbols` comma-separated, max 200 | `result` array; `symbol`, `timestamp`, `lastPrice`, `currency` | Mock request/parsing 구현됨 |
| getTrades | GET | `/api/v1/trades` | `symbol`, optional `count` max 50 | `result` array; `price`, `volume`, `timestamp`, `currency` | Request definition 후보; parser/model 후속 |
| getPriceLimit | GET | `/api/v1/price-limits` | `symbol` | `timestamp`, `upperLimitPrice`, `lowerLimitPrice`, `currency` | Request definition 후보; parser/model 후속 |
| getCandles | GET | `/api/v1/candles` | `symbol`, `interval`, optional `count`, `before`, `adjusted` | `result` object; `candles[]`, optional `nextBefore` | Mock request와 `CandlePage` parser 정렬 완료 |

재검증 메모:

- `getCandles`의 공식 response root는 배열이 아니라 object입니다.
- `candles[]` 내부에는 `timestamp`, `openPrice`, `highPrice`, `lowPrice`, `closePrice`, `volume` 등이 포함됩니다.
- MS-05.02에서 `CandlePage.candles`와 `CandlePage.next_before`로 공식 root를 보존하도록 정렬했습니다.
- timestamp/dateTime 표시와 numeric string 처리 정책은 모델별 후속 검증이 필요합니다.

## 6. Market Info / Exchange Rate

### `GET /api/v1/exchange-rate`

공식 재검증 결과:

- Auth required: Yes
- accountSeq required: No
- Query:
  - optional `dateTime`
- Response result:
  - `baseCurrency`
  - `quoteCurrency`
  - `rate`
  - `validFrom`
  - `validUntil`

MS-05.02 alignment 결과:

- request builder는 optional `dateTime`만 query로 구성합니다.
- `baseCurrency`, `quoteCurrency` query는 더 이상 요구하거나 전송하지 않습니다.
- parser는 response의 `baseCurrency`, `quoteCurrency`, `rate`, `validFrom`, `validUntil`을 처리합니다.
- 금융 숫자는 `Decimal`로 복원합니다.
- 기존 SQLite 저장 계층 호환을 위해 내부 필드 `exchange_rate`를 유지하고 공식 이름 `rate` property를 제공합니다.
- `valid_from`, `valid_until`은 optional field로 보존합니다.
- 실제 API 호출과 OAuth token 발급은 구현하거나 수행하지 않았습니다.
- 이 단계에서는 API KEY, SECRET KEY, Client ID, Client Secret, Access Token, accountSeq가 필요하지 않습니다.

## 7. Account / Asset / Order 계열 분리

Account/Asset/Order History/Order Info API에는 read-only endpoint가 포함되어 있지만, 대부분 accountSeq 또는 계좌 정보를 필요로 합니다.

현재 정책:

- `GET /api/v1/accounts`는 read-only지만 `accountSeq`를 반환하므로 별도 승인 전까지 구현하지 않습니다.
- `GET /api/v1/holdings`, `GET /api/v1/orders`, `GET /api/v1/orders/{orderId}`, `GET /api/v1/buying-power`, `GET /api/v1/sellable-quantity`, `GET /api/v1/commissions`는 account-scoped read-only 후보로만 문서화합니다.
- 주문 생성/정정/취소 endpoint는 write/order denylist에 유지합니다.

Write/order denylist:

- `POST /api/v1/orders`
- `POST /api/v1/orders/{orderId}/modify`
- `POST /api/v1/orders/{orderId}/cancel`

## 8. MS-05.03 Live API Safety Gate

Safety gate는 실제 request나 인증 context를 만들지 않고 method, path, category,
auth/account 요구 여부와 설정 flag만 검사합니다.

Dry-run 평가 allowlist:

- `GET /api/v1/stocks`
- `GET /api/v1/stocks/{symbol}/warnings`
- `GET /api/v1/prices`
- `GET /api/v1/candles`
- `GET /api/v1/exchange-rate`

Pending 상태로 기본 차단:

- `GET /api/v1/orderbook`
- `GET /api/v1/trades`
- `GET /api/v1/price-limits`
- market calendar 계열
- unknown endpoint

Account-scoped API는 read-only 여부와 무관하게 별도 승인 전까지 차단합니다.

- `/api/v1/accounts`
- `/api/v1/holdings`
- `/api/v1/orders` GET
- `/api/v1/orders/{orderId}` GET
- `/api/v1/buying-power`
- `/api/v1/sellable-quantity`
- `/api/v1/commissions`

Write/order denylist는 설정과 무관하게 항상 차단합니다.

- `POST /api/v1/orders`
- `POST /api/v1/orders/{orderId}/modify`
- `POST /api/v1/orders/{orderId}/cancel`
- category가 `order`, `write`, `trading`, `mutation`인 endpoint
- `POST`, `PUT`, `PATCH`, `DELETE` method 후보

설정 정책:

- `ALLOW_LIVE_API=false`: live 후보 차단
- `ALLOW_REAL_ORDER=true`: critical 위험 상태로 차단
- `DRY_RUN_ONLY=true`: metadata 평가만 허용하고 send 후보 차단
- 이번 단계에서는 실제 API 호출, OAuth token 발급, 인증 요청을 수행하지 않습니다.

## 9. MS-05.03 이후 작업 후보

1. `orderbook`, `trades`, `price-limits`의 최소 response model/parser 구현 여부를 결정합니다.
2. `StockInfo` optional official fields 확장 범위를 결정합니다.
3. timestamp/dateTime 정규화와 Decimal 표시 자릿수 정책을 별도 단계에서 결정합니다.
4. Account/Asset/Order History/Order Info read-only API는 accountSeq 요구 여부와 안전 정책을 재확인한 뒤 별도 Micro Stage로만 다룹니다.
5. Order Mutation API는 계속 denylist에 둡니다.
