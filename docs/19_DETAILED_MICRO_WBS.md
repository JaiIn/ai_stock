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
