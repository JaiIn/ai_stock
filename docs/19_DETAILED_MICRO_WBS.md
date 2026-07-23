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
| MS-06.07 | Fake snapshot local SQLite file smoke | scripts/fake_snapshot_local_db_file_smoke.py, src/ai_stock/storage/local_snapshot_db_smoke.py, tests/test_fake_snapshot_local_db_file_smoke.py, reports/ | Runs fixed fake providers once against `data/local/ai_stock.sqlite3`, reopens the same file, and verifies one StockInfo, PriceSnapshot, Candle, and ExchangeRate with Decimal/timestamp preservation | DB file creation is approved only for this stage; target and `data/` remain Git-ignored/untracked, with no API/OAuth/live smoke/.env.local/accountSeq/order operation |
| MS-06.08 | Live snapshot local SQLite file preflight | src/ai_stock/storage/live_snapshot_local_db_preflight.py, tests/test_live_snapshot_local_db_preflight.py, reports/ | Immutable no-I/O plan fixes the future five-call read-only scope, existing-file coexistence, idempotent schema requirement, StockInfo upsert, snapshot inserts, and safe repository verification | Existing `data/local/ai_stock.sqlite3` is allowed but not modified; no API/OAuth/live smoke/.env.local/accountSeq/order operation, and DB/data remain Git-ignored/untracked |
| MS-06.09 | Live snapshot local SQLite file smoke | scripts/live_snapshot_local_db_file_smoke.py, src/ai_stock/storage/live_snapshot_local_db_smoke.py, tests/test_live_snapshot_local_db_file_smoke.py, reports/ | Executes exactly one OAuth plus four read-only GETs, then idempotently appends/upserts parsed models into the existing file DB and verifies counts/types | All five calls HTTP 200; stocks 1→1 and price/candle/rate 1→2; no retry, warnings/account/order call, secret/raw-body storage, DB overwrite, or Git tracking |
| MS-06.10 | Local snapshot SQLite DB read-only audit | scripts/local_snapshot_db_readonly_audit.py, src/ai_stock/storage/local_snapshot_db_audit.py, tests/test_local_snapshot_db_readonly_audit.py, reports/ | Opens the existing DB with SQLite URI `mode=ro`, enables `query_only`, and returns aggregate counts, safe timestamp ranges, and minimum-state checks | No schema initialization, write SQL, API/OAuth/smoke/env/accountSeq/order operation, row output, secret output, or DB metadata change; DB/data remain Git-ignored/untracked |
| MS-06.11 | Local snapshot latest read model | scripts/local_snapshot_latest_read_model.py, src/ai_stock/storage/local_snapshot_latest_read_model.py, tests/test_local_snapshot_latest_read_model.py, reports/ | Builds immutable StockInfo, latest PriceSnapshot, latest 1d Candle, latest USD/KRW ExchangeRate, source-count, and completeness DTOs using SQLite URI `mode=ro` and `query_only` | Decimal values remain Decimal internally and become strings only in safe JSON; partial data is explicit, with no write SQL, API/OAuth/smoke/env/accountSeq/order operation, row output, or DB metadata change |
| MS-06.12 | Latest read model actual local DB smoke | reports/MS-06.12_latest_read_model_local_db_smoke_report.md, docs/, references/ | Runs the existing latest read model CLI exactly once against `data/local/ai_stock.sqlite3`; source counts 1/2/2/2 and every completeness flag pass | Read-only URI and `query_only` preserve identical file size/mtime; no code change, API/OAuth/other smoke/env/accountSeq/order operation, raw-row output, secret output, or Git tracking |
| MS-07.01 | Read-only Streamlit snapshot dashboard preflight | src/ai_stock/ui/readonly_snapshot_dashboard_preflight.py, tests/test_readonly_streamlit_snapshot_dashboard_preflight.py, reports/ | Immutable no-I/O plan fixes the latest-read-model data source, safe sections/fields, local read-only actions, and denied live/write/order/AI actions | Full Streamlit UI remains deferred; no API/OAuth/smoke/env/DB access/accountSeq/order/AI operation, row or secret output, or DB metadata change |
| MS-07.02 | Minimal read-only Streamlit snapshot dashboard | app/streamlit_app.py, src/ai_stock/ui/readonly_snapshot_dashboard.py, tests/test_readonly_streamlit_snapshot_dashboard.py, reports/ | Thin Streamlit entrypoint renders a pure safe-view DTO built only through `local_snapshot_latest_read_model`; missing DB and partial data return safe UI messages | Existing SQLite URI `mode=ro` and `query_only` remain the only DB path; no API/OAuth/env/write/migration/schema/account/order/AI action, raw-row output, secret output, or DB metadata change |
| MS-07.03 | Read-only Streamlit dashboard local smoke | reports/MS-07.03_readonly_streamlit_dashboard_local_smoke_report.md, docs/, references/ | Starts the existing Streamlit app once on localhost, verifies HTTP 200 and health `ok`, then confirms title, snapshot sections, completeness, source counts, and diagnostics with Streamlit AppTest | Server is stopped after the smoke; browser manual check unavailable, no code change, API/OAuth/env/write/account/order/AI action, secret/raw-row output, or DB metadata change |
| MS-07.04 | Read-only dashboard symbol/pair selector | app/streamlit_app.py, src/ai_stock/ui/readonly_snapshot_dashboard.py, tests/test_readonly_streamlit_snapshot_dashboard.py, reports/ | Adds trimmed symbol and normalized three-letter base/quote inputs; valid selectors alone reach `local_snapshot_latest_read_model`, while invalid input returns a safe warning before DB open | Defaults remain `005930` and `USD/KRW`; no Streamlit server, API/OAuth/smoke/env/write/migration/schema/account/order/AI action, raw-row output, secret output, or DB metadata change |
| MS-07.05 | Read-only dashboard selector local smoke | reports/MS-07.05_readonly_dashboard_selector_local_smoke_report.md, docs/, references/ | One AppTest session performs five render runs for defaults, valid normalized pair, blank-symbol fallback, invalid currency, and invalid symbol; render exceptions and buttons remain zero | Streamlit server/HTTP/browser are not run; no code change, API/OAuth/env/write/migration/schema/account/order/AI action, secret/raw-row output, Git tracking, or DB metadata change |
| MS-07.06 | Read-only dashboard selector server smoke | reports/MS-07.06_readonly_dashboard_selector_server_smoke_report.md, docs/, references/ | Starts the selector-enabled Streamlit app exactly once, verifies localhost root/health HTTP 200, performs one AppTest auxiliary render, and then stops the server | Port listener and server PID are cleared; no code change, API/OAuth/env/write/account/order/AI action, secret/raw-row output, Git tracking, or DB metadata change |
| MS-07.07 | Read-only dashboard local runbook | docs/28_READONLY_DASHBOARD_RUNBOOK.md, reports/MS-07.07_readonly_dashboard_runbook_report.md, docs/, references/ | Documents local startup/shutdown, selector usage, visual checks, missing/partial DB behavior, troubleshooting, and pre/post safety checks | Documentation only; no server/AppTest/HTTP/browser execution, API/OAuth/env/DB write/account/order/AI action, code change, secret/raw-row output, or DB metadata change |
| MS-07.08 | Read-only dashboard final checkpoint | reports/MS-07.08_readonly_dashboard_final_checkpoint_report.md, docs/, references/ | Audits MS-07.01 through MS-07.07 artifacts and records completed preflight, dashboard, selectors, smoke evidence, runbook, supported scope, limitations, and next-stage boundaries | Documentation only; no code or runbook change, server/AppTest/HTTP/browser execution, API/OAuth/env/DB write/account/order/AI action, secret/raw-row output, or DB metadata change |

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
| MS-07.01 | Read-only snapshot dashboard preflight | src/ai_stock/ui/readonly_snapshot_dashboard_preflight.py, tests/test_readonly_streamlit_snapshot_dashboard_preflight.py | immutable no-I/O policy contract | Full UI 구현 전 sections/actions/sensitive-field 경계 확인 |
| MS-07.02 | Minimal read-only snapshot dashboard | app/streamlit_app.py, src/ai_stock/ui/readonly_snapshot_dashboard.py, tests/test_readonly_streamlit_snapshot_dashboard.py | pure helper tests, missing/partial DB safety, compileall/unittest/pytest/dev_check/ruff | local latest read model만 사용하고 API/OAuth/DB write/AI/주문 UI가 없음을 확인 |
| MS-07.03 | Read-only dashboard local smoke | reports/MS-07.03_readonly_streamlit_dashboard_local_smoke_report.md, docs/, references/ | localhost HTTP/health와 AppTest render 확인 후 서버 종료 | DB metadata 불변, 금지 action/input 부재, 브라우저 수동 확인 미수행 결과 확인 |
| MS-07.04 | Read-only dashboard symbol/pair selector | app/streamlit_app.py, src/ai_stock/ui/readonly_snapshot_dashboard.py, tests/test_readonly_streamlit_snapshot_dashboard.py | pure selector validation, parameter forwarding, invalid-input fail-safe, missing/partial DB safety, full offline regression | 기본값과 safe sections를 유지하고 API/OAuth/DB write/credential/AI/주문 UI가 없음을 확인 |
| MS-07.05 | Read-only dashboard selector local smoke | reports/MS-07.05_readonly_dashboard_selector_local_smoke_report.md, docs/, references/ | AppTest 기본/valid/invalid selector 5회 render와 전체 offline regression | 서버·HTTP·브라우저 없이 selector 렌더, safe warning, 금지 control 부재, DB metadata 불변 확인 |
| MS-07.06 | Read-only dashboard selector server smoke | reports/MS-07.06_readonly_dashboard_selector_server_smoke_report.md, docs/, references/ | Streamlit 서버 1회 기동, localhost root/health와 AppTest 보조 확인, 서버 종료 및 전체 offline regression | selector 기본값·금지 control 부재·DB metadata 불변·listener 0 확인 |
| MS-07.07 | Read-only dashboard local runbook | docs/28_READONLY_DASHBOARD_RUNBOOK.md, reports/MS-07.07_readonly_dashboard_runbook_report.md, docs/, references/ | 실행 전후 체크리스트, 실행·종료 명령, selector 사용, safe sections, troubleshooting 문서 검토와 전체 offline regression | 코드·서버·HTTP·AppTest 변경/실행 없이 local-only read-only 운영 절차와 민감정보 경계 확인 |
| MS-07.08 | Read-only dashboard final checkpoint | reports/MS-07.08_readonly_dashboard_final_checkpoint_report.md, docs/, references/ | MS-07.01~07.07 산출물, 지원·미지원 범위, 안전 정책, 다음 단계 경계 검토와 전체 offline regression | 코드·runbook·runtime 실행 없이 read-only dashboard 단계 완료 여부와 후속 AI preflight 후보를 확인 |
| MS-07.09 | UI 수동 실행 점검 | reports/test-results/ | manual run report | 사용자 화면 확인 요청 |
| MS-07.10 | M7 통합 체크 | reports/stage-gates/M7-completion-checklist.md | UI smoke pass | M8 진행 승인 대기 |

---

## M8 — 품질, 문서, 패키징

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-08.01 | AI recommendation safety preflight | src/ai_stock/recommendation/safety_preflight.py, tests/test_ai_recommendation_safety_preflight.py, reports/MS-08.01_ai_recommendation_safety_preflight_report.md, docs/, references/ | immutable no-I/O deny-by-default policy, disclaimer/language contract, MS-08.02 boundary, full offline regression | 실제 추천·mock 추천·LLM·외부 AI/Toss API·OAuth·credential·accountSeq·DB write·UI·실거래를 모두 금지하고 투자 조언이 아닌 안전 계약만 정의 |
| MS-08.02 | Mock-only recommendation policy model | src/ai_stock/recommendation/mock_policy_model.py, src/ai_stock/recommendation/\_\_init\_\_.py, tests/test_ai_recommendation_mock_policy_model.py, reports/MS-08.02_mock_only_recommendation_policy_model_report.md, docs/, references/ | Caller-supplied mock/local snapshot summary만 받는 frozen DTO, deterministic pure no-I/O builder/validator, MS-08.01 disclaimer·언어 정책 재사용, incomplete/risk/neutral 분기, 전체 offline regression | 실제 추천·투자 자문·직접 매수/매도/보유 지시·LLM/OpenAI/Toss API·OAuth·credential·accountSeq·DB write·Streamlit·계좌/주문 기능은 금지하며, 다음 단계는 별도 승인 후 MS-08.03 recommendation explanation UI preflight |
| MS-08.03 | Recommendation explanation UI preflight | src/ai_stock/recommendation/explanation_ui_preflight.py, src/ai_stock/recommendation/\_\_init\_\_.py, tests/test_ai_recommendation_explanation_ui_preflight.py, reports/MS-08.03_recommendation_explanation_ui_preflight_report.md, docs/, references/ | UI contract only=true인 deterministic pure no-I/O display ViewModel preflight. MS-08.02 caller-supplied mock result만 입력으로 받고 safe sections, forbidden sections, disclaimer, diagnostics, sensitive control deny flags를 검증 | 실제 Streamlit UI 연결, app/streamlit_app.py 수정, 실제 추천/투자 자문/buy/sell/hold directive/LLM/OpenAI/Toss API/OAuth/accountSeq/DB write/order/account/assets/balance/fills/실주문 버튼은 금지하며, 다음 단계는 별도 승인 후 MS-08.04 mock-only recommendation panel UI integration |
| MS-08.04 | Mock-only recommendation panel UI integration | app/streamlit_app.py, tests/test_ai_recommendation_panel_ui_integration.py, docs/19_DETAILED_MICRO_WBS.md, references/endpoint_matrix.md, reports/MS-08.04_mock_only_recommendation_panel_ui_integration_report.md | 기존 read-only Streamlit dashboard 아래에 MS-08.02 mock-only result와 MS-08.03 explanation ViewModel contract를 검증 후 표시한다. 표시 목적은 mock-only, observation-only, not investment advice, no real recommendation, no order/account/live/credential 상태 안내다. | 실제 추천, 투자 자문, buy/sell/hold 지시, live refresh, OAuth, credential/accountSeq 입력, order/account/assets/balance/fills, DB write 및 실주문 버튼은 계속 금지한다. 다음 단계는 별도 승인 후 MS-08.05 recommendation panel AppTest smoke 또는 server smoke |
| MS-08.05 | Recommendation panel AppTest smoke | tests/test_ai_recommendation_panel_apptest_smoke.py, docs/19_DETAILED_MICRO_WBS.md, references/endpoint_matrix.md, reports/MS-08.05_recommendation_panel_apptest_smoke_report.md | Streamlit AppTest local render only smoke. MS-08.04 mock-only panel copy, observation-only/not-investment-advice safety text, forbidden UI control absence, no network/OAuth/LLM/env/DB-write guard, and DB file mtime stability are verified without running a server | Streamlit server, HTTP smoke, live smoke, fake smoke, browser, actual API/OAuth/LLM, credential/accountSeq, order/account/assets/balance/fills, DB write, app code change, commit, and push remain forbidden. Next step is separately approved MS-08.06 recommendation panel server smoke |

### MS-08.04 상세 범위

- 목적: MS-08.02 mock-only recommendation policy model 결과를 MS-08.03 explanation UI preflight contract로 변환해 기존 read-only dashboard에 안전하게 표시한다.
- 허용 범위: `app/streamlit_app.py`의 Streamlit 표시, 새 AppTest/단위 테스트, WBS/endpoint matrix/report 갱신.
- 금지 범위: 실제 AI 추천, 투자 조언, 직접 buy/sell/hold 지시, 주문 버튼, 계좌/자산/잔고/체결 기능, credential/accountSeq 입력, live refresh, OAuth, Toss/OpenAI/LLM/API 호출, DB write, raw DB row/raw API response 출력.
- 산출물: mock-only explanation panel, `tests/test_ai_recommendation_panel_ui_integration.py`, MS-08.04 report, WBS 및 endpoint matrix 기록.
- 검증: compileall, unittest, pytest, `scripts/dev_check.py`, ruff, `git diff --check`, AppTest 기반 렌더 확인, forbidden control/string 부재 확인.
- 다음 단계: 별도 사용자 승인 후 MS-08.05 recommendation panel AppTest smoke 또는 MS-08.05 recommendation panel server smoke.

### MS-08.05 상세 범위

- 목적: MS-08.04 mock-only recommendation panel이 Streamlit AppTest 로컬 렌더에서 안전하게 표시되는지 smoke 검증한다.
- 허용 범위: `tests/test_ai_recommendation_panel_apptest_smoke.py`, WBS, endpoint matrix, MS-08.05 report 작성. AppTest local render only, no-network/no-credential/no-live-api/no-DB-write guard 사용.
- 금지 범위: `app/streamlit_app.py` 수정, Streamlit server 실행, HTTP smoke, live smoke, fake smoke, browser 실행, 실제 AI 추천, buy/sell/hold 지시, LLM/OpenAI/Toss API/OAuth 호출, credential/accountSeq 입력, 주문/계좌/자산/잔고/체결 기능, 실주문 버튼, DB write, raw DB row/raw API response 출력.
- 산출물: AppTest smoke 테스트, MS-08.05 report, WBS 및 endpoint matrix 기록.
- 검증: compileall, unittest, pytest, `scripts/dev_check.py`, ruff, `git diff --check`, `git status`, AppTest smoke 포함, `app/streamlit_app.py` 변경 없음, forbidden control/string 부재, `.env.local` 및 DB/data Git 미추적 확인.
- 다음 단계: 별도 사용자 승인 후 MS-08.06 recommendation panel server smoke.
| MS-08.06 | Recommendation panel server smoke | docs/19_DETAILED_MICRO_WBS.md, references/endpoint_matrix.md, reports/MS-08.06_recommendation_panel_server_smoke_report.md | Streamlit local headless server smoke exactly once; localhost root and health endpoint checks; clean shutdown and port listener removal; offline regression checks | External endpoints, live/fake smoke, manual browser, Toss/OAuth/OpenAI/LLM/API calls, credential/accountSeq, order/account/assets/balance/fills, DB write, app code change, commit, and push remain forbidden. Next step is separately approved MS-08.07 recommendation panel final checkpoint |

### MS-08.06 Detail Scope

- Purpose: verify the MS-08.04 mock-only recommendation panel in a local Streamlit server process after MS-08.05 AppTest coverage, focusing on server startup, localhost root/health responses, clean shutdown, and no remaining port listener.
- Allowed scope: `reports/MS-08.06_recommendation_panel_server_smoke_report.md`, WBS, and endpoint matrix updates. One local headless Streamlit server run bound to localhost, with `http://127.0.0.1:8501/` and `http://127.0.0.1:8501/_stcore/health` checks only.
- Forbidden scope: `app/streamlit_app.py` changes, external network endpoints, Toss API, OAuth token endpoint, OpenAI/LLM/API calls, live smoke, fake smoke, manual browser execution, credential or accountSeq usage, order/account/assets/balance/fills functionality, real recommendation or buy/sell/hold directive generation, DB write, raw DB row output, raw API response output, commit, and push.
- Deliverables: MS-08.06 server smoke report, WBS update, and endpoint matrix update.
- Verification: compileall, unittest, pytest, `scripts/dev_check.py`, ruff, `git diff --check`, `git status`, one Streamlit local server smoke, root 200, health 200/ok, fatal log pattern absence, server shutdown, port 8501 listener removal, `app/streamlit_app.py` unchanged, forbidden path unchanged checks, `.env.local` and DB/data Git untracked checks.
- Next step: separately approved MS-08.07 recommendation panel final checkpoint.

### MS-08.07 Detail Scope

- Purpose: summarize the completed MS-08.01 through MS-08.06 recommendation panel work, record supported scope, explicitly list unsupported scope, and propose next-stage candidates.
- Allowed scope: WBS update, endpoint matrix update, and `reports/MS-08.07_recommendation_panel_final_checkpoint_report.md`.
- Forbidden scope: `app/streamlit_app.py`, `tests/`, `src/`, `README.md`, `docs/28_READONLY_DASHBOARD_RUNBOOK.md`, `pyproject.toml`, `data/`, `.env.local`, Streamlit server execution, HTTP smoke, live smoke, fake smoke, browser execution, AI recommendation generation, buy/sell/hold directive generation, LLM/OpenAI/API calls, Toss API calls, OAuth token endpoint calls, credential/accountSeq use, DB write, raw DB row output, raw API response output, order/account/assets/balance/fills implementation, real order button, commit, and push.
- Deliverables: MS-08.07 final checkpoint report plus WBS and endpoint matrix entries.
- Verification: compileall, unittest, pytest, `scripts/dev_check.py`, ruff, `git diff --check`, `git status`, forbidden path unchanged checks, `.env.local` and DB/data Git untracked checks, and Git diff sensitive value scan.
- MS-08 completion criteria: MS-08.01 safety preflight, MS-08.02 deterministic mock-only policy model, MS-08.03 explanation UI contract, MS-08.04 read-only dashboard panel integration, MS-08.05 AppTest smoke, and MS-08.06 local server smoke records are present and retain the no-advice/no-order/no-credential/no-live-API boundaries.
- Next step candidates: MS-08.08 M8 integrated completion checklist, recommendation panel copy polish under the same mock-only policy, or a separately approved future stage for any real recommendation/LLM/live API capability.
| MS-08.07 | Recommendation panel final checkpoint | docs/19_DETAILED_MICRO_WBS.md, references/endpoint_matrix.md, reports/MS-08.07_recommendation_panel_final_checkpoint_report.md | MS-08.01~MS-08.06 산출물 요약, 지원/미지원 범위, 안전 경계, AppTest/server smoke 기록, 민감정보/DB/data 미추적 확인 | 별도 승인 후 커밋 대기 |
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

## MS-09.00: Next Roadmap MS09-MS20 Planning

### Purpose

Document the MS-09 through MS-20 restart roadmap after the MS-08 mock-only recommendation panel checkpoint, so the project can continue toward a local-only MVP with explicit safety, credential, DB-write, and no-real-order boundaries.

### Deliverables

```text
docs/29_AI_STOCK_NEXT_ROADMAP_MS09_MS20.md
reports/MS-09.00_next_roadmap_ms09_ms20_report.md
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
```

### Allowed Scope

- Add the MS-09 through MS-20 roadmap document.
- Record MS-09.00 in the WBS and endpoint matrix.
- Summarize stage-by-stage credential timing.
- Summarize stage-by-stage DB write timing.
- Keep the work documentation-only.

### Forbidden Scope

- No code implementation.
- No `src/`, `tests/`, `app/streamlit_app.py`, `README.md`, `pyproject.toml`, or read-only dashboard runbook changes.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, or browser execution.
- No Toss API, OAuth token endpoint, OpenAI/LLM/API model call, credential request, accountSeq request, DB write, raw DB row output, raw API response output, order/account/assets/balance/fills implementation, or real order button.

### Completion Criteria

- `docs/29_AI_STOCK_NEXT_ROADMAP_MS09_MS20.md` and `reports/MS-09.00_next_roadmap_ms09_ms20_report.md` are present.
- WBS and endpoint matrix contain natural MS-09.00 entries without helper guide text.
- Helper source files and insertion guide are excluded from the final changed-file set.
- Only the two existing project documents and two MS-09.00 documents remain changed.
- Offline validation commands pass or known warnings are documented.

### Next Step Candidate

```text
MS-09.01 candidate input contract preflight
```

## MS-09.01: Candidate Input Contract Preflight

### Purpose

Define the safe candidate input contract before any recommendation, scoring,
watchlist persistence, UI integration, Toss API, OpenAI/LLM, OAuth, accountSeq,
account, order, balance, asset, fill, or DB read/write functionality is added.

### Allowed Scope

- Add a pure no-I/O candidate input preflight module.
- Define allowed candidate sources such as dashboard selector, local snapshot
  summary, manual watchlist, future watchlist file, and test fixture.
- Define forbidden candidate sources such as real account holdings, account
  balance, order history, fills, live API refresh, OAuth/account scope,
  accountSeq-based source, raw API response, raw DB rows, and credential-based
  source.
- Define candidate item fields, safe validation statuses, duplicate handling
  policy, insufficient-data policy, and preflight summary flags.
- Add offline tests, WBS entry, endpoint matrix entry, and MS-09.01 report.

### Forbidden Scope

- No actual recommendation, scoring model, watchlist storage, UI change, or
  Streamlit app change.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, or browser run.
- No Toss API, OAuth token endpoint, OpenAI/LLM/API model call, credential
  request, accountSeq request, DB read, DB write, raw DB row output, raw API
  response output, order/account/assets/balance/fills implementation, or real
  order button.

### Deliverables

```text
src/ai_stock/recommendation/candidate_input_preflight.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_candidate_input_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.01_candidate_input_contract_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Allowed and forbidden candidate sources are explicitly defined.
- Candidate item fields exclude price, real holdings, real balance, fills,
  recommendation score, and buy/sell/hold labels.
- Safe statuses include valid, insufficient data, unsupported source, invalid
  symbol, disabled, duplicate, and needs-review states.
- Preflight summary required flags remain false for credential, DB read/write,
  Toss API, OpenAI, OAuth, accountSeq, and real order.
- Tests confirm deterministic pure no-I/O behavior and no forbidden labels.

### Next Step Candidate

```text
MS-09.02 watchlist data model
```

## MS-09.02: Watchlist Data Model

### Purpose

Define a local/manual watchlist data model on top of the MS-09.01 candidate
input contract before any watchlist persistence, file loader, UI, DB read/write,
scoring, recommendation, Toss API, OpenAI/LLM, OAuth, accountSeq, account,
order, balance, asset, or fill integration is added.

### Allowed Scope

- Add a pure no-I/O watchlist model and validation contract.
- Reuse MS-09.01 allowed sources, forbidden sources, candidate validation
  statuses, forbidden label policy, and required false flags.
- Define watchlist item fields, collection fields, statuses, forbidden fields,
  duplicate handling, disabled-item handling, insufficient-data handling, and
  summary flags.
- Add a pure conversion from watchlist items to MS-09.01 candidate inputs.
- Add offline tests, WBS entry, endpoint matrix entry, and MS-09.02 report.

### Forbidden Scope

- No actual recommendation, scoring model, watchlist storage, watchlist file
  loader, DB read, DB write, UI change, or Streamlit app change.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, or browser run.
- No Toss API, OAuth token endpoint, OpenAI/LLM/API model call, credential
  request, accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, or real order button.

### Deliverables

```text
src/ai_stock/recommendation/watchlist_model.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_watchlist_model.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.02_watchlist_data_model_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Watchlist item fields exclude real holdings, real balance, fills, order IDs,
  accountSeq, access token, authorization header, API keys, secrets, scores,
  buy/sell/hold labels, target price, and expected return.
- Watchlist collection fields are metadata-only and do not include storage path,
  file loader, DB table, or schema behavior.
- Summary flags remain false for credential, DB read/write, file read/write,
  Toss API, OpenAI, OAuth, accountSeq, real order, scoring, and UI.
- Tests confirm deterministic pure no-I/O behavior and MS-09.01 contract reuse.

### Next Step Candidate

```text
MS-09.03 manual/local watchlist source
```

## MS-09.03: Manual/Local Watchlist Source

### Purpose

Define a pure no-I/O manual/local source adapter that converts only
caller-supplied symbols or item dictionaries into the MS-09.02 watchlist model
and validates the result through the existing MS-09.01 candidate input contract.

### Allowed Scope

- Add a pure no-I/O source adapter for caller-supplied manual symbols, manual
  watchlist items, local static candidates, and test fixture records.
- Reuse MS-09.01 candidate source/status/forbidden label policies and MS-09.02
  watchlist item, collection, validation, summary, and candidate conversion
  policies.
- Normalize default market, tags, group, reason, enabled state, priority, note,
  and data availability hints without reading files or databases.
- Detect forbidden caller-supplied fields and report safe diagnostics without
  copying forbidden values into output models.
- Add offline tests, WBS entry, endpoint matrix entry, and MS-09.03 report.

### Forbidden Scope

- No actual recommendation, scoring model, watchlist storage, watchlist file
  loader, file read, file write, DB read, DB write, UI change, or Streamlit app
  change.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, or browser run.
- No Toss API, OAuth token endpoint, OpenAI/LLM/API model call, credential
  request, accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, or real order button.

### Deliverables

```text
src/ai_stock/recommendation/watchlist_source.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_watchlist_source.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.03_manual_local_watchlist_source_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Source types are limited to caller-supplied manual symbols, manual watchlist
  item dictionaries, local static candidates, and test fixture records.
- File path, database table/query, API endpoint, credential, token,
  Authorization header, accountSeq, raw API response, raw DB row, and real
  holdings/balance/fills/order inputs are rejected or safely diagnosed.
- Source result flags remain false for credential, DB read/write, file
  read/write, Toss API, OpenAI, OAuth, accountSeq, real order, scoring, and UI.
- Tests confirm deterministic pure no-I/O behavior, forbidden field sanitizing,
  duplicate handling, disabled item handling, and insufficient-data handling.

### Next Step Candidate

```text
MS-09.04 watchlist source test fixtures or manual dashboard preflight
```

## MS-09.04: Watchlist Source Test Fixtures

### Purpose

Define deterministic pure no-I/O watchlist source fixtures on top of the
MS-09.01 candidate input contract, MS-09.02 watchlist data model, and MS-09.03
manual/local source adapter. These fixtures are reusable by tests, future
documentation, and future dashboard preflight work without adding UI, storage,
file loading, DB access, scoring, recommendation, Toss API, OpenAI/LLM, OAuth,
accountSeq, account, order, balance, asset, or fill behavior.

### Allowed Scope

- Add in-memory fixture scenario records for basic manual symbols, mixed valid
  and invalid symbols, duplicates and disabled items, insufficient-data review,
  forbidden-field sanitization, and empty watchlists.
- Reuse the MS-09.03 source adapter to build actual watchlist source results.
- Define expected-vs-actual fixture evaluation that compares watchlist status,
  candidate statuses, required false flags, diagnostics, and rejection reasons.
- Keep fixture/evaluation outputs deterministic, immutable-friendly, and
  side-effect free.
- Add offline tests, WBS entry, endpoint matrix entry, and MS-09.04 report.

### Forbidden Scope

- No actual recommendation, scoring model, watchlist storage, fixture file
  loader, watchlist file loader, file read, file write, DB read, DB write, UI
  change, or Streamlit app change.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, or browser run.
- No Toss API, OAuth token endpoint, OpenAI/LLM/API model call, credential
  request, accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, or real order button.

### Deliverables

```text
src/ai_stock/recommendation/watchlist_fixtures.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_watchlist_fixtures.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.04_watchlist_source_test_fixtures_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- All allowed fixture scenarios are generated deterministically.
- Fixture records contain scenario, description, source config, expected
  watchlist status, expected candidate statuses, expected summary flags,
  expected rejection keywords, and expected diagnostics keywords.
- Evaluation results compare expected vs actual adapter output and keep all
  required flags false.
- Forbidden fields are diagnosed without copying forbidden values into output
  models.
- Forbidden labels are not generated as action labels, recommendation results,
  scoring output, or execution directives.

### Next Step Candidate

```text
MS-09.05 manual dashboard preflight
```

## MS-09.05: Manual Dashboard Preflight

### Purpose

Define a pure no-I/O dashboard preflight view model contract on top of the
MS-09.01 candidate input contract, MS-09.02 watchlist data model, MS-09.03
manual/local source adapter, and MS-09.04 test fixtures. This stage prepares
dashboard display fields, safety badges, warnings, diagnostics, and safe empty
states before any Streamlit UI integration or dashboard selector work.

### Allowed Scope

- Add an immutable-friendly dashboard preflight policy, row model, view model,
  validation result, and builder functions.
- Convert in-memory MS-09.03 source results and MS-09.04 fixtures into
  dashboard-ready preflight models without rendering UI.
- Define safety badges, forbidden badge/action policy, row sanitization,
  duplicate display policy, disabled display policy, insufficient-data display
  policy, empty-watchlist display policy, and required false flags.
- Reuse existing candidate, watchlist, source, fixture, forbidden field,
  forbidden label, and no-I/O policies.
- Add offline tests, WBS entry, endpoint matrix entry, and MS-09.05 report.

### Forbidden Scope

- No actual recommendation, scoring model, watchlist storage, file loader,
  file read, file write, DB read, DB write, UI integration, Streamlit component,
  Streamlit app change, dashboard selector, or `app/streamlit_app.py` change.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, or browser run.
- No Toss API, OAuth token endpoint, OpenAI/LLM/API model call, credential
  request, accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, or real order button.

### Deliverables

```text
src/ai_stock/recommendation/dashboard_preflight.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_dashboard_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.05_manual_dashboard_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Dashboard view model fields include display metadata, counts, rows, warnings,
  diagnostics, safety badges, and next-action hints only.
- Dashboard rows exclude account, order, balance, holdings, fills, token,
  authorization, API key, secret, score, target price, expected return, and
  buy/sell/hold action fields.
- Safety badges remain non-directive and include observation-only, manual/mock
  input only, no real order, no account access, no live API, no LLM, no DB
  write, needs review, and insufficient data states only.
- Required flags remain false for credential, DB read/write, file read/write,
  Toss API, OpenAI, OAuth, accountSeq, real order, scoring, UI, Streamlit, and
  HTTP smoke.
- Tests confirm deterministic pure no-I/O behavior, fixture-based preflight
  generation, forbidden field sanitization, forbidden label/action prevention,
  and safe display policy for duplicate, disabled, insufficient-data, and empty
  watchlist states.

### Next Step Candidate

```text
MS-09.06 manual dashboard UI integration
```

## MS-09.06: Manual Dashboard UI Integration

### Purpose

Render the MS-09.05 dashboard preflight view model inside the existing
Streamlit dashboard as an observation-only manual/watchlist preflight section.
This stage displays in-memory MS-09.04 fixture-based preflight output without
adding real recommendation, scoring, persistence, file loading, DB read/write,
Toss API, OpenAI/LLM, OAuth, accountSeq, account, order, balance, asset, or
fill behavior.

### Allowed Scope

- Add a Streamlit display section for manual/watchlist dashboard preflight.
- Use the existing MS-09.05 fixture dashboard preflight builder.
- Display safe section copy, fixture scenario selection, counts, safety badges,
  warnings, diagnostics, and sanitized row fields.
- Add AppTest-only UI integration coverage.
- Add WBS entry, endpoint matrix entry, and MS-09.06 report.

### Forbidden Scope

- No actual recommendation, scoring model, buy/sell/hold judgment, watchlist
  storage, watchlist file loader, fixture file loader, file read, file write,
  DB write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, order/account/assets/balance/fills implementation, or real
  order button.
- No Streamlit server, HTTP smoke, live smoke, fake smoke, manual browser, API
  refresh, OAuth login button, credential input, accountSeq input, file upload,
  file path input, DB refresh button, or real order control.

### Deliverables

```text
app/streamlit_app.py
tests/test_ai_recommendation_manual_dashboard_ui_integration.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.06_manual_dashboard_ui_integration_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Existing MS-08 mock-only recommendation panel remains intact.
- Manual dashboard preflight section renders observation-only copy and safe
  fixture/manual watchlist data.
- Safety badges include observation-only, manual/mock input only, no real
  order, no account access, no live API, no LLM, and no DB write.
- Displayed rows include only allowed preflight fields and exclude account,
  order, balance, holdings, fills, token, authorization, API key, secret,
  score, target price, expected return, and buy/sell/hold action fields.
- AppTest confirms safe render, fixture scenario selection or default fixture
  display, duplicate/disabled/insufficient/empty states, forbidden control
  absence, and no local DB file modification.

### Next Step Candidate

```text
MS-09.07 manual dashboard AppTest smoke hardening or MS-09.07 recommendation list UI preflight
```

## MS-09.07: Manual Dashboard AppTest Hardening

### Purpose

Harden the MS-09.06 observation-only manual/watchlist preflight UI with
additional Streamlit AppTest coverage. This is a checkpoint stage that fixes
UI safety policy expectations and fixture scenario coverage without adding new
dashboard functionality.

### Allowed Scope

- Add AppTest hardening coverage for the existing Manual Watchlist Dashboard
  Preflight section.
- Verify observation-only copy, fixture scenario selectbox behavior, fixture
  coverage expander output, summary metrics, safety badges, warnings,
  diagnostics, rows, and safe empty states.
- Verify forbidden button/action/input absence and forbidden field
  sanitization in rendered output.
- Confirm local DB file metadata is unchanged by AppTest render.
- Add WBS entry, endpoint matrix entry, and MS-09.07 report.
- Keep `app/streamlit_app.py` unchanged unless label stability requires a
  minimal copy-only adjustment.

### Forbidden Scope

- No actual recommendation, scoring model, buy/sell/hold judgment, watchlist
  storage, watchlist file loader, fixture file loader, file read, file write,
  new DB read/write implementation, Toss API call, OAuth token endpoint call,
  OpenAI/LLM/API model call, credential request, accountSeq request, raw DB row
  output, raw API response output, order/account/assets/balance/fills
  implementation, real order button, API refresh button, OAuth login button,
  credential input, accountSeq input, Streamlit server, HTTP smoke, live smoke,
  fake smoke, or manual browser run.

### Deliverables

```text
tests/test_ai_recommendation_manual_dashboard_apptest_hardening.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.07_manual_dashboard_apptest_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- AppTest renders the Manual Watchlist Dashboard Preflight section without
  Streamlit server, HTTP smoke, browser, Toss API, OAuth, OpenAI/LLM, or
  credential access.
- Scenario selectbox covers basic, mixed invalid, duplicate/disabled,
  insufficient-data, forbidden-field sanitized, and empty watchlist fixtures.
- Fixture coverage expander lists every fixture scenario and safe status.
- Safety badges and observation-only/no-order/no-account/no-live-api/no-LLM
  copy remain visible.
- Forbidden fields remain sanitized from row output.
- Forbidden buttons, actions, file upload/path, credential, API refresh, OAuth
  login, accountSeq, raw API response, and raw DB row controls remain absent.
- DB file metadata remains unchanged by AppTest render.

### Next Step Candidate

```text
MS-10.00 feature/data quality model preflight
```

## MS-10.00: Feature/Data Quality Model Preflight

### Purpose

Define a pure no-I/O feature/data quality contract on top of the MS-09
candidate, watchlist, manual/local source, fixture, and dashboard preflight
contracts. This stage expresses whether candidate data is usable, incomplete,
or requires review. It does not score, rank, recommend, or produce
buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/feature_quality.py`.
- Reuse MS-09 candidate input, watchlist model, manual/local source, fixture,
  and dashboard preflight contracts.
- Define feature quality policy, feature records, feature quality assessments,
  allowed quality statuses, forbidden action/status policy, summary flags, and
  validation.
- Build feature quality assessments from dashboard rows, dashboard preflights,
  and all six in-memory watchlist fixtures.
- Add offline unit tests, WBS entry, endpoint matrix entry, and MS-10.00 report.

### Forbidden Scope

- No actual recommendation, scoring model, ranking model, buy/sell/hold
  judgment, target price, expected return, profit probability, watchlist
  storage, watchlist file loader, feature file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, order/account/assets/balance/fills implementation, UI
  integration, `app/streamlit_app.py` change, Streamlit server, HTTP smoke,
  live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/feature_quality.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_feature_quality.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-10.00_feature_data_quality_model_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Feature quality policy documents allowed feature names, forbidden feature
  names, allowed quality statuses, forbidden action/status labels, and all
  required false flags.
- Feature records and assessments contain no score, rank, recommendation,
  action, target price, expected return, profit probability, account, order,
  credential, token, or accountSeq fields.
- Valid, duplicate, disabled, insufficient-data, forbidden-field sanitized,
  invalid, and empty fixture states map to conservative quality statuses.
- All six MS-09.04 in-memory fixture scenarios generate deterministic feature
  quality assessments through MS-09.05 dashboard preflight builders.
- All required flags remain false and no UI, API, DB, file loader, scoring,
  ranking, or recommendation path is introduced.

### Next Step Candidate

```text
MS-10.01 feature quality fixture expansion or MS-10.01 deterministic feature extraction preflight
```

## MS-10.01: Feature Quality Fixture Expansion

### Purpose

Expand deterministic feature quality fixture scenarios on top of the MS-10.00
feature/data quality model contract. This stage fixes expected-vs-actual
quality behavior for data quality, review, and usability cases only; it does
not score, rank, recommend, or produce buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/feature_quality_fixtures.py`.
- Reuse MS-10.00 feature quality policy, assessment builders, validators,
  allowed quality statuses, forbidden action/status policy, and required false
  flags.
- Reuse MS-09.04 in-memory watchlist fixtures and MS-09.05 dashboard preflight
  outputs through the MS-10.00 quality builders.
- Define expanded fixture records, all-fixture matrix coverage, evaluator
  results, and expected-vs-actual checks.
- Add offline unit tests, WBS entry, endpoint matrix entry, and MS-10.01 report.

### Forbidden Scope

- No actual recommendation, scoring model, ranking model, buy/sell/hold
  judgment, target price, expected return, profit probability, watchlist
  storage, watchlist file loader, feature file loader, fixture file loader,
  file read/write, DB read/write, Toss API call, OAuth token endpoint call,
  OpenAI/LLM/API model call, credential request, accountSeq request, raw DB row
  output, raw API response output, order/account/assets/balance/fills
  implementation, UI integration, `app/streamlit_app.py` change, Streamlit
  server, HTTP smoke, live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/feature_quality_fixtures.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_feature_quality_fixtures.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-10.01_feature_quality_fixture_expansion_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Expanded quality fixtures cover basic OK, mixed invalid/review, duplicate,
  disabled, insufficient-data, forbidden-field sanitized, empty input, and the
  all-fixture matrix.
- Evaluators compare expected quality statuses, review counts, future-scoring
  usability counts, blocked reason keywords, warnings, diagnostics, required
  false flags, and forbidden keyword absence.
- Duplicate, disabled, insufficient-data, invalid, forbidden-field sanitized,
  and empty input cases remain conservative review/block states.
- Forbidden fields are diagnostic-only and are not copied as output fields or
  raw values.
- All required flags remain false and no UI, API, DB, file loader, scoring,
  ranking, or recommendation path is introduced.

### Next Step Candidate

```text
MS-10.02 deterministic feature extraction preflight
```

## MS-10.02: Deterministic Feature Extraction Preflight

### Purpose

Define a pure no-I/O deterministic feature extraction preflight contract on top
of the MS-10.00 feature quality model and MS-10.01 fixture/evaluator layer.
This stage normalizes already in-memory dashboard preflight, feature quality,
and fixture assessment results into future-scoring candidate feature sets. It
does not fetch actual feature data, score, rank, recommend, or produce
buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/feature_extraction_preflight.py`.
- Reuse MS-10.00 feature quality policy, assessment builders, validators,
  allowed quality statuses, forbidden action/status policy, and required false
  flags.
- Reuse MS-10.01 feature quality fixtures and evaluators.
- Reuse MS-09.04 in-memory watchlist fixtures and MS-09.05 dashboard preflight
  through existing feature quality builders.
- Define feature extraction policy, extraction input records, extracted feature
  set records, allowed extraction statuses, forbidden extraction sources,
  forbidden output labels/fields, validation, fixture extraction builders, and
  summary counts.
- Add offline unit tests, WBS entry, endpoint matrix entry, and MS-10.02 report.

### Forbidden Scope

- No actual recommendation, scoring model, ranking model, buy/sell/hold
  judgment, target price, expected return, profit probability, API/DB/file
  feature lookup, watchlist storage, watchlist file loader, feature file
  loader, file read/write, DB read/write, Toss API call, OAuth token endpoint
  call, OpenAI/LLM/API model call, credential request, accountSeq request, raw
  DB row output, raw API response output, order/account/assets/balance/fills
  implementation, UI integration, `app/streamlit_app.py` change, Streamlit
  server, HTTP smoke, live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/feature_extraction_preflight.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_feature_extraction_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-10.02_deterministic_feature_extraction_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Extraction policy documents allowed in-memory sources, forbidden sources,
  allowed extraction statuses, forbidden output labels/fields, and all required
  false flags.
- Feature extraction input and extracted feature set models contain no score,
  rank, recommendation, action, target price, expected return, profit
  probability, account, order, credential, token, or accountSeq fields.
- Quality OK, duplicate, disabled, insufficient-data, invalid,
  forbidden-field sanitized, and empty-input states map to conservative
  extraction statuses.
- Extracted features are derived only from existing MS-10.00 feature records and
  are deterministic.
- All MS-09.04 and MS-10.01 fixture paths produce deterministic extraction
  outputs with required flags false.
- No UI, API, DB, file loader, scoring, ranking, or recommendation path is
  introduced.

### Next Step Candidate

```text
MS-10.03 feature extraction fixture hardening or MS-11.00 deterministic scoring model preflight
```

## MS-10.03: Feature Extraction Fixture Hardening

### Purpose

Add a pure no-I/O fixture/evaluator hardening layer for the MS-10.02
deterministic feature extraction preflight contract. This stage expands and
locks extraction result verification cases; it does not fetch features, score,
rank, recommend, or produce buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/feature_extraction_fixtures.py`.
- Reuse MS-10.02 extraction policy, extraction builders, validators, summary
  counts, allowed extraction statuses, forbidden source/output policy, and
  required false flags.
- Reuse MS-10.01 feature quality fixture/evaluator coverage.
- Reuse MS-10.00 feature quality contract and MS-09.04/MS-09.05 in-memory
  fixture/dashboard preflight paths through existing builders.
- Define extraction fixture records, hardening scenarios, forbidden fixture
  scenarios, expected-vs-actual evaluator results, all-fixture matrix checks,
  and forbidden output sanitization checks.
- Add offline unit tests, WBS entry, endpoint matrix entry, and MS-10.03
  report.

### Forbidden Scope

- No actual recommendation, scoring model, ranking model, buy/sell/hold
  judgment, target price, expected return, profit probability, API/DB/file
  feature lookup, watchlist storage, watchlist file loader, feature file
  loader, fixture file loader, file read/write, DB read/write, Toss API call,
  OAuth token endpoint call, OpenAI/LLM/API model call, credential request,
  accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, UI integration,
  `app/streamlit_app.py` change, Streamlit server, HTTP smoke, live/fake
  smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/feature_extraction_fixtures.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_feature_extraction_fixtures.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-10.03_feature_extraction_fixture_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Extraction fixtures cover basic ready, mixed review, duplicate blocked,
  disabled blocked, missing data blocked, forbidden-field sanitized, empty
  input, and all-fixture matrix scenarios.
- Evaluators compare expected extraction statuses, ready counts, review
  counts, future-scoring usability counts, missing/blocked feature keywords,
  blocked reason keywords, warnings, diagnostics, required false flags, and
  forbidden keyword absence.
- Duplicate, disabled, insufficient-data, invalid, forbidden-field sanitized,
  and empty-input cases remain conservative review/block extraction states.
- Forbidden fields are diagnostics-only and are not copied as output fields or
  raw values.
- All required flags remain false and no UI, API, DB, file loader, scoring,
  ranking, or recommendation path is introduced.

### Next Step Candidate

```text
MS-11.00 deterministic scoring model preflight
```

## MS-11.00: Deterministic Scoring Model Preflight

### Purpose

Define a pure no-I/O deterministic scoring preflight contract on top of the
MS-10.02 extracted feature set contract and MS-10.03 fixture/evaluator
hardening. This stage creates only a data-quality scoring policy, input model,
component model, result model, validators, and summaries for future scoring
shape checks. It does not rank, recommend, produce buy/sell/hold actions, or
interpret scores as investment attractiveness.

### Allowed Scope

- Add `src/ai_stock/recommendation/scoring_preflight.py`.
- Reuse MS-10.02 feature extraction policy, extraction builders, validators,
  summaries, allowed extraction statuses, forbidden source/output policy, and
  required false flags.
- Reuse MS-10.03 feature extraction fixtures and evaluators.
- Reuse MS-10.00/MS-10.01 feature quality contracts indirectly through the
  extraction contract chain.
- Define scoring preflight policy, scoring input records, score components,
  scoring preflight result records, allowed scoring statuses, forbidden scoring
  sources, forbidden output fields, validation, fixture scoring builders, and
  summary counts.
- Add offline unit tests, WBS entry, endpoint matrix entry, and MS-11.00
  report.

### Forbidden Scope

- No actual recommendation, ranking model, ranking list, buy/sell/hold
  judgment, target price, expected return, profit probability, API/DB/file
  feature lookup, watchlist storage, watchlist file loader, feature file
  loader, fixture file loader, file read/write, DB read/write, Toss API call,
  OAuth token endpoint call, OpenAI/LLM/API model call, credential request,
  accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, UI integration,
  `app/streamlit_app.py` change, Streamlit server, HTTP smoke, live/fake
  smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/scoring_preflight.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_scoring_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-11.00_deterministic_scoring_model_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Scoring preflight policy documents allowed in-memory extracted feature set
  sources, forbidden sources, allowed scoring statuses, forbidden output
  labels/fields, data-quality component names, and all required false flags.
- Scoring input, score component, and scoring preflight result models contain
  no recommendation, action, buy/sell/hold, rank, target price, expected
  return, profit probability, account, order, credential, token, or accountSeq
  fields.
- Extraction ready, duplicate, disabled, missing-data, invalid,
  forbidden-field sanitized, and empty-input states map to conservative scoring
  statuses.
- `total_score` is deterministic, bounded by `score_scale`, and represents
  only data quality and extraction readiness preflight shape.
- All MS-09.04 and MS-10.03 fixture paths produce deterministic scoring
  preflight outputs with required flags false.
- No UI, API, DB, file loader, ranking, recommendation, or trade directive path
  is introduced.

### Next Step Candidate

```text
MS-11.01 scoring fixture expansion
```

## MS-11.01: Scoring Fixture Expansion

### Purpose

Add a pure no-I/O scoring fixture/evaluator layer on top of the MS-11.00
deterministic scoring preflight contract. This stage fixes expected scoring
preflight statuses, score bounds, component names, required false flags, and
forbidden-output absence across representative fixture scenarios. The
`total_score` remains a data-quality and extraction-readiness preflight score
only, not investment attractiveness.

### Allowed Scope

- Add `src/ai_stock/recommendation/scoring_fixtures.py`.
- Reuse MS-11.00 scoring preflight policy, input/result builders,
  component builders, validators, summaries, allowed statuses, forbidden
  source/output policies, and required false flags.
- Reuse MS-10.03 feature extraction fixtures/evaluators and the MS-10.02
  extraction contract chain.
- Reuse MS-10.00/MS-10.01 feature quality contracts indirectly through the
  extraction and scoring contract chain.
- Define scoring fixture policy, fixture records, evaluator result records,
  fixture builders, all-fixture matrix evaluation, and offline unit tests.
- Add endpoint matrix and MS-11.01 report entries.

### Forbidden Scope

- No actual recommendation, ranking model, ranking list, buy/sell/hold
  judgment, target price, expected return, profit probability, API/DB/file
  feature lookup, watchlist storage, watchlist file loader, feature file
  loader, fixture file loader, file read/write, DB read/write, Toss API call,
  OAuth token endpoint call, OpenAI/LLM/API model call, credential request,
  accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, UI integration,
  `app/streamlit_app.py` change, Streamlit server, HTTP smoke, live/fake
  smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/scoring_fixtures.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_scoring_fixtures.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-11.01_scoring_fixture_expansion_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Scoring fixtures cover basic ready, mixed review, duplicate blocked,
  disabled blocked, missing data blocked, forbidden-field sanitized, empty
  input, and all-fixture matrix scenarios.
- Evaluators compare expected scoring statuses, ready counts, review counts,
  future-ranking usability counts, total-score bounds, component names,
  blocked reason keywords, warnings, diagnostics, required false flags, and
  forbidden keyword absence.
- Duplicate, disabled, missing-data, invalid, forbidden-field sanitized, and
  empty-input cases remain conservative review/block score states.
- `total_score` is deterministic, bounded by `score_scale`, and is not used as
  recommendation, ranking, action, buy/sell/hold, target price, expected
  return, or profit probability output.
- All required flags remain false and no UI, API, DB, file loader, ranking,
  recommendation, or trade directive path is introduced.

### Next Step Candidate

```text
MS-11.02 scoring fixture hardening or MS-12.00 recommendation list UI preflight
```

## MS-11.02: Scoring Fixture Hardening

### Purpose

Add a pure no-I/O hardening layer on top of the MS-11.00 deterministic scoring
preflight contract and MS-11.01 scoring fixture/evaluator layer. This stage
checks scoring fixture safety, determinism, forbidden-output absence, summary
stability, and evaluator failure behavior. The `total_score` remains a
data-quality and extraction-readiness preflight score only, not investment
attractiveness.

### Allowed Scope

- Add `src/ai_stock/recommendation/scoring_fixture_hardening.py`.
- Reuse MS-11.00 scoring preflight policy, result builders, validators,
  summaries, allowed statuses, forbidden source/output policies, and required
  false flags.
- Reuse MS-11.01 scoring fixture policy, fixture builders, evaluators, and
  all-fixture matrix.
- Reuse the MS-10.03/MS-10.02 extraction and MS-10.00/MS-10.01 quality
  contract chain indirectly through scoring fixtures.
- Define hardening policy, hardening result, deterministic checks, failure
  probe, offline unit tests, endpoint matrix entry, and report.

### Forbidden Scope

- No actual recommendation, ranking model, ranking list, buy/sell/hold
  judgment, target price, expected return, profit probability, API/DB/file
  feature lookup, watchlist storage, watchlist file loader, feature file
  loader, fixture file loader, file read/write, DB read/write, Toss API call,
  OAuth token endpoint call, OpenAI/LLM/API model call, credential request,
  accountSeq request, raw DB row output, raw API response output,
  order/account/assets/balance/fills implementation, UI integration,
  `app/streamlit_app.py` change, Streamlit server, HTTP smoke, live/fake
  smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/scoring_fixture_hardening.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_scoring_fixture_hardening.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-11.02_scoring_fixture_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- All required scoring fixture scenarios are present, including
  `scoring_all_fixture_matrix`.
- All scoring fixture evaluators pass and intentional mismatch/failure probe
  produces a failure.
- Total scores remain deterministic and within `0..100`.
- Score component names and scoring statuses remain within allowed sets.
- Forbidden output keywords and directive labels are absent from scoring
  outputs.
- Required external capability flags remain false.
- Summary aggregation and repeated hardening runs are deterministic.
- `total_score` is not used as recommendation, ranking, action, buy/sell/hold,
  target price, expected return, or profit probability output.
- No UI, API, DB, file loader, ranking, recommendation, or trade directive path
  is introduced.

### Next Step Candidate

```text
MS-12.00 recommendation list model preflight
```

## MS-12.00: Recommendation List Model Preflight

### Purpose

Add a pure no-I/O recommendation list model preflight contract on top of the
MS-11.00 deterministic scoring preflight, MS-11.01 scoring fixtures, and
MS-11.02 scoring fixture hardening contracts. This stage defines only future
list item model shape, policy, validation, and summary guardrails. It does not
create an actual recommendation list, ranking, buy/sell/hold action, or trade
directive. The `score_snapshot` remains a data-quality and extraction-readiness
preflight score snapshot only, not investment attractiveness.

### Allowed Scope

- Add `src/ai_stock/recommendation/recommendation_list_preflight.py`.
- Reuse MS-11.00 scoring preflight policy, result builders, validators,
  summaries, allowed statuses, forbidden source/output policies, and required
  false flags.
- Reuse MS-11.01 scoring fixture policy, fixture builders, evaluators, and
  all-fixture matrix.
- Reuse MS-11.02 scoring fixture hardening policy and checks.
- Define recommendation list preflight policy, list input model, observation
  item model, item validation, deterministic builders, summaries, offline unit
  tests, endpoint matrix entry, and report.

### Forbidden Scope

- No actual recommendation, recommendation list generation, ranking model,
  ranking list, buy/sell/hold judgment, target price, expected return, profit
  probability, API/DB/file feature lookup, watchlist storage, watchlist file
  loader, feature file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, order/account/assets/balance/fills implementation, UI
  integration, `app/streamlit_app.py` change, Streamlit server, HTTP smoke,
  live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/recommendation_list_preflight.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_recommendation_list_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-12.00_recommendation_list_model_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Recommendation list preflight policy documents allowed in-memory scoring
  result sources, forbidden sources, allowed item statuses, forbidden action,
  recommendation, ranking labels, forbidden output fields, and required false
  flags.
- List input and observation item models contain no recommendation result,
  action, buy/sell/hold, rank, ranking position, target price, expected return,
  profit probability, order, position, account, credential, token, or accountSeq
  fields.
- Score statuses map conservatively to observation item statuses for ready,
  needs-review, duplicate, disabled, missing-data, invalid, forbidden-field
  sanitized, blocked-quality, and empty-input states.
- `display_bucket` is a review grouping label only, not a rank or priority.
- `usable_for_future_list` is a future list-readiness flag only, not a ranking
  flag.
- `score_snapshot` is not used as recommendation, ranking, action,
  buy/sell/hold, target price, expected return, or profit probability output.
- All required flags remain false and no UI, API, DB, file loader, ranking,
  recommendation, or trade directive path is introduced.

### Next Step Candidate

```text
MS-12.01 recommendation list fixture expansion
```

## MS-12.01: Recommendation List Fixture Expansion

### Purpose

Add a pure no-I/O fixture/evaluator layer on top of the MS-12.00
recommendation list model preflight contract. This stage fixes
observation-only list item scenarios and compares expected item statuses,
review counts, list-readiness counts, display buckets, score snapshot bounds,
component names, diagnostics, warnings, required false flags, and forbidden
output absence. It does not create an actual recommendation list, ranking, or
buy/sell/hold action.

### Allowed Scope

- Add `src/ai_stock/recommendation/recommendation_list_fixtures.py`.
- Reuse MS-12.00 recommendation list preflight policy, item builders,
  validators, summaries, allowed item statuses, forbidden source/output
  policies, and required false flags.
- Reuse MS-11.00 scoring preflight, MS-11.01 scoring fixtures/evaluators, and
  MS-11.02 scoring fixture hardening.
- Define recommendation list fixture policy, fixture records, scenario builders,
  expected-vs-actual evaluators, offline unit tests, endpoint matrix entry, and
  report.

### Forbidden Scope

- No actual recommendation, recommendation list generation, ranking model,
  ranking list, buy/sell/hold judgment, target price, expected return, profit
  probability, API/DB/file feature lookup, watchlist storage, watchlist file
  loader, feature file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, order/account/assets/balance/fills implementation, UI
  integration, `app/streamlit_app.py` change, Streamlit server, HTTP smoke,
  live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/recommendation_list_fixtures.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_recommendation_list_fixtures.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-12.01_recommendation_list_fixture_expansion_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Recommendation list fixtures cover ready-for-review, mixed review,
  duplicate blocked, disabled blocked, missing-data blocked, forbidden-field
  sanitized, empty input, and all-fixture matrix scenarios.
- Evaluators compare expected item statuses, ready-for-review counts, review
  counts, future-list usability counts, display buckets, score snapshot bounds,
  component names, blocked reason keywords, warnings, diagnostics, required
  false flags, and forbidden keyword absence.
- `score_snapshot` remains a data-quality and extraction-readiness preflight
  snapshot only, not investment attractiveness.
- `display_bucket` remains a review grouping label only, not rank, priority, or
  ordering.
- `usable_for_future_list` remains a future list-readiness flag only, not a
  ranking flag.
- All required flags remain false and no UI, API, DB, file loader, ranking,
  recommendation, actual list generation, or trade directive path is
  introduced.

### Next Step Candidate

```text
MS-12.02 recommendation list fixture hardening
```

## MS-12.02: Recommendation List Fixture Hardening

### Purpose

Add a pure no-I/O hardening layer on top of the MS-12.00 recommendation list
model preflight contract and MS-12.01 recommendation list fixture/evaluator
layer. This stage verifies observation-only list fixture scenarios, evaluator
success, score snapshot bounds, display bucket guardrails, component names,
allowed item statuses, forbidden output absence, required false flags,
deterministic repeated runs, summary stability, and evaluator failure probe
behavior. It does not create an actual recommendation list, ranking, or
buy/sell/hold action.

### Allowed Scope

- Add `src/ai_stock/recommendation/recommendation_list_fixture_hardening.py`.
- Reuse MS-12.00 recommendation list preflight policy, item builders,
  validators, summaries, allowed item statuses, forbidden source/output
  policies, and required false flags.
- Reuse MS-12.01 recommendation list fixtures/evaluators.
- Reuse MS-11.00 scoring preflight, MS-11.01 scoring fixtures/evaluators, and
  MS-11.02 scoring fixture hardening.
- Define recommendation list fixture hardening policy, aggregate hardening
  result, deterministic check functions, evaluator failure probe, offline unit
  tests, endpoint matrix entry, and report.

### Forbidden Scope

- No actual recommendation, actual recommendation list generation, ranking
  model, ranking list, buy/sell/hold judgment, target price, expected return,
  profit probability, API/DB/file feature lookup, watchlist storage, watchlist
  file loader, feature file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, order/account/assets/balance/fills implementation, UI
  integration, `app/streamlit_app.py` change, Streamlit server, HTTP smoke,
  live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/recommendation_list_fixture_hardening.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_recommendation_list_fixture_hardening.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-12.02_recommendation_list_fixture_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Required recommendation list fixture scenarios exist, including
  `list_all_fixture_matrix`.
- All recommendation list fixture evaluators pass.
- `score_snapshot` remains within `0..100` and remains a data-quality and
  extraction-readiness preflight snapshot only.
- `display_bucket` remains a review grouping label only, not rank, priority, or
  ordering.
- `usable_for_future_list` remains a future list-readiness flag only, not a
  ranking flag.
- Component names and item statuses remain inside allowed contract values.
- Forbidden item statuses and forbidden output keywords are absent from
  hardening outputs.
- Required flags remain false, repeated runs are deterministic, summaries are
  stable, and evaluator mismatch probes produce failures.
- No UI, API, DB, file loader, ranking, recommendation, actual list generation,
  or trade directive path is introduced.

### Next Step Candidate

```text
MS-13.00 observation list UI preflight
```

## MS-13.00: Observation List UI Preflight

### Purpose

Add a pure no-I/O observation-list UI preflight contract on top of the
MS-12.00 recommendation list model preflight, MS-12.01 recommendation list
fixtures/evaluators, and MS-12.02 recommendation list fixture hardening. This
stage defines Streamlit-safe row/view model shapes, display policy, summary,
and guardrail validation for future UI integration. It does not render UI,
modify Streamlit code, create an actual recommendation list, rank candidates,
or issue buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/observation_list_ui_preflight.py`.
- Reuse MS-12.00 recommendation list preflight policy, item builders,
  validators, summaries, allowed item statuses, forbidden source/output
  policies, and required false flags.
- Reuse MS-12.01 recommendation list fixtures/evaluators.
- Reuse MS-12.02 recommendation list fixture hardening.
- Define observation-list UI preflight policy, row/view model, validation
  result, summary model, deterministic row builders, validators, offline unit
  tests, endpoint matrix entry, and report.

### Forbidden Scope

- No Streamlit import, UI rendering, UI integration, button, callback,
  session state, API refresh button, OAuth login button, credential input,
  accountSeq input, order/account/assets/balance/fills UI, actual
  recommendation, actual recommendation list generation, ranking model,
  ranking list, buy/sell/hold judgment, target price, expected return, profit
  probability, API/DB/file feature lookup, watchlist storage, watchlist file
  loader, feature file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, `app/streamlit_app.py` change, Streamlit server, HTTP
  smoke, live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/observation_list_ui_preflight.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_observation_list_ui_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-13.00_observation_list_ui_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Observation-list UI preflight policy exists with allowed view modes, allowed
  column keys, forbidden column keys, allowed badge labels, forbidden badge
  labels, required disclaimer labels, required false flags, and no-action,
  no-ranking, no-trade-directive, no-live-refresh, deterministic-only policies.
- Observation-list UI row/view model exists with symbol, market, item status,
  status badge, display bucket, score snapshot label, score scale label,
  component summary, review/usability labels, blocked reason summary, warning
  summary, diagnostic summary, disclaimer labels, and guardrail flags.
- Rows can be built deterministically from all in-memory recommendation list
  fixtures.
- `status_badge` remains an observation status, not buy/sell/hold.
- `score_snapshot_label` remains a data-quality/extraction-readiness display
  label, not recommendation, ranking, or action.
- `display_bucket` remains a grouping label only, not rank, priority, or
  order.
- `usability_label` remains a list-readiness display label only, not a ranking
  flag.
- Forbidden output fields are not copied into UI rows and required flags
  remain false.
- No Streamlit import, app code change, UI control, API refresh, OAuth,
  credential input, accountSeq input, API, DB, file loader, ranking,
  recommendation, actual list generation, or trade directive path is
  introduced.

### Next Step Candidate

```text
MS-13.01 observation list UI fixture expansion
```

## MS-13.01: Observation List UI Fixture Expansion

### Purpose

Add a pure no-I/O fixture/evaluator layer for the MS-13.00 observation-list UI
preflight contract. This stage fixes deterministic row/view model expectations
for ready, review, blocked, sanitized, empty, and all-fixture matrix cases. It
does not connect Streamlit UI, modify app code, create an actual
recommendation list, rank candidates, or issue buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/observation_list_ui_fixtures.py`.
- Reuse MS-13.00 observation-list UI preflight policy, row builders,
  validators, and summary.
- Reuse MS-12.00 recommendation list preflight, MS-12.01 recommendation list
  fixtures/evaluators, and MS-12.02 recommendation list fixture hardening.
- Define observation-list UI fixture policy, fixture record, evaluator result,
  deterministic fixture builders, expected-vs-actual evaluator, offline unit
  tests, endpoint matrix entry, and report.

### Forbidden Scope

- No Streamlit import, UI rendering, UI integration, button, callback,
  session state, API refresh button, OAuth login button, credential input,
  accountSeq input, order/account/assets/balance/fills UI, actual
  recommendation, actual recommendation list generation, ranking model,
  ranking list, buy/sell/hold judgment, target price, expected return, profit
  probability, API/DB/file feature lookup, watchlist storage, watchlist file
  loader, feature file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, `app/streamlit_app.py` change, Streamlit server, HTTP
  smoke, live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/observation_list_ui_fixtures.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_observation_list_ui_fixtures.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-13.01_observation_list_ui_fixture_expansion_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Observation-list UI fixture policy, fixture record, and evaluator result
  models exist and are immutable.
- Required fixture scenarios exist:
  `ui_basic_ready_for_review`, `ui_mixed_review`,
  `ui_duplicates_blocked`, `ui_disabled_blocked`,
  `ui_missing_data_blocked`, `ui_forbidden_field_sanitized`,
  `ui_empty_input`, and `ui_all_fixture_matrix`.
- All UI fixture scenarios evaluate deterministically and pass expected-vs-
  actual checks.
- Rows can be built from all in-memory recommendation list fixtures without
  file, network, environment, database, or Streamlit access.
- `status_badge` remains an observation status, not buy/sell/hold.
- `score_snapshot_label` remains a data-quality/extraction-readiness display
  label, not recommendation, ranking, or action.
- `display_bucket` remains a grouping label only, not rank, priority, or
  order.
- `usability_label` remains a list-readiness display label only, not a ranking
  flag.
- Forbidden output fields are not copied into UI rows and required flags
  remain false.
- No UI integration, API, DB, file loader, ranking, recommendation, actual list
  generation, or trade directive path is introduced.

### Next Step Candidate

```text
MS-13.02 observation list UI fixture hardening
```

## MS-13.02: Observation List UI Fixture Hardening

### Purpose

Add a pure no-I/O hardening layer for the MS-13.00 observation-list UI
preflight contract and MS-13.01 observation-list UI fixtures/evaluators. This
stage rechecks scenario coverage, evaluator success, row generation,
determinism, summary stability, forbidden-output absence, required false
flags, and UI safety guardrails. It does not connect Streamlit UI, modify app
code, create an actual recommendation list, rank candidates, or issue
buy/sell/hold actions.

### Allowed Scope

- Add `src/ai_stock/recommendation/observation_list_ui_fixture_hardening.py`.
- Reuse MS-13.00 observation-list UI preflight policy, row builders,
  validators, and summary.
- Reuse MS-13.01 observation-list UI fixtures/evaluators.
- Reuse MS-12.00 recommendation list preflight, MS-12.01 recommendation list
  fixtures/evaluators, and MS-12.02 recommendation list fixture hardening.
- Define observation-list UI fixture hardening policy, hardening result,
  deterministic check functions, evaluator failure probe, offline unit tests,
  endpoint matrix entry, and report.

### Forbidden Scope

- No Streamlit import, UI rendering, UI integration, button, callback,
  session state, API refresh button, OAuth login button, credential input,
  accountSeq input, order/account/assets/balance/fills UI, actual
  recommendation, actual recommendation list generation, ranking model,
  ranking list, buy/sell/hold judgment, target price, expected return, profit
  probability, API/DB/file feature lookup, watchlist storage, watchlist file
  loader, feature file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request, accountSeq request, raw DB row output, raw API
  response output, `app/streamlit_app.py` change, Streamlit server, HTTP
  smoke, live/fake smoke, or manual browser run.

### Deliverables

```text
src/ai_stock/recommendation/observation_list_ui_fixture_hardening.py
src/ai_stock/recommendation/__init__.py
tests/test_ai_recommendation_observation_list_ui_fixture_hardening.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-13.02_observation_list_ui_fixture_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm forbidden paths remain unchanged and `.env.local`, DB file, and
  `data/` remain untracked/ignored.

### Completion Criteria

- Observation-list UI fixture hardening policy and result models exist and are
  immutable.
- Required fixture scenarios exist, including `ui_all_fixture_matrix`.
- All UI fixture evaluators pass and all-fixture UI row generation remains
  deterministic.
- `status_badge` remains an observation status, not buy/sell/hold.
- `score_snapshot_label` remains a data-quality/extraction-readiness display
  label, not recommendation, ranking, or action.
- `display_bucket` remains a grouping label only, not rank, priority, or
  order.
- `usability_label` remains a list-readiness display label only, not a ranking
  flag.
- Forbidden output fields are not copied into UI rows and required flags
  remain false.
- Repeated runs are deterministic, summaries are stable, and evaluator
  mismatch probes produce failures.
- No Streamlit import, app code change, UI control, API refresh, OAuth,
  credential input, accountSeq input, API, DB, file loader, ranking,
  recommendation, actual list generation, or trade directive path is
  introduced.

### Next Step Candidate

```text
MS-13.03 Streamlit observation list UI integration preflight
```

## MS-13.03: Streamlit Observation List UI Integration Preflight

### Purpose

Add a Streamlit observation-list UI preflight section based on the MS-13.00
observation-list UI preflight contract, MS-13.01 UI fixture/evaluator layer,
and MS-13.02 UI fixture hardening layer. This stage displays fixture-based
observation rows only. It is not a live API integration, an actual
recommendation UI, a ranking table, or a buy/sell/hold workflow.

### Allowed Scope

- Update `app/streamlit_app.py` with an observation-only preflight section.
- Add `tests/test_ai_recommendation_observation_list_ui_integration_preflight.py`.
- Use fixture-derived observation row display fields only:
  `symbol`, `market`, `item_status`, `status_badge`, `display_bucket`,
  `score_snapshot_label`, `score_scale_label`, `component_summary`,
  `needs_review_label`, `usability_label`, `blocked_reason_summary`,
  `warning_summary`, `diagnostic_summary`, `disclaimer_labels`, and
  `guardrail_flags`.
- Reference the MS-13.00 row builder, summary builder, and MS-13.02 hardening
  runner contract without adding live input, API refresh, or session mutation.
- Update this WBS, the endpoint matrix, and the MS-13.03 report.

### Forbidden Scope

- No actual recommendation list, ranking list, buy/sell/hold judgment, target
  price, expected return, profit probability, watchlist persistence, feature
  file loader, watchlist file loader, fixture file loader, file read/write, DB
  read/write, Toss API call, OAuth token endpoint call, OpenAI/LLM/API model
  call, credential request/input, accountSeq request/input, order/account/
  assets/balance/holdings/fills UI, API refresh button, OAuth login button,
  `st.button`, callback, session state, Streamlit server, HTTP smoke, live/fake
  smoke, or manual browser run.

### Deliverables

```text
app/streamlit_app.py
tests/test_ai_recommendation_observation_list_ui_integration_preflight.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-13.03_streamlit_observation_list_ui_integration_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm the app change is limited to the MS-13.03 observation-list section
  and forbidden modules remain unchanged.

### Completion Criteria

- The Streamlit app renders a section named `Observation List UI Preflight`.
- The section is fixture-based, observation-only, and read-only.
- The section references the MS-13.00 row builder, summary builder, and
  MS-13.02 hardening runner contract.
- Displayed fields remain limited to observation row fields.
- `status_badge` is not buy/sell/hold, `score_snapshot_label` is not a
  recommendation/ranking/action, `display_bucket` is not ranking/priority/
  order, and `usability_label` is not a ranking flag.
- No forbidden control, API, DB write, file loader, credential, accountSeq,
  actual recommendation, ranking, target price, expected return, or trade
  directive path is introduced.

### Next Step Candidate

```text
MS-13.04 Streamlit observation list UI AppTest hardening
```

## MS-13.04: Streamlit Observation List UI AppTest Hardening

### Purpose

Harden the MS-13.03 Streamlit observation-list UI section with AppTest and
static checks. This stage fixes the fixture-based observation-only section as a
read-only preflight display. It is not a live API integration, an actual
recommendation UI, a ranking table, or a buy/sell/hold workflow.

### Allowed Scope

- Add `tests/test_ai_recommendation_observation_list_ui_apptest_hardening.py`.
- Validate the existing MS-13.03 section with `streamlit.testing.v1.AppTest`.
- Use static checks to confirm the section title, fixture row preview,
  hardening reference, allowed observation fields, and forbidden UI element
  absence.
- Update this WBS, the endpoint matrix, and the MS-13.04 report.

### Forbidden Scope

- No `app/streamlit_app.py` change unless a rendering blocker is separately
  reported and approved.
- No Streamlit server, HTTP smoke, browser run, live/fake smoke, Toss API call,
  OAuth token endpoint call, OpenAI/LLM/API model call, credential input,
  accountSeq input, API refresh button, OAuth login button, new `st.button`,
  callback, session state, order/account/assets/balance/holdings/fills UI,
  new DB read/write, file read/write, feature loader, watchlist loader,
  fixture loader, actual recommendation, ranking, target price, expected
  return, profit probability, or trade directive path.

### Deliverables

```text
tests/test_ai_recommendation_observation_list_ui_apptest_hardening.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-13.04_streamlit_observation_list_ui_apptest_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm `app/streamlit_app.py` and existing MS-13.00 through MS-13.03
  contract modules remain unchanged.

### Completion Criteria

- AppTest renders the observation-list UI preflight section successfully.
- The section remains fixture-based, observation-only, read-only, and preflight
  scoped.
- Fixture row preview and hardening check reference are visible.
- Display fields remain limited to observation row fields.
- Forbidden UI elements, recommendation/action/ranking labels, buy/sell/hold
  controls, target price, expected return, profit probability, credential,
  accountSeq, API refresh, OAuth login, new button, callback, and session state
  paths are absent from the MS-13.03 section.
- `status_badge` is not buy/sell/hold, `score_snapshot_label` is not a
  recommendation/ranking/action, `display_bucket` is not ranking/priority/
  order, and `usability_label` is not a ranking flag.

### Next Step Candidate

```text
MS-14.00 Toss API client contract preflight
```

## MS-14.00: Toss API Client Contract Preflight

### Purpose

Define a pure no-I/O Toss API client contract before implementing any live
client behavior. This stage describes symbolic endpoint, request, response,
error, credential-name, redaction, and validation shapes only. It is not a live
Toss API call, OAuth token issuance, credential loading, account/balance/order/
fill lookup, OpenAI/LLM call, recommendation, ranking, or buy/sell/hold
workflow.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_client_contract.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_client_contract.py`.
- Define frozen dataclass contract models and deterministic validation helpers.
- Define symbolic endpoint contracts only; no concrete Toss URL or path.
- Define credential name policy only; no credential values or loaders.
- Define pure redaction helpers and raw-payload blocking policy.
- Update this WBS, the endpoint matrix, and the MS-14.00 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, environment,
  `.env.local`, credential, OAuth token endpoint, Access Token issuance,
  Authorization Bearer creation, accountSeq, account/assets/balance/holdings/
  fills/order, DB read/write, file read/write, OpenAI/LLM, Streamlit,
  recommendation, ranking, buy/sell/hold, target price, expected return, profit
  probability, live HTTP, smoke test, or client instance initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk, recommendation,
  README, pyproject, docs/28, data, or `.env` files.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_client_contract.py
tests/test_ai_clients_toss_api_client_contract.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-14.00_toss_api_client_contract_preflight_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, recommendation, storage, paper_trading, risk, README,
  pyproject, docs/28, data, and `.env` paths remain unchanged.

### Completion Criteria

- Contract policy includes no-network, no-OAuth, no-credential, no-accountSeq,
  no-order/account/balance/fill, no-DB, no-file-I/O, no-Streamlit, no-LLM,
  no-recommendation, and no-ranking flags.
- External capability flags remain false, including `live_http_ready=false`,
  `oauth_ready=false`, `credential_required_now=false`,
  `accountSeq_required_now=false`, `order_required_now=false`,
  `streamlit_required=false`, and `http_smoke_required=false`.
- Endpoint contracts are symbolic only and include no concrete URL/path.
- Request contracts are dry-run-only and `live_call_allowed=false`.
- Response contracts block raw payload output.
- Redaction helpers mask sensitive field values deterministically.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, or `.env.local`
  content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-14.01 Toss API fake transport / response fixtures
```

## MS-14.01: Toss API Fake Transport / Response Fixtures

### Purpose

Add a pure no-I/O fake transport and deterministic in-memory response fixture
layer on top of the MS-14.00 Toss API client contract. This stage provides
contract-safe previews only. It is not a live Toss API call, OAuth token
issuance, credential loading, accountSeq use, account/balance/order/fill
lookup, OpenAI/LLM call, recommendation, ranking, or buy/sell/hold workflow.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_fake_transport.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_fake_transport.py`.
- Reuse MS-14.00 contract policy, symbolic endpoint contract, redaction helper,
  sensitive-output validation, and contract preflight runner.
- Define frozen dataclass fake transport policy, symbolic fake request, fake
  response, fixture, runner result, and validation result models.
- Define in-memory response fixtures only.
- Update this WBS, the endpoint matrix, and the MS-14.01 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment, `.env.local`, credential values, accountSeq, account/assets/
  balance/holdings/fills/order, DB read/write, file read/write, OpenAI/LLM,
  Streamlit, recommendation, ranking, buy/sell/hold, target price, expected
  return, profit probability, live smoke, fake live smoke, HTTP smoke, or
  client instance initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk,
  recommendation, README, pyproject, docs/28, data, or `.env` files.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_fake_transport.py
tests/test_ai_clients_toss_api_fake_transport.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-14.01_toss_api_fake_transport_response_fixtures_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, recommendation, storage,
  paper_trading, risk, README, pyproject, docs/28, data, and `.env` paths
  remain unchanged.

### Completion Criteria

- Fake transport policy reuses the MS-14.00 contract and keeps no-network,
  no-OAuth, no-credential, no-accountSeq, no-order/account/balance/fill, no-DB,
  no-file-I/O, no-Streamlit, no-LLM, no-recommendation, and no-ranking flags.
- `fake_transport_ready=true`, while `live_http_ready=false`,
  `oauth_ready=false`, `credential_required_now=false`,
  `accountSeq_required_now=false`, `order_required_now=false`,
  `streamlit_required=false`, and `http_smoke_required=false`.
- Fake requests are symbolic and dry-run-only.
- Fake response fixtures are in-memory and expose redacted previews only.
- Raw payload, credential values, Access Token, Authorization Bearer,
  accountSeq, account/balance/order/fill data, DB row, file path, and
  `.env.local` content are not read, printed, stored, or committed.

### Next Step Candidate

```text
MS-14.02 credential/config redaction guardrail
```

## MS-14.02: Credential/Config Redaction Guardrail

### Purpose

Add a pure no-I/O credential/config redaction guardrail before any Toss API
live smoke work. This stage defines validation-only source policy, symbolic
credential field policy, readiness decision, redaction helpers, and preflight
checks. It does not read `.env.local`, `.env`, `.env.example`, environment
variables, credential values, files, DB rows, or live service responses.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_config_guardrail.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_config_guardrail.py`.
- Reuse MS-14.00 contract policy, credential-name policy, external capability
  flags, redaction helpers, sensitive-output validation, and contract preflight.
- Define frozen dataclass guardrail policy, source policy, field policy,
  redaction result, validation result, readiness decision, and preflight result.
- Update this WBS, the endpoint matrix, and the MS-14.02 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment read, `.env.local` read, `.env` read, `.env.example` creation,
  credential value input/read/output, accountSeq, account/assets/balance/
  holdings/fills/order, DB read/write, file read/write, OpenAI/LLM, Streamlit,
  recommendation, ranking, buy/sell/hold, target price, expected return, profit
  probability, live smoke, fake live smoke, HTTP smoke, or client instance
  initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk,
  recommendation, README, pyproject, docs/28, data, `.env`, `.env.local`, or
  `.env.example`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_config_guardrail.py
tests/test_ai_clients_toss_api_config_guardrail.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-14.02_credential_config_redaction_guardrail_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, MS-14.01 fake transport,
  recommendation, storage, paper_trading, risk, README, pyproject, docs/28,
  data, `.env`, `.env.local`, and `.env.example` paths remain unchanged.

### Completion Criteria

- Guardrail policy reuses the MS-14.00 contract and credential-name policy.
- Config sources remain symbolic, validation-only, and `read_now=false`.
- Credential field policies are name-only; values, raw output, print, log, and
  persist are all disallowed.
- Readiness decision keeps `credential_required_now=false`,
  `toss_key_required_now=false`, `toss_secret_required_now=false`,
  `openai_key_required_now=false`, `access_token_required_now=false`,
  `accountSeq_required_now=false`, `live_http_allowed_now=false`,
  `oauth_allowed_now=false`, and `safe_to_request_user_secret_now=false`.
- Sensitive dummy inputs are masked and safe previews do not expose raw values.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, `.env.local`, or
  `.env` content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-14.03 live-readiness checklist / no-secret dry run gate
```

## MS-14.03: Live-Readiness Checklist / No-Secret Dry Run Gate

### Purpose

Add a pure no-I/O live-readiness checklist and no-secret dry run gate before
any Toss API live smoke work. This stage aggregates MS-14.00 contract
preflight, MS-14.01 fake transport preflight, and MS-14.02 config guardrail
preflight results to decide whether live work may proceed now. The decision
keeps live smoke, secret requests, OAuth, live HTTP, accountSeq, order/account/
balance/fill capabilities, env reads, file I/O, DB access, OpenAI/LLM,
recommendation, ranking, and buy/sell/hold flows blocked until an explicit
future stage.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_live_readiness.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_live_readiness.py`.
- Reuse MS-14.00 contract preflight, MS-14.01 fake transport preflight, and
  MS-14.02 config guardrail preflight without modifying those modules.
- Define frozen dataclass policy, checklist item, gate decision, no-secret dry
  run result, and aggregate preflight result models.
- Update this WBS, the endpoint matrix, and the MS-14.03 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment read, `.env.local` read, `.env` read, `.env.example` creation or
  modification, credential value input/read/output, accountSeq, account/assets/
  balance/holdings/fills/order, DB read/write, file read/write, OpenAI/LLM,
  Streamlit, recommendation, ranking, buy/sell/hold, target price, expected
  return, profit probability, live smoke, fake live smoke, HTTP smoke, or
  client instance initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk,
  recommendation, README, pyproject, docs/28, data, `.env`, `.env.local`, or
  `.env.example`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_live_readiness.py
tests/test_ai_clients_toss_api_live_readiness.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-14.03_live_readiness_no_secret_dry_run_gate_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, MS-14.01 fake transport,
  MS-14.02 config guardrail, recommendation, storage, paper_trading, risk,
  README, pyproject, docs/28, data, `.env`, `.env.local`, and `.env.example`
  paths remain unchanged.

### Completion Criteria

- Live-readiness policy reuses the MS-14.00, MS-14.01, and MS-14.02 preflight
  layers.
- Checklist categories cover contract, fake transport, config guardrail,
  secret request/output, env read, file I/O, live HTTP, OAuth, accountSeq,
  order/account/balance/fills, DB, Streamlit, LLM, recommendation/ranking/
  action, and next-stage gate checks.
- Gate decision keeps `live_smoke_allowed_now=false`,
  `safe_to_request_user_secret_now=false`, `credential_required_now=false`,
  `toss_key_required_now=false`, `toss_secret_required_now=false`,
  `openai_key_required_now=false`, `access_token_required_now=false`,
  `oauth_allowed_now=false`, `live_http_allowed_now=false`,
  `accountSeq_allowed_now=false`, and `order_allowed_now=false`.
- No-secret dry run returns safe summary fields only and remains deterministic.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, `.env.local`,
  `.env`, or `.env.example` content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-15.00 first read-only live smoke planning
```

## MS-15.00: First Read-Only Live Smoke Planning

### Purpose

Define the scope, allow conditions, block conditions, prerequisites, and
execution gate for a future first read-only Toss API live smoke. This stage is
pure no-I/O planning only. It does not call Toss API, issue OAuth tokens, load
credentials, read `.env.local`, read `.env`, read environment variables, use
accountSeq, query account/balance/order/fill data, request an OpenAI key,
generate recommendations, rank candidates, or create buy/sell/hold decisions.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_live_smoke_plan.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_live_smoke_plan.py`.
- Reuse MS-14.00 contract preflight, MS-14.01 fake transport preflight,
  MS-14.02 config guardrail preflight, and MS-14.03 live-readiness preflight.
- Define frozen dataclass planning policy, symbolic read-only smoke target,
  allowlist, blocklist, prerequisite, execution gate, plan, and validation
  result models.
- Update this WBS, the endpoint matrix, and the MS-15.00 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment read, `.env.local` read, `.env` read, `.env.example` creation or
  modification, credential value input/read/output, accountSeq, account/assets/
  balance/holdings/fills/order, DB read/write, file read/write, OpenAI/LLM,
  Streamlit, recommendation, ranking, buy/sell/hold, target price, expected
  return, profit probability, live smoke execution, HTTP smoke, or client
  instance initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`, live client modules,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk, recommendation,
  README, pyproject, docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_live_smoke_plan.py
tests/test_ai_clients_toss_api_live_smoke_plan.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-15.00_first_readonly_live_smoke_planning_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, MS-14.01 fake transport,
  MS-14.02 config guardrail, MS-14.03 live-readiness, recommendation, storage,
  paper_trading, risk, README, pyproject, docs/28, data, `.env`,
  `.env.local`, and `.env.example` paths remain unchanged.

### Completion Criteria

- Planning policy is `planning_only=true` and keeps no-network, no-OAuth,
  no-credential-now, no-env-read, no-file-read/write, no-accountSeq,
  no-order/account/balance/fill, no-DB, no-Streamlit, no-LLM,
  no-recommendation, no-ranking, and no-live-HTTP-now flags true.
- Symbolic read-only smoke targets are market-data-only and keep
  `actual_url_defined=false`, `actual_endpoint_path_defined=false`,
  `live_call_allowed_now=false`, and `planning_only=true`.
- Execution gate keeps `planning_passed=true`,
  `live_execution_allowed_now=false`,
  `credential_request_allowed_now=false`, `oauth_allowed_now=false`,
  `token_issuance_allowed_now=false`, `accountSeq_allowed_now=false`,
  `order_allowed_now=false`, `account_data_allowed_now=false`,
  `balance_allowed_now=false`, `fills_allowed_now=false`,
  `openai_key_allowed_now=false`, `llm_allowed_now=false`, and
  `explicit_approval_required=true`.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, `.env.local`,
  `.env`, or `.env.example` content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-15.01 read-only live smoke disabled skeleton
```

## MS-15.01: Read-Only Live Smoke Disabled Skeleton

### Purpose

Add a pure no-I/O disabled skeleton for the future read-only Toss API live smoke
entry point. This stage proves the local skeleton can be invoked while still
blocking live execution, credential requests, OAuth, token issuance,
accountSeq, account/balance/order/fill access, DB/file/env access, OpenAI/LLM,
recommendation, ranking, and buy/sell/hold behavior.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_live_smoke_disabled.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_live_smoke_disabled.py`.
- Reuse MS-14.00 contract preflight, MS-14.01 fake transport preflight,
  MS-14.02 config guardrail preflight, MS-14.03 live-readiness preflight,
  MS-14.03 no-secret dry run, and MS-15.00 planning preflight.
- Define frozen dataclass disabled policy, request, decision, result, and
  validation result models.
- Update this WBS, the endpoint matrix, and the MS-15.01 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment read, `.env.local` read, `.env` read, `.env.example` creation or
  modification, credential value input/read/output, accountSeq, account/assets/
  balance/holdings/fills/order, DB read/write, file read/write, OpenAI/LLM,
  Streamlit, recommendation, ranking, buy/sell/hold, target price, expected
  return, profit probability, live smoke execution, HTTP smoke, or client
  instance initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`, live client modules,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk, recommendation,
  README, pyproject, docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_live_smoke_disabled.py
tests/test_ai_clients_toss_api_live_smoke_disabled.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-15.01_readonly_live_smoke_disabled_skeleton_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, MS-14.01 fake transport,
  MS-14.02 config guardrail, MS-14.03 live-readiness, MS-15.00 planning,
  recommendation, storage, paper_trading, risk, README, pyproject, docs/28,
  data, `.env`, `.env.local`, and `.env.example` paths remain unchanged.

### Completion Criteria

- Disabled policy is `disabled_skeleton_only=true`,
  `planning_gate_required=true`, `uses_ms_15_00_plan=true`, and keeps
  no-network, no-OAuth, no-credential-now, no-env-read, no-file-read/write,
  no-accountSeq, no-order/account/balance/fill, no-DB, no-Streamlit, no-LLM,
  no-recommendation, no-ranking, and no-live-HTTP-now flags true.
- Symbolic disabled request keeps `readonly=true`, `planning_only=true`,
  `disabled=true`, `live_call_attempted=false`, `credential_attached=false`,
  `token_attached=false`, `account_seq_attached=false`, and
  `raw_payload_attached=false`.
- Disabled decision keeps `skeleton_invocation_allowed=true`,
  `planning_gate_passed=true`, `live_execution_allowed_now=false`,
  `credential_request_allowed_now=false`, `oauth_allowed_now=false`,
  `token_issuance_allowed_now=false`, `account_seq_allowed_now=false`,
  `order_allowed_now=false`, `account_data_allowed_now=false`,
  `balance_allowed_now=false`, `fills_allowed_now=false`,
  `openai_key_allowed_now=false`, `llm_allowed_now=false`, and
  `explicit_approval_required=true`.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, `.env.local`,
  `.env`, or `.env.example` content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-15.02 read-only live smoke explicit approval gate
```

## MS-15.02: Read-Only Live Smoke Explicit Approval Gate

### Purpose

Add a pure no-I/O explicit approval gate for the future read-only Toss API live
smoke. This stage proves that the approval gate can be evaluated locally while
no explicit approval is present and live execution, credential requests, OAuth,
token issuance, env/file access, accountSeq, account/balance/order/fill access,
DB access, OpenAI/LLM, recommendation, ranking, and buy/sell/hold behavior
remain blocked.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_live_smoke_approval.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_live_smoke_approval.py`.
- Reuse MS-14.00 contract preflight, MS-14.01 fake transport preflight,
  MS-14.02 config guardrail preflight, MS-14.03 live-readiness preflight,
  MS-14.03 no-secret dry run, MS-15.00 planning preflight, and MS-15.01
  disabled skeleton preflight.
- Define frozen dataclass approval policy, intent, requirement, decision, gate
  result, and validation result models.
- Update this WBS, the endpoint matrix, and the MS-15.02 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment read, `.env.local` read, `.env` read, `.env.example` creation or
  modification, credential value input/read/output, accountSeq, account/assets/
  balance/holdings/fills/order, DB read/write, file read/write, OpenAI/LLM,
  Streamlit, recommendation, ranking, buy/sell/hold, target price, expected
  return, profit probability, live smoke execution, HTTP smoke, user signature
  capture, or client instance initialization.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`,
  `src/ai_stock/clients/toss_api_live_smoke_disabled.py`, live client modules,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk, recommendation,
  README, pyproject, docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_live_smoke_approval.py
tests/test_ai_clients_toss_api_live_smoke_approval.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-15.02_readonly_live_smoke_explicit_approval_gate_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, MS-14.01 fake transport,
  MS-14.02 config guardrail, MS-14.03 live-readiness, MS-15.00 planning,
  MS-15.01 disabled skeleton, recommendation, storage, paper_trading, risk,
  README, pyproject, docs/28, data, `.env`, `.env.local`, and `.env.example`
  paths remain unchanged.

### Completion Criteria

- Approval policy is `approval_gate_only=true`,
  `explicit_user_approval_required=true`, `disabled_skeleton_required=true`,
  `planning_gate_required=true`, `uses_ms_15_00_plan=true`, and
  `uses_ms_15_01_disabled_skeleton=true`.
- Symbolic approval intent keeps `readonly=true`, `planning_only=true`,
  `approval_recorded=false`, `live_call_requested=false`,
  `live_call_approved=false`, `credential_request_approved=false`,
  `oauth_approved=false`, `token_issuance_approved=false`,
  `account_seq_approved=false`, `order_approved=false`,
  `account_data_approved=false`, and `raw_payload_approved=false`.
- Approval decision keeps `approval_gate_invocation_allowed=true`,
  `planning_gate_passed=true`, `disabled_skeleton_passed=true`,
  `explicit_approval_present=false`, `live_execution_allowed_now=false`,
  `credential_request_allowed_now=false`, `env_read_allowed_now=false`,
  `file_read_allowed_now=false`, `oauth_allowed_now=false`,
  `token_issuance_allowed_now=false`, `account_seq_allowed_now=false`,
  `order_allowed_now=false`, `account_data_allowed_now=false`,
  `balance_allowed_now=false`, `fills_allowed_now=false`,
  `openai_key_allowed_now=false`, `llm_allowed_now=false`, and
  `gate_closed=true`.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, `.env.local`,
  `.env`, or `.env.example` content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-15.03 credential request timing policy
```

## MS-15.03: Credential Request Timing Policy

### Purpose

Define a pure no-I/O policy for when Toss API credentials may be requested in a
future stage. MS-15.03 records MS-16.00 as the first candidate for a separately
approved Toss credential request while proving that the current stage does not
request, read, load, use, print, or persist credentials and does not execute
OAuth, live HTTP, accountSeq, account/account/balance/fills/order, DB, OpenAI,
recommendation, ranking, or buy/sell/hold behavior.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_credential_timing.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_credential_timing.py`.
- Reuse MS-14.00 contract preflight, MS-14.01 fake transport preflight,
  MS-14.02 config guardrail preflight, MS-14.03 live-readiness preflight,
  MS-14.03 no-secret dry run, MS-15.00 planning preflight, MS-15.01 disabled
  skeleton preflight, and MS-15.02 explicit approval gate preflight.
- Define frozen dataclass timing policy, candidate stage, requirement, decision,
  result, and validation result models.
- Update this WBS, the endpoint matrix, and the MS-15.03 report.

### Forbidden Scope

- No `requests`, `httpx`, `aiohttp`, `urllib.request`, socket, live HTTP,
  OAuth token endpoint, Access Token issuance, Authorization Bearer creation,
  environment read, `.env.local` read, `.env` read, `.env.example` creation or
  modification, credential value input/read/output, accountSeq, account/assets/
  balance/holdings/fills/order, DB read/write, file read/write, OpenAI/LLM,
  Streamlit, recommendation, ranking, buy/sell/hold, target price, expected
  return, profit probability, live smoke execution, HTTP smoke, or credential
  prompt.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`,
  `src/ai_stock/clients/toss_api_live_smoke_disabled.py`,
  `src/ai_stock/clients/toss_api_live_smoke_approval.py`, live client modules,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk, recommendation,
  README, pyproject, docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_credential_timing.py
tests/test_ai_clients_toss_api_credential_timing.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-15.03_credential_request_timing_policy_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14.00 contract, MS-14.01 fake transport,
  MS-14.02 config guardrail, MS-14.03 live-readiness, MS-15.00 planning,
  MS-15.01 disabled skeleton, MS-15.02 approval gate, recommendation, storage,
  paper_trading, risk, README, pyproject, docs/28, data, `.env`, `.env.local`,
  and `.env.example` paths remain unchanged.

### Completion Criteria

- Timing policy is `credential_timing_policy_only=true`,
  `current_stage_requests_credentials=false`,
  `current_stage_reads_credentials=false`, `current_stage_uses_credentials=false`,
  `credential_required_now=false`, `toss_key_required_now=false`,
  `toss_secret_required_now=false`, `openai_key_required_now=false`,
  `access_token_required_now=false`, `safe_to_request_user_secret_now=false`,
  `live_execution_allowed_now=false`, and `credential_request_allowed_now=false`.
- Candidate stage is symbolic MS-16.00 read-only market data scope with
  `may_request_toss_credentials_later=true` only after explicit approval, while
  OpenAI key, accountSeq, and order scope remain unavailable.
- Timing decision keeps `timing_policy_invocation_allowed=true`,
  `approval_gate_passed=true`, all current-stage credential/env/OAuth/token/live
  HTTP/live execution/account/order/balance/fills/OpenAI/LLM flags false, and
  `ms_16_00_can_request_toss_credentials_after_explicit_approval=true`.
- No Toss API key, secret key, OpenAI key, Access Token, Authorization Bearer,
  accountSeq, raw response, raw request, raw DB row, DB file, `.env.local`,
  `.env`, or `.env.example` content is read, printed, stored, or committed.

### Next Step Candidate

```text
MS-16.00 first read-only Toss API live smoke
```

## MS-16.00: First Read-Only Toss API Live Smoke

### Purpose

Implement the first tightly gated read-only Toss API live smoke entrypoint after
MS-15.03 credential request timing policy. MS-16.00 permits checking only the
presence of approved local process environment names and attempts live HTTP only
when an explicit runtime approval object, redaction block, read-only scope, and
confirmed public/market-data endpoint candidate are all present.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_first_live_smoke.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_first_live_smoke.py`.
- Reuse MS-14.00 contract preflight, MS-14.01 fake transport preflight,
  MS-14.02 config guardrail preflight, MS-14.03 live-readiness/no-secret dry run,
  MS-15.00 planning preflight, MS-15.01 disabled skeleton preflight,
  MS-15.02 approval gate preflight, and MS-15.03 credential timing preflight.
- Allow process environment presence checks for `AI_STOCK_TOSS_API_KEY` and
  `AI_STOCK_TOSS_API_SECRET` only, returning booleans and redacted missing-name
  placeholders only.
- Allow only injected/fake executor testing and redacted HTTP result summaries.

### Forbidden Scope

- No accountSeq request/use, account assets, balance, fills, holdings, order
  scope, OpenAI key request, OpenAI/LLM call, Streamlit import, DB read/write,
  file read/write, `.env.local` read, `.env` read, `.env.example` creation or
  modification, credential value output, credential persistence, raw request
  output, raw response output, Access Token manual entry, Authorization Bearer
  manual entry, recommendation, ranking, buy/sell/hold action, target price,
  expected return, or profit probability.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`,
  `src/ai_stock/clients/toss_api_live_smoke_disabled.py`,
  `src/ai_stock/clients/toss_api_live_smoke_approval.py`,
  `src/ai_stock/clients/toss_api_credential_timing.py`, live client modules,
  `src/ai_stock/models/toss.py`, storage, paper trading, risk, recommendation,
  README, pyproject, docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Secret Handling

- Do not paste Toss key or secret values into ChatGPT.
- Do not echo, print, log, store, hash, fingerprint, suffix-mask, or commit
  credential values.
- If local setup is needed in a future approved run, use local process
  environment variables only:

```powershell
$env:AI_STOCK_TOSS_API_KEY = "<YOUR_TOSS_API_KEY>"
$env:AI_STOCK_TOSS_API_SECRET = "<YOUR_TOSS_API_SECRET>"
```

### Runtime Approval Conditions

Live HTTP remains blocked unless all of these are true:

- `explicit_user_approved_ms_16_00=true`
- `runtime_live_http_approved=true`
- `credential_request_approved=true`
- `readonly_scope_confirmed=true`
- `raw_output_block_confirmed=true`
- `no_account_scope_confirmed=true`
- `no_order_scope_confirmed=true`
- required credential presence booleans are true
- endpoint candidate is confirmed read-only market-data/public and executable
  without OAuth or account scope

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_first_live_smoke.py
tests/test_ai_clients_toss_api_first_live_smoke.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-16.00_first_readonly_toss_api_live_smoke_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14/MS-15 modules, recommendation, storage,
  paper_trading, risk, README, pyproject, docs/28, data, `.env`, `.env.local`,
  and `.env.example` paths remain unchanged.

### Completion Criteria

- Default run returns a blocked dry-run with `live_http_attempted=false`.
- Missing credentials, missing runtime approval, or unconfirmed endpoint keeps
  live HTTP unattempted.
- Injected fake executor can exercise the attempted case without raw request or
  raw response output.
- Decisions keep accountSeq/order/account/balance/fills/OpenAI/LLM/DB/
  Streamlit/recommendation/ranking/buy-sell-hold flags false and credentials
  redacted.

### Next Step Candidate

```text
MS-16.01 read-only live smoke result hardening
```

## MS-16.01: Read-Only Live Smoke Result Hardening

### Purpose

Harden the result and diagnostics path around the MS-16.00 first read-only Toss
API live smoke framework. MS-16.01 does not execute live HTTP and does not
request, read, load, print, or persist Toss credentials. It validates that only
safe result summaries and redacted diagnostics can be reported from blocked
dry-run and injected/fake executor paths.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_live_smoke_result_hardening.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_live_smoke_result_hardening.py`.
- Reuse MS-16.00 first live smoke policy, endpoint candidate, runtime approval,
  run, validation, and preflight helpers without modifying MS-16.00.
- Reuse MS-14/MS-15 preflight checks and redaction helpers without modifying
  their modules.
- Add safe HTTP summary, safe error summary, redaction probe, hardening decision,
  hardening result, and validation result dataclass shapes.

### Forbidden Scope

- No live HTTP, HTTP smoke, Toss API call, network access, OAuth token endpoint,
  Access Token issuance, Authorization Bearer creation/output, Toss key/secret
  request, OpenAI key request, credential value read/output, environment read,
  `.env.local` read, `.env` read, `.env.example` creation/modification,
  accountSeq, account/assets/balance/holdings/fills/order scope, DB read/write,
  file read/write, Streamlit import, OpenAI/LLM call, recommendation, ranking,
  buy/sell/hold, target price, expected return, profit probability, raw request,
  raw response, raw DB row, endpoint URL output, or raw traceback output.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`,
  `src/ai_stock/clients/toss_api_live_smoke_disabled.py`,
  `src/ai_stock/clients/toss_api_live_smoke_approval.py`,
  `src/ai_stock/clients/toss_api_credential_timing.py`,
  `src/ai_stock/clients/toss_api_first_live_smoke.py`, live client modules,
  storage, paper trading, risk, recommendation, README, pyproject, docs/28,
  data, `.env`, `.env.local`, or `.env.example`.

### Result Hardening Scope

- Preserve `live_http_execution_allowed=false`.
- Preserve `credential_request_allowed=false`.
- Preserve `raw_request_output_allowed=false` and
  `raw_response_output_allowed=false`.
- Preserve account/order/balance/fills/OpenAI/LLM/DB/Streamlit/recommendation/
  ranking/buy-sell-hold false decision flags.

### Safe HTTP Summary

Allowed fields are `attempted`, `status_code`, `success`, `error_category`,
`response_shape_summary`, `elapsed_ms`, `diagnostics_kind`, and
`redaction_applied=true`. Raw URL, headers, request body, response body,
Authorization, token, credential, accountSeq, and account/order/balance/fills
data remain blocked.

### Safe Error Summary

Allowed fields are `error_category`, `safe_error_code`, `retryable`,
`operator_action`, and `redacted_message`. Raw exception text, raw traceback,
endpoint URL, Authorization header, token, credential, accountSeq, and raw
payload remain blocked.

### Redaction Probe

Synthetic forbidden probe inputs are checked only inside validation. Hardening
results return safe probe labels, counts, placeholder metadata, and whether raw
probe validation failure was observed; raw synthetic inputs are not returned in
result, decision, or safe diagnostics.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_live_smoke_result_hardening.py
tests/test_ai_clients_toss_api_live_smoke_result_hardening.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-16.01_readonly_live_smoke_result_hardening_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14/MS-15/MS-16.00 modules, recommendation,
  storage, paper_trading, risk, README, pyproject, docs/28, data, `.env`,
  `.env.local`, and `.env.example` paths remain unchanged.

### Completion Criteria

- Hardening decision keeps `hardening_invocation_allowed=true`,
  `ms_16_00_preflight_passed=true`, `live_http_execution_allowed=false`,
  `credential_request_allowed=false`, `raw_request_output_allowed=false`,
  `raw_response_output_allowed=false`, `credentials_redacted=true`,
  `safe_http_summary_allowed=true`, `safe_error_summary_allowed=true`, and
  `redaction_probe_passed=true`.
- Forbidden synthetic strings fail validation if they appear in safe output.
- Safe result reports only status code, elapsed ms, response shape summary,
  error category, safe diagnostics kind, and redacted summary metadata.

### Next Step Candidate

```text
MS-16.02 confirmed read-only endpoint selection
```

## MS-16.02: Confirmed Read-Only Endpoint Selection

### Purpose

Add a pure no-I/O policy for selecting a confirmed read-only/public market-data
endpoint candidate for a later live smoke. MS-16.02 does not execute live HTTP,
does not request or read Toss credentials, does not issue OAuth tokens, does not
use accountSeq, and does not touch account/order/balance/fills, OpenAI/LLM,
recommendation, ranking, or buy/sell/hold paths.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_readonly_endpoint_selection.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_readonly_endpoint_selection.py`.
- Reuse MS-16.00 first live smoke preflight and validation helpers without
  modifying MS-16.00.
- Reuse MS-16.01 result hardening preflight and validation helpers without
  modifying MS-16.01.
- Reuse MS-14/MS-15 preflight checks and redaction helpers without modifying
  those modules.
- Model endpoint evidence, candidate, selection decision, selection result, and
  validation result as frozen dataclasses.

### Forbidden Scope

- No live HTTP, HTTP smoke, Toss API call, network access, OAuth token endpoint,
  Access Token issuance, Authorization Bearer creation/output, Toss key/secret
  request, OpenAI key request, credential value read/output, environment read,
  `.env.local` read, `.env` read, `.env.example` creation/modification,
  accountSeq, account/assets/balance/holdings/fills/order scope, DB read/write,
  file read/write, Streamlit import, OpenAI/LLM call, recommendation, ranking,
  buy/sell/hold, target price, expected return, profit probability, raw request,
  raw response, raw DB row, endpoint full URL output, or unconfirmed endpoint
  path creation.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`,
  `src/ai_stock/clients/toss_api_live_smoke_disabled.py`,
  `src/ai_stock/clients/toss_api_live_smoke_approval.py`,
  `src/ai_stock/clients/toss_api_credential_timing.py`,
  `src/ai_stock/clients/toss_api_first_live_smoke.py`,
  `src/ai_stock/clients/toss_api_live_smoke_result_hardening.py`, live client
  modules, storage, paper trading, risk, recommendation, README, pyproject,
  docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Endpoint Selection Criteria

An endpoint candidate can be selected only when all of these symbolic evidence
conditions are true:

- `endpoint_confirmed=true`
- `readonly=true`
- `market_data_only=true` or `public_or_market_data=true`
- `requires_account_seq=false`
- `requires_order_scope=false`
- `requires_account_balance_fills=false`
- `requires_oauth_token=false`
- `live_http_executable_without_oauth=true`
- `allows_raw_payload_output=false`
- evidence confirms read-only scope, no accountSeq, no order scope, no
  account/balance/fills scope, no OAuth requirement for the smoke, and raw
  output blocking

### Rejected Candidate Conditions

Candidates are rejected when confirmation is missing, the candidate requires
accountSeq, order scope, account/balance/fills scope, OAuth token issuance, raw
payload output, or cannot be executed later without OAuth. Rejected candidates
remain symbolic metadata only and do not trigger live HTTP.

### Selected Endpoint Conditions

If no existing project reference or symbolic contract confirms a candidate,
MS-16.02 returns a safe blocked result with no selected endpoint. The default
candidate is deliberately unconfirmed until a later stage supplies confirmed
project-local evidence.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_readonly_endpoint_selection.py
tests/test_ai_clients_toss_api_readonly_endpoint_selection.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-16.02_confirmed_readonly_endpoint_selection_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14/MS-15/MS-16.00/MS-16.01 modules,
  recommendation, storage, paper_trading, risk, README, pyproject, docs/28,
  data, `.env`, `.env.local`, and `.env.example` paths remain unchanged.

### Completion Criteria

- Default selection is blocked with no selected endpoint because the default
  candidate is unconfirmed.
- Confirmed symbolic read-only/public market-data candidates can be selected
  only when all evidence and safety flags pass.
- Rejected candidate conditions keep selection blocked and leave
  `live_http_execution_allowed_now=false`, `credential_request_allowed_now=false`,
  OAuth/token/account/order/balance/fills/OpenAI/LLM/DB/Streamlit/recommendation/
  ranking/buy-sell-hold flags false, raw request/response output false, and
  endpoint full URL output false.

### Next Step Candidate

```text
MS-16.03 live smoke operator runbook / runtime approval rehearsal
```

## MS-16.03: Live Smoke Operator Runbook / Runtime Approval Rehearsal

### Purpose

Add a pure no-I/O operator runbook and runtime approval rehearsal model after
MS-16.00 first live smoke, MS-16.01 result hardening, and MS-16.02 endpoint
selection. MS-16.03 documents and validates the prerequisite, approval, stop,
and runbook-step shape that must exist before any future live HTTP smoke, while
preserving the current MS-16.02 state: no selected endpoint,
`selection_blocked=true`, and `candidate_ineligible`.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_live_smoke_operator_runbook.py`.
- Add public exports in `src/ai_stock/clients/__init__.py`.
- Add `tests/test_ai_clients_toss_api_live_smoke_operator_runbook.py`.
- Reuse MS-16.00 first live smoke preflight/validation helpers without modifying
  MS-16.00.
- Reuse MS-16.01 result hardening preflight/validation helpers without modifying
  MS-16.01.
- Reuse MS-16.02 endpoint selection preflight/validation helpers without
  modifying MS-16.02.
- Model operator policy, prerequisite, runtime approval checklist, stop
  condition, runbook step, rehearsal decision, rehearsal result, and validation
  result as frozen dataclasses.

### Forbidden Scope

- No live HTTP, HTTP smoke, Toss API call, network access, OAuth token endpoint,
  Access Token issuance, Authorization Bearer creation/output, Toss key/secret
  request, OpenAI key request, credential value read/output, credential presence
  inspection, environment read, `.env.local` read, `.env` read, `.env.example`
  creation/modification, accountSeq, account/assets/balance/holdings/fills/order
  scope, DB read/write, file read/write, Streamlit import, OpenAI/LLM call,
  recommendation, ranking, buy/sell/hold, target price, expected return, profit
  probability, raw request, raw response, raw DB row, endpoint full URL output,
  unconfirmed endpoint path creation, actual execution command generation, or
  live smoke CLI implementation.
- No changes to `app/streamlit_app.py`, `scripts/dev_check.py`,
  `src/ai_stock/clients/toss_api_client_contract.py`,
  `src/ai_stock/clients/toss_api_fake_transport.py`,
  `src/ai_stock/clients/toss_api_config_guardrail.py`,
  `src/ai_stock/clients/toss_api_live_readiness.py`,
  `src/ai_stock/clients/toss_api_live_smoke_plan.py`,
  `src/ai_stock/clients/toss_api_live_smoke_disabled.py`,
  `src/ai_stock/clients/toss_api_live_smoke_approval.py`,
  `src/ai_stock/clients/toss_api_credential_timing.py`,
  `src/ai_stock/clients/toss_api_first_live_smoke.py`,
  `src/ai_stock/clients/toss_api_live_smoke_result_hardening.py`,
  `src/ai_stock/clients/toss_api_readonly_endpoint_selection.py`, live client
  modules, storage, paper trading, risk, recommendation, README, pyproject,
  docs/28, data, `.env`, `.env.local`, or `.env.example`.

### Operator Runbook Scope

- Capture symbolic runbook steps only.
- Keep `execute_live_http_smoke.allowed_now=false`.
- Keep `collect_runtime_approval` as a rehearsal item, not actual approval
  collection.
- Do not create command strings, endpoint URLs, credential prompts, or live
  smoke CLI behavior.

### Runtime Approval Rehearsal Scope

- Default approval checklist has no explicit live HTTP approval.
- Default approval checklist has no selected endpoint.
- Default approval checklist keeps account, order, balance, fills, accountSeq,
  OAuth token issuance, raw output, OpenAI key, and LLM scope blocked.
- `approval_rehearsal_passed=false`.

### Prerequisite

Required prerequisites include confirmed endpoint selection, MS-16.00 framework
availability, MS-16.01 hardening availability, MS-16.02 selection availability,
runtime approval rehearsal, local-session credential rule, raw output block,
account scope block, order scope block, OAuth token scope block, environment
file usage block, and no OpenAI/LLM scope.

### Stop Condition

Stop conditions include missing selected endpoint, blocked endpoint selection,
endpoint accountSeq requirement, endpoint order requirement, endpoint OAuth token
requirement, raw response exposure, credential value exposure, environment file
requirement, account/balance/fills scope, OpenAI/LLM scope, and
recommendation/trading action scope. The default rehearsal triggers
`selected_endpoint_missing` and `endpoint_selection_blocked`.

### Runbook Step

Runbook steps are symbolic only: verify main commit, verify MS-16.00 preflight,
verify MS-16.01 hardening, verify MS-16.02 endpoint selection, verify selected
endpoint, collect runtime approval rehearsal, require local-session credentials,
block environment files, block raw output, block account scope, block order
scope, block OAuth token scope, and keep live HTTP smoke execution blocked.

### Rehearsal Blocked Conditions

The rehearsal remains blocked while selected endpoint is missing or endpoint
selection is blocked. With the current MS-16.02 default, `rehearsal_blocked=true`
and blocking reasons include `selected_endpoint_missing` and
`endpoint_selection_blocked`.

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_live_smoke_operator_runbook.py
tests/test_ai_clients_toss_api_live_smoke_operator_runbook.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-16.03_live_smoke_operator_runbook_rehearsal_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`
- Confirm app, dev_check, MS-14/MS-15/MS-16.00/MS-16.01/MS-16.02 modules,
  recommendation, storage, paper_trading, risk, README, pyproject, docs/28,
  data, `.env`, `.env.local`, and `.env.example` paths remain unchanged.

### Completion Criteria

- Default rehearsal returns a safe blocked result with no selected endpoint.
- Decision keeps `operator_runbook_invocation_allowed=true`,
  `runtime_approval_rehearsal_only=true`, MS-16.00/MS-16.01/MS-16.02 preflight
  flags true, `selected_endpoint_available=false`,
  `endpoint_selection_blocked=true`, and `rehearsal_blocked=true`.
- Runtime execution, credential request, env read, OAuth/token issuance,
  accountSeq, order/account/balance/fills, OpenAI/LLM, DB/Streamlit,
  recommendation/ranking/buy-sell-hold, raw request/response, endpoint full URL,
  and execution command output remain blocked.

### Next Step Candidate

```text
MS-16.04 confirmed endpoint evidence update
or
MS-16.04 live smoke dry-run command contract
```

MS-16.04 confirmed endpoint evidence update
-------------------------------------------

## MS-16.04: Confirmed Endpoint Evidence Update

### Purpose

MS-16.04 updates the MS-16 live-smoke chain with a pure no-I/O confirmed
endpoint evidence policy. The stage resolves the MS-16.02 default selected
endpoint gap by modeling a single symbolic read-only public/market-data
candidate backed by existing official/project evidence, while keeping all live
runtime gates closed.

### Allowed Scope

- Add `src/ai_stock/clients/toss_api_confirmed_endpoint_evidence.py`.
- Add `tests/test_ai_clients_toss_api_confirmed_endpoint_evidence.py`.
- Export only public dataclasses and helper functions from
  `src/ai_stock/clients/__init__.py`.
- Update `references/endpoint_matrix.md`.
- Add `reports/MS-16.04_confirmed_endpoint_evidence_update_report.md`.
- Reuse MS-16.00 first live smoke preflight.
- Reuse MS-16.01 result hardening preflight.
- Reuse MS-16.02 endpoint selection preflight.
- Reuse MS-16.03 operator rehearsal preflight.

### Forbidden Scope

- No actual live HTTP execution.
- No Toss credential request, credential loading, or credential presence check.
- No environment variable read and no environment file read.
- No OAuth token issuance, Access Token creation, or Authorization Bearer
  construction.
- No accountSeq, account, order, balance, fills, DB, Streamlit, OpenAI/LLM,
  recommendation, ranking, or buy/sell/hold scope.
- No endpoint full URL output, raw endpoint path output, raw request output, raw
  response output, or execution command generation.
- No changes to app, dev_check, MS-14/MS-15/MS-16.00/MS-16.01/MS-16.02/MS-16.03
  modules, recommendation modules, storage, paper_trading, risk, README,
  pyproject, docs/28, data, or environment files.

### Endpoint Evidence Criteria

The selected endpoint candidate must be symbolic and must satisfy all of the
following:

- Official or project evidence is available.
- Read-only behavior is confirmed.
- Public or market-data scope is confirmed.
- accountSeq is not required.
- Order scope is not required.
- Account, balance, and fills scope are not required.
- OAuth token issuance is not required for this evidence update stage.
- Raw request and raw response output are blocked.
- Endpoint full URL and raw path are not emitted.

### Selected Endpoint Success Conditions

The default MS-16.04 candidate is a symbolic Prices single-symbol read-only
market-data endpoint candidate. MS-16.04 marks it selected only as an evidence
record for the later MS-16.05 live-smoke stage:

- `endpoint_evidence_confirmed=true`
- `selected_endpoint_id` is not `None`
- `selected_endpoint_confirmed=true`
- `selected_endpoint_readonly=true`
- `selected_endpoint_public_or_market_data=true`
- `selected_endpoint_requires_account_seq=false`
- `selected_endpoint_requires_order_scope=false`
- `selected_endpoint_requires_account_balance_fills=false`
- `selected_endpoint_requires_oauth_token=false`
- `selected_endpoint_allows_raw_payload_output=false`
- `selection_blocked=false`

### Blocked Conditions

MS-16.04 returns a safe blocked result if evidence is absent or the candidate is
not eligible:

- `selected_endpoint_id=None`
- `endpoint_evidence_confirmed=false`
- `selection_blocked=true`
- `blocking_reasons` includes `confirmed_endpoint_evidence_missing` or
  `candidate_ineligible`

### Deliverables

```text
src/ai_stock/clients/__init__.py
src/ai_stock/clients/toss_api_confirmed_endpoint_evidence.py
tests/test_ai_clients_toss_api_confirmed_endpoint_evidence.py
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-16.04_confirmed_endpoint_evidence_update_report.md
```

### Verification

- `python -m compileall -q src tests app`
- `python -m unittest discover -s tests`
- `python -m pytest`
- `python scripts/dev_check.py`
- `ruff check src tests app`
- `git diff --check`
- `git status --short`

If standalone ruff is blocked by Windows Application Control, record it as an
OS/tool execution policy known warning and do not bypass it.

### Completion Criteria

- Confirmed endpoint evidence policy is deterministic and pure no-I/O.
- Default symbolic selected endpoint is confirmed for MS-16.05 candidacy.
- Evidence-missing and ineligible-candidate paths fail closed.
- MS-16.00, MS-16.01, MS-16.02, and MS-16.03 preflights are reused.
- Live HTTP, credentials, env read, OAuth/token issuance, accountSeq, account,
  order, balance, fills, DB, Streamlit, OpenAI/LLM, recommendation, ranking, and
  buy/sell/hold remain blocked.
- Safe diagnostics contain only counts, symbolic selected endpoint id/label,
  evidence confirmed flag, selection blocked flag, blocking reason ids, and
  redaction status.

### Next Stage Candidate

```text
MS-16.05 first actual read-only live HTTP smoke
```
