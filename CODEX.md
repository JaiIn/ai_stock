# CODEX 실행 지침

이 문서는 Codex가 프로젝트를 구현할 때 최우선으로 따라야 하는 운영 지침이다.


## 0. 최우선 실행 규칙 — 단계별 완료 후 사용자 명령 대기

Codex는 이 프로젝트를 진행할 때 **한 단계가 끝날 때마다 멈춰야 한다.**

각 Phase 또는 Milestone 완료 후 반드시 다음을 수행한다.

1. `reports/stage-gates/`에 단계 완료 체크리스트를 작성한다.
2. 구현 요약, 테스트 결과, 생성/수정 파일, 남은 이슈를 기록한다.
3. 사용자 입력이 필요한 값이 있는지 명확히 판단한다.
4. 실제 토큰, API Key, Client Secret, 계좌 정보, accountSeq, 실 API 호출 승인이 필요하면 사용자에게 알리고 대기한다.
5. 다음 단계 후보를 제시하되, 사용자의 명시적인 명령 전에는 다음 단계로 진행하지 않는다.

필수 참조 문서:

- `docs/17_STAGE_GATE_AND_USER_APPROVAL.md`
- `templates/stage_completion_checklist_template.md`
- `templates/user_input_request_template.md`

예시:

```text
M2 Toss API Client mock 테스트는 완료했습니다.
실제 OAuth2 토큰 발급 테스트를 진행하려면 Toss API Client ID/Secret이 필요합니다.
.env에 값을 입력한 뒤 `설정 완료, 계속 진행`이라고 알려주세요.
사용자 명령을 기다립니다.
```




## 0.1 초세분화 Micro Stage 실행 규칙

이 프로젝트는 한 번에 너무 많은 변화가 생기지 않도록 **Micro Stage 단위**로만 진행한다.

기본 원칙:

```text
사용자 명령 1회 = Micro Stage 1개 수행 = 완료 보고 후 대기
```

Codex는 Milestone 전체를 한 번에 구현하지 않는다. `docs/19_DETAILED_MICRO_WBS.md`의 Micro Stage 순서에 따라 하나씩 구현한다.

각 Micro Stage 완료 시 반드시 수행한다.

1. `reports/micro-stages/MS-xx.xx-<name>.md` 작성
2. 관련 테스트 실행 및 `reports/test-results/MS-xx.xx-*` 저장
3. 구현 리포트 작성 또는 갱신
4. 사용자 입력/승인 필요 여부 판단
5. 다음 Micro Stage 후보 1개만 제시
6. 아래 문구로 종료

```text
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

사용자가 `계속`, `다음 단계 진행`이라고 말해도 다음 Micro Stage **1개만** 진행한다. 여러 단계를 묶어서 진행하려면 사용자가 명시적으로 허용해야 하며, 그 경우에도 최대 3개까지만 허용한다.

즉시 중단해야 하는 상황:

- Toss API Client ID/Secret, Access Token, accountSeq, OpenAI API Key 등 실제 값 필요
- 실제 Toss API 호출 필요
- DB 구조 변경 또는 기존 데이터 영향 가능성 있음
- 실주문 관련 설정 또는 코드 경로 변경 가능성 있음
- 테스트 실패
- 민감정보 로그 노출 가능성 발견

필수 추가 참조 문서:

- `docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md`
- `docs/19_DETAILED_MICRO_WBS.md`
- `docs/20_CODEX_STOP_AND_CONFIRMATION_RULES.md`
- `templates/micro_stage_completion_checklist_template.md`
- `templates/user_approval_request_template.md`
- `templates/development_status_board_template.md`




## 0.2 로컬 전용 실행 최우선 규칙

이 프로젝트는 v0.1에서 배포를 고려하지 않는다. Codex는 로컬 실행만 고려한다.

허용:

```text
127.0.0.1
localhost
SQLite local file
local logs
local reports
.env.local
```

금지:

```text
0.0.0.0 바인딩
Dockerfile / docker-compose.yml
Nginx / reverse proxy
Cloud deploy
external DB
public URL
사용자 인증/다중 사용자 기능
```

필수 참조 문서:

- `docs/21_TECH_STACK_AND_API_SCOPE.md`
- `docs/22_PROJECT_SETUP_AND_USAGE_GUIDE.md`
- `docs/23_LOCAL_ONLY_EXECUTION_POLICY.md`
- `docs/24_FRONTEND_FRAMEWORK_DECISION.md`

로컬 실행 기본 명령:

```bash
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```


## 0.3 역할별 Codex 세션 분리 규칙

사용자는 여러 Codex 세션을 역할별로 나누어 사용할 수 있다. Codex는 자기 세션의 역할 문서에 정의된 파일 범위만 수정한다.

역할 문서:

- `roles/00_ROLE_INDEX.md`
- `roles/01_PM_INTEGRATOR_SESSION.md`
- `roles/02_BACKEND_API_CLIENT_SESSION.md`
- `roles/03_FRONTEND_UI_SESSION.md`
- `roles/04_DATA_DB_SESSION.md`
- `roles/05_AI_RECOMMENDATION_SESSION.md`
- `roles/06_PAPER_TRADING_RISK_SESSION.md`
- `roles/07_QA_TEST_LOGGING_SESSION.md`
- `roles/08_DOCS_GUIDE_SESSION.md`
- `roles/09_GIT_VERSION_CONTROL_SESSION.md`

다른 역할의 파일 수정이 필요하면 직접 수정하지 말고 아래 위치에 인수인계 문서를 작성한다.

```text
reports/session-handoff/
```

필수 참조 문서:

- `docs/25_CODEX_MULTI_SESSION_ROLE_PROCESS.md`


## 0.4 프론트엔드/백엔드 경계 규칙

프론트엔드는 v0.1에서 Streamlit을 사용한다. 단, Streamlit은 UI 전용이다.

Streamlit에서 허용:

- 화면 렌더링
- 사용자 입력 수집
- service layer 호출
- 결과 표시

Streamlit에서 금지:

- Toss API 직접 호출
- SQLite 직접 접근
- 추천 점수 직접 계산
- 모의체결 직접 수행
- 실주문 관련 경로 구현

백엔드 핵심 로직은 `src/ai_stock/` 하위 패키지에 둔다.


## 0.5 프로젝트명 및 GitHub Repository 규칙

프로젝트명은 반드시 `ai_stock`으로 사용한다.

```text
Project Name: ai_stock
Python package: src/ai_stock/
GitHub Repository: https://github.com/JaiIn/ai_stock
Execution: local only
Deployment: none
```

Codex는 이전 이름이나 임시 이름을 새 코드/문서에 사용하지 않는다.

GitHub 작업은 Micro Stage 단위로만 수행한다.

```text
Micro Stage 1개 완료
→ 테스트 실행
→ reports/ 작성
→ git status/diff 확인
→ commit 후보 생성
→ push는 사용자 승인 후만 수행
→ 다음 명령 대기
```

절대 금지:

- 사용자 승인 없는 `git push`
- 사용자 승인 없는 `git rebase`
- 사용자 승인 없는 `git reset --hard`
- 사용자 승인 없는 `git push --force`
- `main` 브랜치 직접 작업
- `.env.local`, token, secret, DB, 로그 원문 commit

필수 참조 문서:

- `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
- `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
- `templates/git_commit_checklist_template.md`
- `templates/git_push_approval_request_template.md`

## 1. 목표

토스증권 Open API를 이용해 다음 기능을 가진 개인용 앱을 만든다.

- 관심종목 등록
- 토스증권 API 인증
- 현재가/호가/체결/캔들/상하한가 조회
- 종목 기본 정보와 매수 유의사항 조회
- 환율과 국내/미국 장 운영 시간 조회
- 계좌 목록, 보유 주식, 매수 가능 금액, 판매 가능 수량, 수수료 조회
- AI 기반 종목 분석/추천 설명 생성
- 모의 포트폴리오, 모의 주문, 체결 시뮬레이션, 손익 추적
- 테스트 결과/에러 로그/구현 리포트 자동 생성

## 2. 절대 금지

- 단계 완료 후 사용자의 명시적인 명령 없이 다음 단계로 넘어가지 말 것.
- 사용자 승인 없이 GitHub에 push하지 말 것.
- 사용자 승인 없이 main 브랜치에 직접 커밋하지 말 것.
- 실제 토큰, API Key, Client Secret, 계좌 정보가 필요할 때 임의값으로 대체하지 말고 사용자에게 입력을 요청한 뒤 대기할 것.
- 사용자 입력이 필요한 상태를 무시하고 live API 테스트를 진행하지 말 것.
- v0.1에서 실제 주문 생성/정정/취소를 실행하지 말 것.
- v0.1에서 배포/클라우드/외부 접속 구조를 만들지 말 것.
- v0.1에서 Docker, Nginx, PostgreSQL, Redis, Celery를 임의로 도입하지 말 것.
- `POST /api/v1/orders`, `POST /api/v1/orders/{orderId}/modify`, `POST /api/v1/orders/{orderId}/cancel`을 실제 계좌에 보내지 말 것.
- API Secret, Access Token, 계좌번호, accountSeq 원문을 로그에 남기지 말 것.
- AI 응답만 믿고 주문 판단을 하지 말 것.
- 금융 데이터 계산에 `float`를 사용하지 말 것. `Decimal`을 사용하라.
- 테스트 없이 기능 완료로 표시하지 말 것.

## 3. 구현 우선순위

### Phase 0 — 프로젝트 뼈대

- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.env.example`, `.gitignore`, `Makefile`
- `src/`, `tests/`, `logs/`, `reports/`, `data/` 디렉토리
- 설정 로더, 로깅, secret masking

### Phase 1 — Toss API read-only client

- OAuth2 token 발급
- token cache / expiry refresh
- rate limit retry
- request id logging
- read-only endpoints 구현
- fixture 기반 contract test

### Phase 2 — 데이터 저장

- SQLite DB
- watchlist, price_snapshot, candles, stock_info_cache, account_snapshot, holdings_snapshot
- paper_portfolio, paper_order, paper_position, recommendation_run

### Phase 3 — 추천 엔진

- rule-based score
- 리스크 필터
- 경고 종목 제외/감점
- LLM 설명 생성
- LLM fallback 템플릿

### Phase 4 — 모의투자

- paper buy/sell order
- 현재가 기반 체결 시뮬레이션
- 수수료/세금 추정
- 평가손익/누적수익률

### Phase 5 — UI

- Streamlit Dashboard
- 관심종목/추천/시세/보유/모의투자/로그 탭

### Phase 6 — 테스트와 보고서

- `pytest -q`
- `ruff check .`
- `reports/test-results/latest-test-summary.md`
- `reports/test-results/latest-pytest-output.txt`
- `reports/implementation/latest-implementation-report.md`

## 4. 권장 명령

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env.local
ruff check .
pytest -q
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

## 5. 완료 조건

- 모든 필수 테스트 통과
- secret masking 테스트 통과
- Toss API client는 mock 응답으로 contract test 통과
- live trading disabled 상태에서 주문 API 호출 시 즉시 차단되는 테스트 통과
- README에 실행 방법 기록
- 테스트 결과와 구현 리포트 생성


## 6. 단계 종료 프로토콜

모든 Phase/Milestone 종료 시 Codex는 아래 순서를 따른다.

1. 구현 결과를 요약한다.
2. `ruff`, `pytest`, 관련 contract test를 실행한다.
3. 테스트 결과를 `reports/test-results/`에 저장한다.
4. 구현 리포트를 `reports/implementation/`에 저장한다.
5. 단계 완료 체크리스트를 `reports/stage-gates/`에 생성한다.
6. 사용자 입력 또는 승인이 필요한 항목을 명시한다.
7. 다음 단계 후보를 제시한다.
8. **사용자의 다음 명령을 기다린다.**

완료 보고에는 반드시 다음 문장을 포함한다.

```text
현재 단계가 종료되었습니다. 다음 명령을 기다립니다.
```
