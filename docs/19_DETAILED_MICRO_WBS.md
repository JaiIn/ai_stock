# 19. 초세분화 WBS — Micro Stage 목록

이 문서는 `docs/12_WBS.md`의 Milestone을 더 작은 Micro Stage로 나눈 실행 순서다.

Codex는 기본적으로 **Micro Stage 1개만 수행한 뒤 사용자 명령을 기다린다.**

---

## Micro Stage ID 규칙

```text
MS-<Milestone 번호>.<순번>
```

예시:

- `MS-00.01` — 공식 문서 Source 확인
- `MS-02.03` — OAuth 토큰 Client mock 테스트
- `MS-05.04` — 모의 체결 로직 구현

각 Micro Stage 완료 파일명은 아래 형식을 따른다.

```text
reports/micro-stages/MS-02.03-oauth-token-client.md
```


---

## 공통 Git 완료 조건

모든 Micro Stage는 완료 시 아래 Git 절차를 수행한다.

1. `git status` 확인
2. `git diff --stat` 확인
3. 변경 범위가 해당 Micro Stage에 한정되는지 확인
4. 테스트 결과와 완료 체크리스트 작성
5. `reports/git/MS-xx.xx-<name>-commit-checklist.md` 작성
6. 민감정보 commit 대상 포함 여부 확인
7. Micro Stage 단위 commit 생성
8. push는 사용자 승인 후에만 수행

관련 문서:

- `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
- `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
- `templates/git_commit_checklist_template.md`

---

## M0 — 문서/스펙 확인

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-00.01 | 공식 Source 위치 확인 | references/source_links.md | 링크/버전 기록 확인 | 최신 문서 기준 확인 |
| MS-00.02 | 로컬 전용 Python 프로젝트 기본 구조 생성 | pyproject.toml, .gitignore, .env.example, src/, app/, tests/, scripts/, logs/, reports/ | `python -m compileall src tests`, package import | 로컬 전용 구조와 민감정보 제외 규칙 승인 |
| MS-00.03 | 로컬 설정/환경변수 및 민감정보 마스킹 구조 구현 | .env.example, pyproject.toml, src/ai_stock/config/, src/ai_stock/utils/, tests/ | 설정 로딩, 마스킹, compileall, pytest | mock 기본값과 민감정보 비노출 승인 |
| MS-00.04 | 로컬 테스트/로그/리포트 기본 실행 체계 정리 | scripts/dev_check.py, docs/10_TEST_EXECUTION_AND_LOGGING.md, README.md, reports/ | compileall, unittest, pytest, `git diff --check`, dev_check | 반복 실행 명령과 PASS/FAIL 기준 승인 |
| MS-00.05 | M0 통합 체크 | reports/stage-gates/M0-completion-checklist.md | 문서 완성도 확인 | M1 진행 승인 대기 |

---

## M1 — 프로젝트 초기화

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-01.00 | GitHub repository clone/remote 확인 | git remote, branch | remote URL 확인 | origin이 JaiIn/ai_stock인지 확인 |
| MS-01.01 | Toss API Client 공통 기반, 예외, 응답 처리 | src/ai_stock/clients/, src/ai_stock/models/, tests/, reports/ | fake/httpx mock 응답, 상태별 예외, live 차단, 민감정보 비노출 | 실제 네트워크/OAuth/주문 미구현 확인 |
| MS-01.02 | Toss OAuth Mock 인증 흐름 구현 | src/ai_stock/clients/, src/ai_stock/models/, tests/, reports/ | 요청/응답 모델, 메모리 토큰 저장, mock provider, live 차단 테스트 | 실제 OAuth HTTP 호출 및 민감정보 노출 없음 확인 |
| MS-01.03 | 인증 요청 컨텍스트 및 안전 헤더 조립 | src/ai_stock/clients/, tests/, reports/ | mock token 연결, Authorization/account 헤더, safe dump, 무전송 테스트 | 실제 API/OAuth 호출 및 민감정보 노출 없음 확인 |
| MS-01.04 | 설정 클래스 초안 | src/ai_stock/config/settings.py | settings unit test | 환경변수 이름 확인 |
| MS-01.05 | `.env.example` 작성 | .env.example | 민감값 placeholder 확인 | 사용자가 실제 값 입력 방식 확인 |
| MS-01.06 | 로깅 기본 구조 | src/ai_stock/core/logging.py | 로그 생성 테스트 | 로그 경로 확인 |
| MS-01.07 | Secret masking 유틸 | src/ai_stock/core/masking.py | masking unit test | 마스킹 규칙 승인 |
| MS-01.08 | Makefile/명령 스크립트 | Makefile | make test/lint 확인 | 실행 명령 확인 |
| MS-01.09 | M1 통합 체크 | reports/stage-gates/M1-completion-checklist.md | ruff/pytest 최소 통과 | M2 진행 승인 대기 |
| MS-01.10 | M1 Git commit 후보 작성 | reports/git/MS-01-git-checklist.md | git diff/secret check | push 여부 사용자 승인 대기 |

---

## M2 — Toss API Read-only Client

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-02.01 | Stock Info Client Mock 구조 구현 | src/ai_stock/clients/, src/ai_stock/models/, tests/, reports/ | getStocks/getStockWarnings 요청 정의, fake parsing, 무전송 테스트 | 실제 호출 없음 및 OpenAPI 응답 구조 재검증 필요 확인 |
| MS-02.02 | Market Data Client Mock 구조 구현 | src/ai_stock/clients/, src/ai_stock/models/, tests/, reports/ | 문서화된 요청 interface, price/candle fake parsing, 무전송 테스트 | 실제 호출 없음 및 미확정 schema 재검증 필요 확인 |
| MS-02.03 | Exchange Rate Client Mock 구조 구현 | src/ai_stock/clients/, src/ai_stock/models/, tests/, reports/ | getExchangeRate 요청 정의, Decimal fake parsing, 무전송 테스트 | 실제 호출 없음 및 응답 schema 재검증 필요 확인 |
| MS-02.04 | OAuth token 발급 mock client | src/ai_stock/toss_api/auth.py | mock token test | 실제 Client ID/Secret 필요 여부 보고 |
| MS-02.05 | Token cache/expiry 처리 | src/ai_stock/toss_api/token_store.py | expiry refresh test | 토큰 저장 위치 승인 |
| MS-02.06 | 공통 request wrapper | src/ai_stock/toss_api/request.py | 401/429 retry mock test | retry 횟수 확인 |
| MS-02.07 | 공통 에러 모델 | src/ai_stock/toss_api/errors.py | error mapping test | 에러 메시지 형식 확인 |
| MS-02.08 | Market Data endpoint 1개 구현 | src/ai_stock/toss_api/market_data.py | fixture parsing test | 관심 API부터 구현할지 확인 |
| MS-02.09 | Market Data 나머지 구현 | src/ai_stock/toss_api/market_data.py | contract fixture tests | 데이터 저장 여부 확인 |
| MS-02.10 | Stock Info 구현 | src/ai_stock/toss_api/stock_info.py | warnings parsing test | 매수 유의 종목 처리 확인 |
| MS-02.11 | Market Info 구현 | src/ai_stock/toss_api/market_info.py | exchange rate fixture test | 환율 사용 방식 확인 |
| MS-02.12 | Account 조회 구현 | src/ai_stock/toss_api/account.py | mock account test | 실제 accountSeq 입력 방식 대기 가능 |
| MS-02.13 | Asset/Holdings 조회 구현 | src/ai_stock/toss_api/asset.py | holdings fixture test | 보유 종목 화면 노출 방식 확인 |
| MS-02.14 | Order Info 조회 구현 | src/ai_stock/toss_api/order_info.py | buying power fixture test | 주문가능금액은 읽기 전용으로 표시 |
| MS-02.15 | 주문 Mutation Guard 구현 | src/ai_stock/toss_api/order_guard.py | real order blocked test | 실주문 금지 확인 |
| MS-02.16 | Order/Modify/Cancel mock wrapper | src/ai_stock/toss_api/order.py | `ALLOW_REAL_ORDER=false` 차단 test | 실제 호출 없음 확인 |
| MS-02.17 | Order History 조회 구현 | src/ai_stock/toss_api/order_history.py | order list fixture test | 과거 주문 조회 범위 확인 |
| MS-02.18 | Toss client 통합 mock 테스트 | tests/contract/ | pytest contract pass | live test 진행 여부 사용자 승인 대기 |
| MS-02.19 | Read-only Live API 준비 점검 | reports/user-requests/ | no command unless approved | 실제 토큰/accountSeq 필요 시 대기 |
| MS-02.20 | M2 통합 체크 | reports/stage-gates/M2-completion-checklist.md | mock test 전체 통과 | M3 진행 승인 대기 |

주의:

- `MS-02.19`는 실제 API 호출을 수행하지 않는다. 사용자 입력과 승인 여부만 확인한다.
- Live API 테스트는 별도 사용자 명령이 있을 때만 수행한다.

---

## M3 — DB/Repository

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-03.01 | 로컬 SQLite 저장소 기반 구조 | src/ai_stock/repositories/, tests/, reports/ | sqlite3 schema, 임시 DB repository CRUD, Decimal TEXT, 무전송 테스트 | 기본 경로와 금지 테이블·민감정보 미저장 확인 |
| MS-03.02 | 로컬 데이터 저장 서비스 계층 | src/ai_stock/services/, src/ai_stock/repositories/, tests/, reports/ | 이미 파싱된 StockInfo/PriceSnapshot/Candle/ExchangeRate 모델을 repository에 저장하는 in-memory SQLite 통합 테스트 | 실제 API 호출·실제 DB 파일·민감정보 저장 없음 확인 |
| MS-03.03 | 로컬 Mock Ingestion Pipeline | src/ai_stock/services/, tests/, reports/ | fake payload를 기존 모델로 parsing 후 LocalDataPersistenceService를 통해 in-memory SQLite에 저장하는 통합 테스트 | 실제 API 호출·실제 DB 파일·민감정보 저장 없음 확인 |
| MS-03.04 | Market Snapshot 모델 | src/ai_stock/db/models/market.py | insert/select test | 저장 주기 확인 |
| MS-03.05 | Candle 모델 | src/ai_stock/db/models/candle.py | unique key test | timeframe 저장 방식 확인 |
| MS-03.06 | Stock Info Cache 모델 | src/ai_stock/db/models/stock_info.py | cache upsert test | 캐시 만료 정책 확인 |
| MS-03.07 | Account Snapshot 모델 | src/ai_stock/db/models/account.py | sensitive masking test | 계좌 식별값 저장 방식 확인 |
| MS-03.08 | Holdings Snapshot 모델 | src/ai_stock/db/models/holding.py | holdings insert test | 평가금액 표시 방식 확인 |
| MS-03.09 | Paper Portfolio 모델 | src/ai_stock/db/models/paper_portfolio.py | create portfolio test | 초기 자본 확인 필요 가능 |
| MS-03.10 | Paper Order 모델 | src/ai_stock/db/models/paper_order.py | order create test | 주문 상태값 확인 |
| MS-03.11 | Paper Position 모델 | src/ai_stock/db/models/paper_position.py | avg price test | Decimal 계산 확인 |
| MS-03.12 | Recommendation Run 모델 | src/ai_stock/db/models/recommendation.py | insert result test | 추천 이력 보존 기간 확인 |
| MS-03.13 | Repository skeleton | src/ai_stock/repositories/ | CRUD unit tests | repository 범위 확인 |
| MS-03.14 | DB 초기화 명령 | scripts/init_db.py | init run test | 기존 DB 있을 때 처리 승인 |
| MS-03.15 | M3 통합 체크 | reports/stage-gates/M3-completion-checklist.md | DB tests pass | M4 진행 승인 대기 |

---

## M4 — Market Data Pipeline

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-04.01 | 모의투자 도메인 모델과 safety guard | src/ai_stock/paper_trading/, src/ai_stock/risk/, tests/, reports/ | PaperPortfolio/PaperHolding/PaperOrder/PaperTrade 검증, paper-only safety guard 테스트 | 실제 주문/API/httpx/OAuth/accountSeq/DB 저장소 미구현 확인 |
| MS-04.02 | 모의투자 주문 검증 서비스 | src/ai_stock/paper_trading/, src/ai_stock/risk/, tests/, reports/ | PaperOrder가 PaperPortfolio 기준으로 유효한지 검증, buy/sell/status/live flag 테스트 | 포트폴리오 변경·실제 주문/API/httpx/OAuth/accountSeq/DB 저장소 미구현 확인 |
| MS-04.03 | 모의투자 체결 서비스 | src/ai_stock/paper_trading/, tests/, reports/ | 검증된 PaperOrder를 명시적 simulated execution price로 체결, buy/sell/status/live flag 테스트 | 실제 주문/API/httpx/OAuth/accountSeq/DB 저장소 미구현 확인 |
| MS-04.04 | 모의투자 포트폴리오 평가 서비스 | src/ai_stock/paper_trading/, tests/, reports/ | PaperPortfolio와 명시적 simulated current price map으로 평가, cash-only/single/multiple/missing price/live flag 테스트 | 실제 가격 조회/API/httpx/OAuth/accountSeq/DB 저장소 미구현 확인 |
| MS-04.05 | 환율/시장 정보 service | src/ai_stock/services/market_info_service.py | fixture test | 국내/미국 구분 확인 |
| MS-04.06 | Snapshot 저장 job | src/ai_stock/jobs/snapshot_job.py | job dry run | 자동 실행 여부 확인 |
| MS-04.07 | M4 통합 체크 | reports/stage-gates/M4-completion-checklist.md | service tests pass | M5 진행 승인 대기 |

---

## M5 — AI 추천 엔진

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-05.01 | Toss OpenAPI schema 재검증 및 endpoint matrix 정리 | docs/02_TOSS_OPEN_API_REFERENCE.md, references/endpoint_matrix.md, reports/MS-05.01_toss_openapi_schema_recheck_report.md | 공식 OpenAPI read-only 확인, mock client 가정과 schema 차이 문서화, src/tests/pyproject.toml 변경 없음 검증 | MS-05.02 이후 code alignment 범위 승인 |
| MS-05.02 | Toss read-only schema alignment (`getExchangeRate`, `getCandles`) | src/ai_stock/clients/, src/ai_stock/models/, tests/, docs/, references/, reports/ | optional `dateTime` request, 공식 환율 field Decimal parsing, candle object root/`nextBefore` parsing, 전체 회귀 테스트 | 실제 API/OAuth 호출 없음과 mock schema 정렬 결과 승인 |
| MS-05.03 | Live API Safety Gate 및 endpoint allowlist/denylist 구현 | src/ai_stock/risk/, tests/, docs/, references/, reports/ | metadata-only decision, read-only dry-run 허용, order/write/account/unknown 차단, no-network 테스트 | 실제 API/OAuth/credential 미사용과 fail-closed 정책 승인 |
| MS-05.04 | OAuth token live smoke test 준비 및 제한 실행 | src/ai_stock/clients/, scripts/, tests/, docs/, references/, reports/ | form request mock contract, token masking, safety flag 차단, credential 존재 시 OAuth endpoint 단일 live smoke | credential 로컬 입력 및 masked 결과 승인 |
| MS-05.05 | 최초 read-only live API smoke test (`getExchangeRate`) | src/ai_stock/clients/, scripts/, tests/, docs/, references/, reports/ | OAuth→Safety Gate→환율 GET fake flow, 응답 Decimal parsing, phase/status safe diagnostics, 실제 제한 smoke | 최초 실패 기록, 진단 보강 중 live 재시도 없음, 별도 재시도 승인 필요 |
| MS-05.06 | Exchange Rate live retry diagnostics | reports/MS-05.06_exchange_rate_live_retry_diagnostics_report.md, references/endpoint_matrix.md | 사전 전체 검증 후 OAuth 1회와 `GET /api/v1/exchange-rate` 1회만 실행, safe phase/status 기록 | `readonly_exchange_rate`, HTTP 400, `invalid-request` 결과와 추가 재시도 없음 확인 |
| MS-05.07 | Exchange Rate schema realignment | src/ai_stock/clients/market_info.py, src/ai_stock/clients/readonly_smoke.py, src/ai_stock/models/market_info.py, tests/, docs/, references/, reports/ | 공식 OpenAPI 정적 확인, required currency query, full response Decimal parsing, safe error schema fake tests | 실제 API/OAuth/.env.local 미사용과 HTTP 400 원인 정렬 확인 |
| MS-05.08 | Exchange Rate USD/KRW live retry | reports/MS-05.08_exchange_rate_usd_krw_live_retry_report.md, references/endpoint_matrix.md | 사전 전체 검증 후 OAuth 1회와 `GET /api/v1/exchange-rate?baseCurrency=USD&quoteCurrency=KRW` 1회만 실행, safe diagnostics 기록 | HTTP 200과 공식 응답 field parsing 성공, 추가 호출 없음 확인 |
| MS-05.09 | Stock Info read-only schema preflight | src/ai_stock/clients/stock_info.py, src/ai_stock/models/stock_info.py, src/ai_stock/risk/live_api.py, tests/, docs/, references/, reports/ | 공식 OpenAPI 정적 확인, symbols/path validation, full StockInfo Decimal parsing, safe error schema와 Safety Gate fake tests | 실제 API/OAuth/.env.local 미사용과 다음 단일 Stock Info live 후보 승인 대기 |
| MS-05.10 | Stock Info single-symbol live smoke | src/ai_stock/clients/stock_info_smoke.py, scripts/stock_info_smoke_test.py, tests/test_stock_info_live_smoke.py, reports/MS-05.10_stock_info_single_symbol_live_smoke_report.md, references/endpoint_matrix.md | fake transport 전체 flow 검증 후 OAuth 1회와 `GET /api/v1/stocks?symbols=005930` 1회만 실행, safe diagnostics 기록 | HTTP 200, 단일 result와 공식 StockInfo 주요 필드 parsing 성공, 추가 호출 없음 확인 |
| MS-05.11 | Stock Warnings single-symbol live smoke | src/ai_stock/clients/stock_warnings_smoke.py, scripts/stock_warnings_smoke_test.py, tests/test_stock_warnings_live_smoke.py, reports/MS-05.11_stock_warnings_single_symbol_live_smoke_report.md, references/endpoint_matrix.md | fake transport 전체 flow 검증 후 OAuth 1회와 `GET /api/v1/stocks/005930/warnings` 1회만 실행, safe diagnostics 기록 | HTTP 200과 정상 빈 warning 배열 parsing 성공, 추가 호출 없음 확인 |
| MS-05.12 | Prices read-only schema preflight | src/ai_stock/clients/market_data.py, src/ai_stock/models/market_data.py, tests/, docs/, references/, reports/ | Official OpenAPI static verification, required 1~200 symbols validation, nullable timestamp and Decimal price parsing, safe error metadata, Safety Gate tests | No API/OAuth/.env.local access; separate approval required for `GET /api/v1/prices?symbols=005930` live smoke |
| MS-05.14 | Candles read-only schema preflight | src/ai_stock/clients/market_data.py, src/ai_stock/models/market_data.py, tests/, docs/, references/, reports/ | Official OpenAPI static verification, required symbol/interval, optional count/before/adjusted validation, CandlePage parser, safe error metadata, Safety Gate tests | No API/OAuth/.env.local access; separate approval required for `GET /api/v1/candles?symbol=005930&interval=1d&count=1&adjusted=true` live smoke |
| MS-05.15 | Candles single-symbol live smoke | scripts/candles_smoke_test.py, src/ai_stock/clients/candles_smoke.py, tests/test_candles_live_smoke.py, references/, reports/ | Exactly one OAuth token request and one `GET /api/v1/candles?symbol=005930&interval=1d&count=1&adjusted=true` request succeeded with HTTP 200 and safe diagnostics | No retry loop; no `before`; no Prices/Stocks/Warnings/order/account endpoints; credentials, token, Authorization header, and raw response body are not stored |
| MS-06.01 | Read-only snapshot ingestion service foundation | src/ai_stock/services/readonly_snapshot_ingestion.py, tests/test_readonly_snapshot_ingestion_service.py, reports/ | Dependency-injected fake/mock providers persist parsed StockInfo, PriceSnapshot, CandlePage/Candle, and ExchangeRate through LocalDataPersistenceService using in-memory SQLite tests | No live client/OAuth/.env.local/accountSeq; StockWarnings persistence deferred because no dedicated local repository/schema exists |
| MS-06.02 | Fake read-only snapshot ingestion E2E smoke | scripts/readonly_snapshot_ingestion_smoke.py, tests/test_readonly_snapshot_ingestion_e2e_smoke.py, reports/ | Fixed fake providers run ReadOnlySnapshotIngestionService end-to-end against in-memory SQLite; repository round-trip preserves one StockInfo, PriceSnapshot, Candle, and ExchangeRate with Decimal/timestamp values | Not a live ingestion; no API/OAuth/.env.local/accountSeq/order call or real DB file; StockWarnings persistence remains deferred |
| MS-06.03 | Live read-only snapshot ingestion preflight | src/ai_stock/services/readonly_snapshot_ingestion_preflight.py, tests/test_live_readonly_snapshot_ingestion_preflight.py, reports/ | Dry-run plan fixes one future OAuth call plus four read-only business calls, in-memory SQLite target, StockWarnings exclusion, and Safety Gate metadata evaluation | No API/OAuth/.env.local/database access in preflight; next live stage requires separate approval and must not exceed five total calls |
| MS-06.04 | Live read-only snapshot ingestion smoke | scripts/live_readonly_snapshot_ingestion_smoke.py, src/ai_stock/services/live_readonly_snapshot_ingestion_smoke.py, tests/test_live_readonly_snapshot_ingestion_smoke.py, reports/ | Exactly one OAuth call plus Stocks, Prices, Candles, and Exchange Rate calls succeeded with HTTP 200; official models were persisted and round-tripped once through in-memory SQLite | Five-call strict ledger, no retry, no StockWarnings/account/order calls, no credential/token/raw-body storage, and no DB file |
| MS-06.05 | Local snapshot SQLite DB file preflight | src/ai_stock/storage/local_snapshot_db_preflight.py, tests/test_local_snapshot_db_preflight.py, reports/ | Immutable no-I/O plan fixes `data/local/ai_stock.sqlite3`, disabled creation/schema/repository flags, required Git ignore patterns, and caller-supplied validation observations | No DB directory/file, API/OAuth/live smoke/.env.local/accountSeq/order operation; exact `data/` ignore rule remains a blocking prerequisite before any file DB stage |
| MS-06.06 | Local snapshot DB Git ignore hardening | .gitignore, tests/test_local_snapshot_db_preflight.py, reports/ | Adds exact `data/` protection while retaining global `*.sqlite`, `*.sqlite3`, and `*.db` rules; reruns MS-06.05 validator against repository ignore patterns | Ignore policy now passes, but DB/data creation and API/OAuth/live smoke/.env.local/accountSeq/order operations remain disabled |

---

## M6 — 모의투자 엔진

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-06.01 | 모의 계좌 초기화 | src/ai_stock/paper_trading/account.py | initial cash test | 초기 자본 입력 필요 가능 |
| MS-06.02 | 모의 주문 생성 | src/ai_stock/paper_trading/order_service.py | create order test | 주문 입력 UI 방향 확인 |
| MS-06.03 | 시장가 체결 시뮬레이션 | src/ai_stock/paper_trading/fill_engine.py | market fill test | 체결 가격 가정 확인 |
| MS-06.04 | 지정가 체결 시뮬레이션 | src/ai_stock/paper_trading/fill_engine.py | limit fill test | 미체결 처리 확인 |
| MS-06.05 | 포지션 업데이트 | src/ai_stock/paper_trading/position_service.py | avg cost/PnL test | Decimal 검증 |
| MS-06.06 | 수수료/세금 모델 | src/ai_stock/paper_trading/fee_model.py | fee calculation test | 수수료/세금 가정 사용자 확인 |
| MS-06.07 | 성과 리포트 | src/ai_stock/paper_trading/performance.py | return/MDD test | 성과 지표 확인 |
| MS-06.08 | 실제 주문 API와 격리 테스트 | tests/safety/ | no external mutation test | 실계좌 영향 없음 확인 |
| MS-06.09 | M6 통합 체크 | reports/stage-gates/M6-completion-checklist.md | paper tests pass | M7 진행 승인 대기 |

---

## M7 — UI

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-07.01 | Streamlit shell | app.py | app import test | UI 방식 확인 |
| MS-07.02 | Sidebar/settings 화면 | src/ai_stock/ui/settings_page.py | render smoke test | 민감값 표시 금지 확인 |
| MS-07.03 | 관심종목 화면 | src/ai_stock/ui/watchlist_page.py | service mock test | 입력 UX 확인 |
| MS-07.04 | 시세 화면 | src/ai_stock/ui/market_page.py | mock render test | 표시 컬럼 확인 |
| MS-07.05 | 추천 화면 | src/ai_stock/ui/recommendation_page.py | fake result render | 추천 문구 확인 |
| MS-07.06 | 모의투자 주문 화면 | src/ai_stock/ui/paper_order_page.py | order form test | 실주문과 구분 확인 |
| MS-07.07 | 포트폴리오 화면 | src/ai_stock/ui/portfolio_page.py | render test | 수익률 표시 방식 확인 |
| MS-07.08 | 로그/리포트 화면 | src/ai_stock/ui/reports_page.py | file read test | 민감정보 마스킹 확인 |
| MS-07.09 | UI 수동 실행 점검 | reports/test-results/ | manual run report | 사용자 화면 확인 요청 |
| MS-07.10 | M7 통합 체크 | reports/stage-gates/M7-completion-checklist.md | UI smoke pass | M8 진행 승인 대기 |

---

## M8 — 품질, 문서, 패키징

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-08.01 | ruff 전체 정리 | src/, tests/ | ruff check pass | 스타일 변경 확인 |
| MS-08.02 | pytest 전체 실행 | tests/ | pytest pass | 실패/skip 확인 |
| MS-08.03 | coverage 요약 | reports/test-results/ | coverage report | 부족 영역 확인 |
| MS-08.04 | README 실행 가이드 갱신 | README.md | 명령 재검토 | 사용자가 따라할 수 있는지 확인 |
| MS-08.05 | 에러/운영 가이드 갱신 | docs/ | 문서 리뷰 | 운영 주의사항 확인 |
| MS-08.06 | 샘플 데이터/fixture 정리 | tests/fixtures/ | fixture load test | 실제 데이터 포함 금지 확인 |
| MS-08.07 | 최종 구현 리포트 | reports/implementation/ | 파일 존재 확인 | v0.1 완료 승인 대기 |
| MS-08.08 | M8 통합 체크 | reports/stage-gates/M8-completion-checklist.md | final checks pass | 최종본 승인 대기 |

---

## Live API 검증 — 별도 승인 단계

Live API 검증은 기본 WBS에 자동 포함하지 않는다. 사용자가 명시적으로 요청할 때만 아래 순서로 진행한다.

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| LIVE-01 | 인증 정보 입력 안내 | reports/user-requests/ | 입력 요청 문서 생성 | Client ID/Secret 직접 입력 대기 |
| LIVE-02 | OAuth token 발급 1회 테스트 | reports/test-results/ | 토큰 원문 미출력 확인 | 성공/실패 보고 후 대기 |
| LIVE-03 | 계좌 목록 조회 1회 테스트 | reports/test-results/ | accountSeq 마스킹 확인 | 사용할 계좌 선택 대기 |
| LIVE-04 | Read-only 시세 조회 1회 테스트 | reports/test-results/ | 호출 결과 마스킹 확인 | 호출 범위 확대 승인 대기 |
| LIVE-05 | 보유/주문가능 정보 조회 1회 테스트 | reports/test-results/ | 민감정보 마스킹 확인 | 이후 사용 여부 승인 대기 |

금지:

- Live 단계에서도 주문 생성/정정/취소 API는 호출하지 않는다.
- 실주문 활성화는 v0.1 범위를 벗어난다.

---

## Codex 수행 단위 제한

기본 제한:

```text
사용자 명령 1회 = Micro Stage 1개 수행
```

예외:

사용자가 명시적으로 `M1에서 3개까지 묶어서 진행`처럼 지시한 경우 최대 3개까지 수행할 수 있다. 단, 다음 상황에서는 즉시 중단한다.

- 인증 정보 필요
- live API 호출 필요
- DB 파괴적 변경 필요
- 실주문 관련 설정 변경 필요
- 테스트 실패
- 스펙 불일치 발견
