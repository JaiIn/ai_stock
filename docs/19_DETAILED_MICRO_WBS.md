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
| MS-02.02 | HTTP client skeleton | src/ai_stock/toss_api/client.py | client init test | timeout/retry 기본값 확인 |
| MS-02.03 | OAuth token 모델 | src/ai_stock/toss_api/auth_models.py | response parsing test | token 저장 방식 확인 |
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
| MS-03.01 | DB 설정 | src/ai_stock/db/session.py | SQLite connect test | DB 파일 위치 확인 |
| MS-03.02 | Base Model/metadata | src/ai_stock/db/base.py | metadata create test | naming convention 확인 |
| MS-03.03 | Watchlist 모델 | src/ai_stock/db/models/watchlist.py | table create test | 관심종목 필드 확인 |
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
| MS-04.01 | 관심종목 수집 서비스 | src/ai_stock/services/watchlist_service.py | CRUD service test | 관심종목 입력 방식 확인 |
| MS-04.02 | 시세 조회 service | src/ai_stock/services/market_data_service.py | mock client test | API 호출 범위 확인 |
| MS-04.03 | 캔들 조회 service | src/ai_stock/services/candle_service.py | fixture test | timeframe 확인 |
| MS-04.04 | 종목 경고 조회 service | src/ai_stock/services/stock_warning_service.py | warning filter test | 경고 종목 제외 기준 확인 |
| MS-04.05 | 환율/시장 정보 service | src/ai_stock/services/market_info_service.py | fixture test | 국내/미국 구분 확인 |
| MS-04.06 | Snapshot 저장 job | src/ai_stock/jobs/snapshot_job.py | job dry run | 자동 실행 여부 확인 |
| MS-04.07 | M4 통합 체크 | reports/stage-gates/M4-completion-checklist.md | service tests pass | M5 진행 승인 대기 |

---

## M5 — AI 추천 엔진

| Micro Stage | 작업 | 변경 범위 | 테스트/검증 | 사용자 확인 포인트 |
|---|---|---|---|---|
| MS-05.01 | 추천 입력 DTO | src/ai_stock/recommendation/schemas.py | schema test | 입력 데이터 범위 확인 |
| MS-05.02 | 기술지표 계산 1차 | src/ai_stock/recommendation/indicators.py | MA/return test | 지표 범위 확인 |
| MS-05.03 | 기술지표 계산 2차 | src/ai_stock/recommendation/indicators.py | RSI/volatility test | 지표 추가 승인 |
| MS-05.04 | Rule-based scoring | src/ai_stock/recommendation/scoring.py | score test | 점수 기준 확인 |
| MS-05.05 | Risk penalty | src/ai_stock/recommendation/risk_filter.py | warning penalty test | 경고 종목 처리 확인 |
| MS-05.06 | 추천 결과 ranking | src/ai_stock/recommendation/ranking.py | ranking test | top N 확인 |
| MS-05.07 | LLM prompt template | src/ai_stock/recommendation/prompts.py | prompt snapshot test | 문구/면책 표현 확인 |
| MS-05.08 | LLM provider abstraction | src/ai_stock/llm/provider.py | fake provider test | 실제 LLM API Key 필요 여부 확인 |
| MS-05.09 | AI 설명 생성 | src/ai_stock/recommendation/explainer.py | fake explanation test | 설명 톤 확인 |
| MS-05.10 | 금지 표현 guardrail | src/ai_stock/recommendation/guardrails.py | banned phrase test | 투자 조언 오해 방지 확인 |
| MS-05.11 | 추천 이력 저장 | src/ai_stock/services/recommendation_service.py | DB save test | 이력 보관 확인 |
| MS-05.12 | M5 통합 체크 | reports/stage-gates/M5-completion-checklist.md | recommendation tests pass | M6 진행 승인 대기 |

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
