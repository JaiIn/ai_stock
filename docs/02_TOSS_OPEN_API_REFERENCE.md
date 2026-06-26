# 02. Toss Open API reference

MS-05.01에서 공식 Toss OpenAPI 문서를 read-only로 재확인하고, MS-05.02에서
`getExchangeRate`와 `getCandles` mock schema를 정렬한 기준 문서입니다.

- 공식 OpenAPI: `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`
- 개발자 문서: `https://developers.tossinvest.com/`
- 확인 기준일: 2026-06-25
- 공식 문서 버전: OpenAPI 3.1.0 / API version 1.1.5
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

### MS-05.04 OAuth token smoke test 경로

- 실제 호출 허용 대상은 `POST /oauth2/token` 하나뿐입니다.
- Content-Type은 `application/x-www-form-urlencoded`입니다.
- Form field는 `grant_type`, `client_id`, `client_secret`입니다.
- Response의 `access_token`, `token_type`, `expires_in`만 메모리 모델로 처리합니다.
- Access Token은 파일로 저장하거나 원문 출력하지 않습니다.
- 실제 업무, read-only, 주문, 계좌, 자산, 잔고, 체결 endpoint는 호출하지 않습니다.
- 실행 전 `ALLOW_LIVE_API=true`, `ALLOW_REAL_ORDER=false`, `DRY_RUN_ONLY=true`를 확인합니다.
- Credential이 없는 경우 live smoke test를 수행하지 않습니다.

### MS-05.05 최초 read-only 업무 API smoke test

- 허용 업무 endpoint는 `GET /api/v1/exchange-rate` 하나뿐입니다.
- 실제 호출 순서는 OAuth token 발급 → Live API Safety Gate 평가 → 환율 GET입니다.
- Safety metadata는 `market_info`, auth 필요, accountSeq 불필요로 고정합니다.
- 응답은 기존 `ExchangeRate` parser로 처리하고 `rate`는 `Decimal`로 유지합니다.
- 실제 응답 전체, Authorization header, token, credential은 출력하거나 저장하지 않습니다.
- 보고 가능한 항목은 HTTP status, 통화 코드, rate 존재 여부, validity field 존재 여부뿐입니다.
- 다른 read-only, 시세, 계좌, 자산, 잔고, 체결, 주문 endpoint는 호출하지 않습니다.
- 실패 진단은 `config_validation`, `oauth_token`, `safety_gate`,
  `readonly_exchange_rate`, `response_parse`, `unknown` phase로 구분합니다.
- 진단에는 HTTP status와 고정된 safe error summary만 보존하며 raw request/response는
  포함하지 않습니다.
- 최초 live 시도는 실패했으며 진단 보강 중 추가 live 재시도는 수행하지 않았습니다.

### MS-05.07 exchange-rate schema 재정렬

- 실제 API와 OAuth endpoint를 호출하지 않고 공식 OpenAPI JSON만 정적으로 확인했습니다.
- `operationId`: `getExchangeRate`
- Security: OAuth2 Client Credentials
- required query: `baseCurrency`, `quoteCurrency`
- optional query: `dateTime`
- 공식 Currency enum: `KRW`, `USD`
- 동일한 기준/표시 통화와 enum 밖 통화는 request 생성 전에 차단합니다.
- 다음 live retry용 고정 통화쌍은 `USD` → `KRW`로 준비하되 이번 단계에서는
  live smoke를 실행하지 않습니다.

## 4. Stock Info

| Operation | Method | Path | 주요 parameter | 공식 response 요약 | 현재 상태 |
|---|---|---|---|---|---|
| getStocks | GET | `/api/v1/stocks` | required `symbols`, comma-separated 1~200 | `result` array; 공식 StockInfo 필드 전체 | Request validation, full parser, safe error metadata 정렬 완료 |
| getStockWarnings | GET | `/api/v1/stocks/{symbol}/warnings` | required path `symbol` | `result` array; `warningType`, optional `exchange`, `startDate`, `endDate`; 경고 없음은 empty array | Path validation, parser, safe error metadata 정렬 완료 |

재검증 메모:

- OpenAPI 3.1.0, API version 1.1.5에서 두 endpoint의 operationId는 각각
  `getStocks`, `getStockWarnings`이며 OAuth2 인증이 필요합니다.
- 두 endpoint 모두 accountSeq를 요구하지 않는 read-only Stock Info API입니다.
- `getStocks.symbols`는 required이며 1~200개를 쉼표로 구분합니다. 개별 symbol은
  영문 대/소문자, 숫자, `.`, `-`만 허용합니다.
- warnings의 path `symbol`도 required이며 같은 문자 형식을 사용합니다.
- StockInfo parser는 required `symbol`, `name`, `englishName`, `isinCode`,
  `market`, `securityType`, `isCommonShare`, `status`, `currency`,
  `sharesOutstanding`와 optional 날짜, leverage, 국내시장 상세 필드를 반영합니다.
- `sharesOutstanding`와 `leverageFactor`는 Decimal로 처리합니다.
- 400 `invalid-request`, 404 `stock-not-found`, 429 `rate-limit-exceeded`,
  500 `internal-error`에서 requestId/code/message와 허용된 data hint만 추출합니다.
- 다음 live smoke 후보는 공식 예시 심볼을 사용한
  `GET /api/v1/stocks?symbols=005930` 단일 요청입니다. 실제 symbol과 호출 여부는
  다음 Micro Stage에서 재확인하고 별도 승인을 받아야 합니다.
- 이번 MS-05.09에서는 실제 API와 OAuth endpoint를 호출하지 않았습니다.

## 5. Market Data

| Operation | Method | Path | 주요 parameter | 공식 response 요약 | 현재 상태 |
|---|---|---|---|---|---|
| getOrderbook | GET | `/api/v1/orderbook` | `symbol` | `timestamp`, `currency`, `asks[]`, `bids[]`; level은 `price`, `volume` | Request definition 후보; parser/model 후속 |
| getPrices | GET | `/api/v1/prices` | required `symbols`, comma-separated 1~200 | `result` array; required `symbol`, `lastPrice`, `currency`; nullable `timestamp` | Official request validation, response parsing, and safe error metadata aligned in MS-05.12 |
| getTrades | GET | `/api/v1/trades` | `symbol`, optional `count` max 50 | `result` array; `price`, `volume`, `timestamp`, `currency` | Request definition 후보; parser/model 후속 |
| getPriceLimit | GET | `/api/v1/price-limits` | `symbol` | `timestamp`, `upperLimitPrice`, `lowerLimitPrice`, `currency` | Request definition 후보; parser/model 후속 |
| getCandles | GET | `/api/v1/candles` | required `symbol`, required `interval`, optional `count`, `before`, `adjusted` | `result` object; required `candles[]`, optional/nullable `nextBefore` | Official request validation, response parsing, and safe error metadata aligned in MS-05.14 |

재검증 메모:

- `getCandles`의 공식 response root는 배열이 아니라 object입니다.
- `candles[]` 내부에는 `timestamp`, `openPrice`, `highPrice`, `lowPrice`, `closePrice`, `volume` 등이 포함됩니다.
- MS-05.02에서 `CandlePage.candles`와 `CandlePage.next_before`로 공식 root를 보존하도록 정렬했습니다.

### MS-05.14 Candles schema preflight

- Official document version: OpenAPI 3.1.0 / API version 1.1.5
- `operationId`: `getCandles`
- Security: OAuth2 Client Credentials
- Account scope: not required; `accountSeq` and `X-Tossinvest-Account` are not used
- Query `symbol` is required and accepts letters, digits, `.`, `-`
- Query `interval` is required and accepts only `1m` or `1d`
- Query `count` is optional, defaults to 100, and accepts 1 to 200
- Query `before` is optional ISO 8601 date-time
- Query `adjusted` is optional boolean and defaults to true
- Response `result` is `CandlePageResponse` with required `candles` array and optional/nullable `nextBefore`
- Each candle requires `timestamp`, `openPrice`, `highPrice`, `lowPrice`,
  `closePrice`, `volume`, and `currency`
- Decimal fields are parsed as finite `Decimal`
- Safe Candles errors retain only `requestId`, `code`, `message`,
  `data.field`, `data.allowedValues`, and `data.constraint.min/max`
- Next live smoke candidate, subject to separate approval:
  `GET /api/v1/candles?symbol=005930&interval=1d&count=1&adjusted=true`
- MS-05.14 performs no OAuth or business API call and does not read `.env.local`
- timestamp/dateTime 표시와 numeric string 처리 정책은 모델별 후속 검증이 필요합니다.

### MS-05.12 Prices schema preflight

- Official document version: OpenAPI 3.1.0 / API version 1.1.5
- `operationId`: `getPrices`
- Security: OAuth2 Client Credentials
- Account scope: not required; `accountSeq` and `X-Tossinvest-Account` are not used
- Query `symbols` is required and accepts 1 to 200 comma-separated symbols
- Each symbol permits English letters, digits, `.`, and `-`
- Success `result` is an array of `PriceResponse`
- Required result fields are `symbol`, `lastPrice`, and `currency`
- `timestamp` may be missing or `null`
- `lastPrice` is parsed as `Decimal`
- Currency currently documents `KRW` and `USD`, while clients must tolerate future unknown values
- The 400 invalid batch-size example exposes only safe metadata:
  `requestId`, `code`, `message`, `data.field`, and `data.constraint.min/max`
- 404, 429, and 500 responses use the common safe error envelope
- No raw request or response body is retained
- The next proposed live smoke candidate is
  `GET /api/v1/prices?symbols=005930`, subject to separate user approval
- MS-05.12 performs no OAuth or business API call and does not read `.env.local`

## 6. Market Info / Exchange Rate

### `GET /api/v1/exchange-rate`

공식 재검증 결과:

- Auth required: Yes
- accountSeq required: No
- Query:
  - required `baseCurrency`
  - required `quoteCurrency`
  - optional `dateTime`
- Response result:
  - `baseCurrency`
  - `quoteCurrency`
  - `rate`
  - `midRate`
  - `basisPoint`
  - `rateChangeType`
  - `validFrom`
  - `validUntil`

MS-05.02 alignment 이력과 MS-05.07 정정:

- MS-05.02에서는 optional `dateTime`만 query로 구성한다고 기록했으나,
  MS-05.07의 공식 API version 1.1.5 재확인 결과 이는 잘못된 가정으로 정정합니다.
- request builder는 required `baseCurrency`, `quoteCurrency`와 optional `dateTime`을 구성합니다.
- parser는 `baseCurrency`, `quoteCurrency`, `rate`, `midRate`, `basisPoint`,
  `rateChangeType`, `validFrom`, `validUntil`을 처리합니다.
- 금융 숫자는 `Decimal`로 복원합니다.
- 기존 SQLite 저장 계층 호환을 위해 내부 필드 `exchange_rate`를 유지하고 공식 이름 `rate` property를 제공합니다.
- `mid_rate`, `basis_point`, `rate_change_type`은 기존 직접 생성/저장 호출의
  호환성을 위해 모델에서는 optional이지만 공식 응답 parsing 경로에서는 필수입니다.
- `valid_from`, `valid_until`은 optional field로 보존합니다.
- 400 error의 `requestId`, `code`, `message`, `data.field`,
  `data.allowedValues`만 별도 안전 모델로 추출하며 raw body는 저장하지 않습니다.

공식 error response:

- 400 `invalid-request`: unsupported currency, same currency
- 404 `exchange-rate-not-found`
- 429 `rate-limit-exceeded`
- 500 `internal-error`

MS-05.06의 HTTP 400 `invalid-request`는 request에서 required
`baseCurrency`/`quoteCurrency`가 누락된 것이 원인일 가능성이 높습니다.
OAuth 단계는 통과했으며 실제 환율 request 단계에서 400이 발생했습니다.
MS-05.07에서는 실제 API 호출과 OAuth token 발급을 수행하지 않았습니다.

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
