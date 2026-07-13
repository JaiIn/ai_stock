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
| Market Data | getPrices | GET | `/api/v1/prices` | Yes | No | Yes | MS-05.13 live smoke succeeded for one symbol | Required 1~200 symbol validation, official PriceResponse parser, safe error metadata, and single-symbol smoke path implemented | High | Required `symbols`; symbol characters are letters, digits, `.`, `-`; nullable timestamp; Decimal lastPrice; `symbols=005930` live smoke succeeded once in MS-05.13 without raw response/token/header storage | Official OpenAPI 1.1.5 `/api/v1/prices` |
| Market Data | getTrades | GET | `/api/v1/trades` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Query `symbol`; optional `count` max 50; result is recent trade array | Official OpenAPI `/api/v1/trades` |
| Market Data | getPriceLimit | GET | `/api/v1/price-limits` | Yes | No | Yes | Candidate read-only support | Request definition exists; parser/model not fully implemented | Medium | Result includes timestamp, upperLimitPrice, lowerLimitPrice, currency; US limit fields can be null | Official OpenAPI `/api/v1/price-limits` |
| Market Data | getCandles | GET | `/api/v1/candles` | Yes | No | Yes | MS-05.15 single-symbol live smoke succeeded | Required symbol/interval validation, optional count/before/adjusted handling, official CandlePage parser, safe error metadata, and dedicated safe live smoke path implemented | High | Live query `symbol=005930&interval=1d&count=1&adjusted=true` returned HTTP 200 with 1 parsed candle; `before` was not used; no Prices/Stocks/Warnings/order/account endpoints were called | Official OpenAPI 1.1.5 `/api/v1/candles` |
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

## MS-06.01 Persistence Readiness

| Stage | Scope | Persisted read-only data | Deferred data | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.01 | Read-only snapshot ingestion foundation | StockInfo, PriceSnapshot, Candle/CandlePage, ExchangeRate | StockWarnings | Fake/mock providers only; in-memory SQLite tests only; no live client, OAuth, `.env.local`, accountSeq, or real DB file |

## MS-06.02 Fake Ingestion E2E Status

| Stage | Scope | Stored counts | Round-trip checks | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.02 | Fake read-only snapshot ingestion E2E smoke | StockInfo 1, PriceSnapshot 1, Candle 1, ExchangeRate 1 | Repository counts, Decimal values, and timestamp values preserved; StockWarnings deferred | `actual_network_call_performed=false`, `oauth_token_endpoint_called=false`, `actual_db_file_created=false`; in-memory SQLite and fake providers only |

## MS-06.03 Live Ingestion Preflight

| Stage | Future approved call plan | Persistence plan | Scope exclusions | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.03 | OAuth token 1 call; Stocks, Prices, Candles, Exchange Rate 1 call each; expected total 5 | `create_connection(":memory:")`; StockInfo, PriceSnapshot, Candle/CandlePage, ExchangeRate only | StockWarnings, account/assets/balance/fills/order/write/mutation endpoints | Metadata-only dry run; four business endpoints are read-only, authenticated, and account-free; no API/OAuth/storage operation is performed in this stage |

## MS-06.04 Live Ingestion Smoke Result

| Stage | Actual call result | Persisted counts | Round-trip result | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.04 | OAuth 1 + business GET 4 = total 5; all HTTP 200 | StockInfo 1, PriceSnapshot 1, Candle 1, ExchangeRate 1 | Repository counts, Decimal, timestamp, currency, and OHLCV verified | In-memory SQLite only; StockWarnings deferred; no retry, accountSeq, order/account endpoint, raw response storage, or DB file |

## MS-06.05 Local Snapshot DB File Preflight

| Stage | Planned local target | Required ignore policy | Current readiness | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.05 | `data/local/ai_stock.sqlite3` | `data/`, `*.sqlite`, `*.sqlite3`, `*.db` | File creation remains disabled; global SQLite extension rules exist, but exact `.gitignore` `data/` rule must be added under separate approval before a file DB stage | Metadata-only immutable plan; no DB/API/OAuth/live smoke/env/accountSeq/order operation and `actual_db_file_created=false` |

## MS-06.06 Local Snapshot DB Git Ignore Hardening

| Stage | Ignore hardening | Preflight revalidation | File DB state | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.06 | Exact `data/` plus global `*.sqlite`, `*.sqlite3`, `*.db` rules are present | Repository patterns satisfy MS-06.05 requirements with no missing patterns and a valid preflight contract | `data/` and DB files remain absent; `db_file_creation_allowed_this_stage=false`, `actual_db_file_created=false` | No API/OAuth/live smoke/env/accountSeq/order operation; actual file DB creation still requires a separate stage |

## MS-06.07 Fake Snapshot Local DB File Smoke

| Stage | Local target | Stored and reopened | Git state | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.07 | `data/local/ai_stock.sqlite3` | StockInfo 1, PriceSnapshot 1, Candle 1, ExchangeRate 1; Decimal, timestamp, currency, and OHLCV preserved | DB file and `data/` are untracked; target is ignored by Git | Fake providers only; StockWarnings deferred; no API/OAuth/live smoke/env/accountSeq/order operation |

## MS-06.08 Live Snapshot Local DB File Preflight

| Stage | Future call plan | Existing DB and write policy | Persist/verify policy | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.08 | OAuth token 1; Stocks, Prices, Candles, Exchange Rate GET 1 each; expected total 5 | Keep `data/local/ai_stock.sqlite3`; no delete/overwrite; idempotent schema required | StockInfo upsert; PriceSnapshot/Candle/ExchangeRate insert; repository count delta or minimum presence plus timestamp summary | Metadata-only no-I/O plan; current-stage DB write/API/OAuth/live smoke/env/accountSeq/order disabled; StockWarnings deferred and DB/data stay untracked |

## MS-06.09 Live Snapshot Local DB File Smoke

| Stage | Actual call result | Repository counts before → after | File result | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.09 | OAuth 1 + Stocks/Prices/Candles/Exchange Rate GET 1 each; total 5; all HTTP 200 | stocks 1→1; price snapshots 1→2; candles 1→2; exchange rates 1→2 | Existing `data/local/ai_stock.sqlite3` modified in place; size 45056→45056; Git ignored/untracked | StockWarnings deferred; no retry, before, account/order call, credential/token/header/raw-body storage, delete, or overwrite |

## MS-06.10 Local Snapshot DB Read-Only Audit

| Stage | Network scope | DB access | Safe observed state | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.10 | None | Existing `data/local/ai_stock.sqlite3` opened with SQLite URI `mode=ro` and `query_only`; aggregate SELECTs only | stocks 1, price snapshots 2, candles 2, exchange rates 2; symbol `005930` and pair `USD/KRW` present | Minimum-count validation passed; StockWarnings deferred; no API/OAuth/smoke/env/accountSeq/order operation, row output, write SQL, schema initialization, DB modification, or Git tracking |

## MS-06.11 Local Snapshot Latest Read Model

| Stage | Network scope | Latest selection policy | Safe read model result | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.11 | None | Stock by symbol; price and 1d candle by timestamp then id descending; USD/KRW rate by date_time then id descending | Immutable DTO with Decimal-preserving summaries, source counts, and per-component completeness flags; current DB is complete | Existing DB opened with SQLite URI `mode=ro` and `query_only`; no API/OAuth/smoke/env/accountSeq/order operation, write SQL, schema initialization, raw-row output, or DB metadata change |

## MS-06.12 Latest Read Model Actual Local DB Smoke

| Stage | Network scope | Actual execution | Safe result | Safety note |
| --- | --- | --- | --- | --- |
| MS-06.12 | None | Existing latest read model CLI executed exactly once for `005930`, `USD/KRW`, and `data/local/ai_stock.sqlite3` | success; source counts stocks 1, price snapshots 2, candles 2, exchange rates 2; all completeness, timestamps, currencies, Decimal string conversion, and OHLCV checks pass | SQLite URI `mode=ro` plus `query_only`; file size/mtime unchanged; no API/OAuth/other smoke/env/accountSeq/order operation, raw-row output, secret output, code change, or Git tracking |

## MS-07.01 Read-Only Streamlit Snapshot Dashboard Preflight

| Stage | Network and storage scope | Planned data source | UI policy | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.01 | No network, OAuth, env, or DB I/O in this stage | `local_snapshot_latest_read_model` with future default `data/local/ai_stock.sqlite3`, symbol `005930`, pair `USD/KRW` | Immutable safe sections/fields and local read-only actions only; full Streamlit UI remains disabled | Live refresh, OAuth, DB write/migration/schema init, account/order data, order controls, AI recommendations, raw rows, and secret fields are denied |

## MS-07.02 Minimal Read-Only Streamlit Snapshot Dashboard

| Stage | Network scope | Storage and data source | Display scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.02 | None; no Toss API or OAuth execution | `local_snapshot_latest_read_model` only; default `data/local/ai_stock.sqlite3`, symbol `005930`, pair `USD/KRW`; SQLite URI `mode=ro` plus `query_only` | StockInfo, latest price, latest 1d candle, USD/KRW rate, completeness, source counts, file metadata, and read-only diagnostics | Missing DB is not created; no write/migration/schema init, env/credential access, account/order feature, AI recommendation, raw row, or secret field |

## MS-07.03 Read-Only Streamlit Dashboard Local Smoke

| Stage | Network scope | Execution result | Render result | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.03 | Localhost only; root HTTP 200 and `/_stcore/health` 200 `ok` | Existing Streamlit app started exactly once on port 8501 and was terminated after verification | AppTest reported no exceptions and rendered title, data source, `005930`, `USD/KRW`, four snapshot sections, all completeness flags, source counts 1/2/2/2, and read-only diagnostics | Browser manual check unavailable; no Toss API/OAuth/env/write/account/order/AI action, credential input, forbidden button, raw-row output, secret output, Git tracking, or DB metadata change |

## MS-07.04 Read-Only Dashboard Symbol/Pair Selector

| Stage | Network scope | Selector contract | Data access | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.04 | None; no localhost server, Toss API, or OAuth execution | Symbol is trimmed and blank falls back to `005930`; base/quote codes are trimmed, uppercased, and require exactly three ASCII letters; defaults remain `USD/KRW` | Only valid selectors are passed to `local_snapshot_latest_read_model`; invalid input returns `invalid_selector` before SQLite open; existing `mode=ro` and `query_only` policy remains | No env/credential input, live refresh, write/migration/schema init, account/order/AI action, raw-row output, secret output, Git tracking, or DB metadata change |

## MS-07.05 Read-Only Dashboard Selector Local Smoke

| Stage | Network scope | AppTest result | Selector result | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.05 | None; Streamlit server, HTTP, browser, Toss API, and OAuth are not executed | One AppTest session, five render runs, zero render exceptions; symbol/base/quote inputs, safe sections, completeness, source counts, and diagnostics render | Defaults `005930`/`USD`/`KRW`; lowercase pair normalizes; valid missing pair returns completeness warning; blank symbol falls back; invalid currency/symbol return safe validation warnings | Buttons, credential/accountSeq inputs, API/OAuth/order/account/AI controls are absent; SQLite remains `mode=ro` plus `query_only`; file size/mtime are unchanged and DB/data stay untracked |

## MS-07.06 Read-Only Dashboard Selector Server Smoke

| Stage | Network scope | Server and HTTP result | Selector render result | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.06 | Localhost only; one Streamlit launch on `127.0.0.1:8501`; no external, Toss API, or OAuth request | Root HTTP 200 and `/_stcore/health` HTTP 200/`ok`; server PID stopped; listener count 0 and health unreachable after stop | One auxiliary AppTest render reports zero exceptions, three selector inputs, defaults `005930`/`USD`/`KRW`, and zero buttons; safe sections remain covered by the existing source/test contract | SQLite remains `mode=ro` plus `query_only`; DB size/mtime are unchanged; no env/credential/account/order/AI control, raw-row output, secret output, Git tracking, or code change |

## MS-07.07 Read-Only Dashboard Local Runbook

| Stage | Runtime scope | Documented operation | Data and selector contract | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.07 | Documentation only; no Streamlit server, HTTP, AppTest, browser, Toss API, or OAuth execution | Local preflight, exact Streamlit command, `Ctrl+C` shutdown, listener cleanup, screen checklist, warnings, and troubleshooting | `local_snapshot_latest_read_model`; default DB `data/local/ai_stock.sqlite3`, symbol `005930`, pair `USD/KRW`; valid selectors reach only parameterized read-only queries; missing/partial data returns safe warnings | SQLite `mode=ro` plus `query_only`; no env/credential/accountSeq requirement, DB write/init/migration, account/order/AI control, raw-row/response output, secret output, Git tracking, or code change |

## MS-07.08 Read-Only Dashboard Final Checkpoint

| Stage | Runtime scope | Completed scope | Deferred or separately approved scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-07.08 | Documentation-only audit; no Streamlit server, HTTP, AppTest, browser, Toss API, OAuth, env, or DB execution | MS-07.01~07.07 preflight, minimal dashboard, local/server smoke evidence, symbol/pair selectors, validation, and local runbook; `local_snapshot_latest_read_model`, default DB `data/local/ai_stock.sqlite3`, symbol `005930`, pair `USD/KRW`, SQLite `mode=ro` plus `query_only` | Live API refresh, OAuth token issue, real account/asset/balance/fill access, real orders, real portfolio valuation, and live AI recommendations require separate stages and explicit approval | No code/runbook change, credential/accountSeq requirement, DB write/init/migration, account/order/AI control, raw-row/response output, secret output, Git tracking, or DB metadata change |

## MS-08.01 AI Recommendation Safety Preflight

| Stage | Endpoint scope | AI scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.01 | No endpoint use; no OAuth, Toss API, order, account, asset, balance, fill, or accountSeq request | No recommendation generation and no AI/LLM external API; both real and mock recommendation generation are disabled in this stage | OpenAI and Toss API keys, Toss secret, token, authorization header, and accountSeq are not required or used | Pure no-I/O policy only; no environment read, DB write, Streamlit change, live market refresh, account access, order execution, or real trade |

## MS-08.02 Mock-Only Recommendation Policy Model

| Stage | Endpoint scope | Input and model scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.02 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Deterministic pure policy model uses only caller-supplied mock/local snapshot summary flags; it performs no DB read, read-model call, API refresh, or external model call | OpenAI and Toss API keys, Toss secret, token, authorization header, and accountSeq are not required or used | Mock-only non-directive labels and explanation language; no DB write, environment read, Streamlit change, investment advice, direct buy/sell/hold directive, order execution, or real trade |

## MS-08.03 Recommendation Explanation UI Preflight

| Stage | Endpoint scope | Input and UI contract scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.03 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Deterministic pure no-I/O explanation UI contract uses only an already caller-supplied MS-08.02 mock result; it performs no DB read, read-model call, API refresh, mock recommendation recalculation, or Streamlit UI change | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Safe sections and forbidden sections are defined for a future panel only; no DB write, environment read, Streamlit app change, investment advice, direct buy/sell/hold directive, order execution, real trade, account data display, raw API response, or raw DB row display |

## MS-08.04 Mock-Only Recommendation Panel UI Integration

| Stage | Endpoint scope | Input and UI scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.04 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Streamlit UI display only; existing local read-only snapshot dashboard flow supplies safe summary fields, MS-08.02 builds a mock-only result, and MS-08.03 validates the display ViewModel before rendering | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Existing local read-only snapshot flow only; no DB write, environment read, API refresh, live refresh, real recommendation, investment advice, direct buy/sell/hold directive, order execution, real trade, account data display, raw API response, raw DB row display, or real order control |

## MS-08.05 Recommendation Panel AppTest Smoke

| Stage | Endpoint scope | Runtime scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.05 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Streamlit AppTest local render only; no Streamlit server, HTTP smoke, browser, live smoke, or fake smoke | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | AppTest verifies the MS-08.04 mock-only panel safe copy and forbidden control absence with no network/OAuth/LLM/env access and no DB write; existing local read-only snapshot flow remains display-only and app code is unchanged |

## MS-08.06 Recommendation Panel Server Smoke

| Stage | Endpoint scope | Runtime scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.06 | No external endpoint use; only `http://127.0.0.1:8501/` and `http://127.0.0.1:8501/_stcore/health` are allowed for the one local Streamlit server smoke | Streamlit server local headless smoke exactly once; root and health checks only; clean shutdown and port 8501 listener removal required; no manual browser, live smoke, or fake smoke | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | No OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, accountSeq request, external API refresh, DB write, environment file read, raw API response display, raw DB row display, real recommendation, direct buy/sell/hold directive, order execution, real trade, or app code change |

## MS-08.07 Recommendation Panel Final Checkpoint

| Stage | Endpoint scope | Runtime scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-08.07 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Documentation-only final checkpoint for MS-08.01 through MS-08.06; no Streamlit server, HTTP smoke, live smoke, fake smoke, manual browser, AppTest-only addition, or code execution beyond offline validation commands | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | No DB write, environment file read, raw API response display, raw DB row display, real recommendation, direct buy/sell/hold directive, order execution, real trade, app code change, test code change, or src code change |


## MS-09.00 Next Roadmap MS09-MS20 Planning

| Stage | Endpoint scope | Runtime scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.00 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Documentation-only roadmap insertion; no Streamlit server, HTTP smoke, live smoke, fake smoke, manual browser, API refresh, or DB write | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Final restart roadmap documentation only; no app, src, tests, README, pyproject, runbook, data, or .env.local change; no raw API response, raw DB row, real recommendation, direct buy/sell/hold directive, order execution, real trade, or real order button |

## MS-09.01 Candidate Input Contract Preflight

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.01 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O candidate input contract only; no DB read, DB write, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, UI change, scoring, watchlist storage, or actual recommendation generation | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Allowed sources are dashboard selector, local snapshot summary, manual watchlist, future watchlist file, and test fixture; forbidden sources include real account holdings/balance, order history, fills, live API refresh, OAuth/account scope, accountSeq source, raw API response, raw DB rows, and credential-based source |

## MS-09.02 Watchlist Data Model

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.02 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O watchlist data model only; no DB read, DB write, file read, file write, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, UI change, scoring, watchlist storage, file loader, or actual recommendation generation | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Watchlist items convert only to MS-09.01 candidate inputs; forbidden fields include real holdings, real balance, fills, order IDs, accountSeq, tokens, auth headers, API keys, secrets, scores, buy/sell/hold labels, target price, and expected return |

## MS-09.03 Manual/Local Watchlist Source

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.03 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O manual/local watchlist source adapter only; caller-supplied symbols and item dictionaries are normalized into MS-09.02 watchlists and MS-09.01 candidate inputs; no DB read, DB write, file read, file write, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, UI change, scoring, watchlist storage, file loader, or actual recommendation generation | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Forbidden source types include file paths, database tables/queries, Toss endpoints, OAuth scopes, accountSeq sources, real account holdings/balance/order/fill sources, raw API responses, raw DB rows, and credential-based sources; forbidden fields are reported only as safe diagnostics and are not copied into output models |

## MS-09.04 Watchlist Source Test Fixtures

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.04 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O watchlist source test fixtures only; deterministic in-memory fixture records reuse MS-09.01 candidate inputs, MS-09.02 watchlists, and MS-09.03 manual/local source adapter; no DB read, DB write, file read, file write, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, UI change, scoring, watchlist storage, fixture loader, file loader, or actual recommendation generation | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Fixture scenarios exclude real account holdings, balances, fills, Toss API responses, DB rows, file paths, credentials, tokens, accountSeq, recommendation scores, and buy/sell/hold action labels; forbidden fields are tested only for sanitization and diagnostics |

## MS-09.05 Manual Dashboard Preflight

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.05 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O dashboard preflight view model only; deterministic in-memory source and fixture results become display-ready rows, counts, warnings, diagnostics, badges, and next-action hints; no DB read, DB write, file read, file write, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, UI integration, dashboard selector, scoring, watchlist storage, fixture loader, file loader, or actual recommendation generation | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Dashboard rows and badges exclude real account/order/balance/holding/fill fields, credentials, tokens, accountSeq, recommendation scores, target price, expected return, and buy/sell/hold action labels; forbidden fields are surfaced only through safe warnings or diagnostics |

## MS-09.06 Manual Dashboard UI Integration

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.06 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Streamlit UI integration only for the MS-09.05 manual dashboard preflight view model; fixture/manual watchlist display uses in-memory builders; no Streamlit server, HTTP smoke, live smoke, fake smoke, browser, file read, file write, DB write, API refresh, scoring, watchlist storage, fixture loader, file loader, or actual recommendation generation; AppTest-based UI verification only | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Observation-only manual/watchlist preflight display; no real recommendation, buy/sell/hold judgment, order/account/asset/balance/fill implementation, real order button, OAuth login button, credential input, accountSeq input, file upload, raw API response, or raw DB row output |

## MS-09.07 Manual Dashboard AppTest Hardening

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-09.07 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Streamlit UI hardening only for the existing MS-09.06 manual dashboard preflight section; AppTest verifies fixture scenario coverage, safety copy, badges, warnings, rows, and forbidden control absence; no Streamlit server, HTTP smoke, live smoke, fake smoke, browser, file read, file write, new DB read implementation, DB write, API refresh, scoring, watchlist storage, fixture loader, file loader, or actual recommendation generation | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | AppTest-only checkpoint; observation-only manual/watchlist preflight remains non-directive with no real recommendation, buy/sell/hold judgment, order/account/asset/balance/fill implementation, real order button, API refresh button, OAuth login button, credential input, accountSeq input, file upload, raw API response, or raw DB row output |

## MS-10.00 Feature/Data Quality Model Preflight

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-10.00 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O feature/data quality contract only; deterministic in-memory MS-09 dashboard preflight and fixture outputs become quality records and assessments; no DB read, DB write, file read, file write, Streamlit UI change, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, scoring, ranking, recommendation, feature loader, watchlist loader, or watchlist storage | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Quality statuses express data usability and review need only; no score, rank, recommendation, buy/sell/hold action, target price, expected return, profit probability, account/order/balance/holding/fill field, raw API response, or raw DB row output |

## MS-10.01 Feature Quality Fixture Expansion

| Stage | Endpoint scope | Runtime and data scope | Credential scope | Safety note |
| --- | --- | --- | --- | --- |
| MS-10.01 | No endpoint use; no OAuth, Toss API, OpenAI/LLM API, order, account, asset, balance, fill, or accountSeq request | Pure no-I/O feature quality fixture expansion only; deterministic in-memory MS-09 fixtures and MS-10.00 quality assessments are compared to expected fixture records; no DB read, DB write, file read, file write, Streamlit UI change, Streamlit server, HTTP smoke, live smoke, fake smoke, browser, scoring, ranking, recommendation, feature loader, watchlist loader, fixture loader, or watchlist storage | OpenAI and Toss API keys, Toss secret, token, authorization header, credential input, and accountSeq are not required or used | Fixture scenarios cover data quality and review cases only; no score, rank, recommendation, buy/sell/hold action, target price, expected return, profit probability, account/order/balance/holding/fill fixture, raw API response, raw DB row, file path fixture, credential fixture, or token fixture |
