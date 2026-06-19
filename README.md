# ai_stock 개발 문서 세트

작성일: 2026-06-19  
대상: Codex / AI Coding Agent / 초급 개발자  
목표: 토스증권 Open API를 이용해 **로컬 전용 AI 추천 + 모의투자 중심 주식 트레이딩 툴 v0.1**을 구현한다.
GitHub Repository: `https://github.com/JaiIn/ai_stock`

---

## 0. 최우선 결정

이 프로젝트는 **배포를 고려하지 않는다.**

```text
실행 환경: 사용자 로컬 PC
접속 방식: http://127.0.0.1:8501
DB: SQLite local file
로그/리포트: local files
배포/클라우드/외부 접속: 제외
```

v0.1의 기본 프론트엔드는 **Streamlit**이다. 단, Streamlit은 UI 레이어로만 사용하고 핵심 로직은 `src/ai_stock/` 백엔드 패키지로 분리한다.

---

## 1. 반드시 먼저 읽을 문서

1. `CODEX.md`
2. `docs/00_SOURCE_REVIEW.md`
3. `docs/01_PRODUCT_REQUIREMENTS.md`
4. `docs/02_TOSS_OPEN_API_REFERENCE.md`
5. `docs/21_TECH_STACK_AND_API_SCOPE.md`
6. `docs/22_PROJECT_SETUP_AND_USAGE_GUIDE.md`
7. `docs/23_LOCAL_ONLY_EXECUTION_POLICY.md`
8. `docs/24_FRONTEND_FRAMEWORK_DECISION.md`
9. `docs/25_CODEX_MULTI_SESSION_ROLE_PROCESS.md`
10. `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
11. `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
12. `roles/00_ROLE_INDEX.md`
13. `docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md`
14. `docs/19_DETAILED_MICRO_WBS.md`
15. `docs/20_CODEX_STOP_AND_CONFIRMATION_RULES.md`

---

## 2. 산출물 구성

```text
.
├── CODEX.md
├── README.md
├── docs/
│   ├── 00_SOURCE_REVIEW.md
│   ├── 01_PRODUCT_REQUIREMENTS.md
│   ├── 02_TOSS_OPEN_API_REFERENCE.md
│   ├── 03_DEVELOPMENT_ARCHITECTURE.md
│   ├── 04_PROJECT_STRUCTURE.md
│   ├── 05_CONFIG_AND_SECRETS.md
│   ├── 06_TOSS_CLIENT_DESIGN.md
│   ├── 07_MARKET_DATA_PIPELINE.md
│   ├── 08_AI_RECOMMENDATION_ENGINE.md
│   ├── 09_PAPER_TRADING_ENGINE.md
│   ├── 10_TEST_EXECUTION_AND_LOGGING.md
│   ├── 11_ORDER_AND_SAFETY_POLICY.md
│   ├── 12_WBS.md
│   ├── 13_CODEX_TASK_PROMPTS.md
│   ├── 14_RISK_COMPLIANCE_AND_OPERATIONS.md
│   ├── 15_OBSERVABILITY_AND_REPORTS.md
│   ├── 16_FUTURE_ROADMAP.md
│   ├── 17_STAGE_GATE_AND_USER_APPROVAL.md
│   ├── 18_MICRO_STAGE_DEVELOPMENT_PROCESS.md
│   ├── 19_DETAILED_MICRO_WBS.md
│   ├── 20_CODEX_STOP_AND_CONFIRMATION_RULES.md
│   ├── 21_TECH_STACK_AND_API_SCOPE.md
│   ├── 22_PROJECT_SETUP_AND_USAGE_GUIDE.md
│   ├── 23_LOCAL_ONLY_EXECUTION_POLICY.md
│   ├── 24_FRONTEND_FRAMEWORK_DECISION.md
│   ├── 25_CODEX_MULTI_SESSION_ROLE_PROCESS.md
│   ├── 26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md
│   └── 27_ROLE_BASED_GIT_WORKFLOW.md
├── roles/
│   ├── 00_ROLE_INDEX.md
│   ├── 01_PM_INTEGRATOR_SESSION.md
│   ├── 02_BACKEND_API_CLIENT_SESSION.md
│   ├── 03_FRONTEND_UI_SESSION.md
│   ├── 04_DATA_DB_SESSION.md
│   ├── 05_AI_RECOMMENDATION_SESSION.md
│   ├── 06_PAPER_TRADING_RISK_SESSION.md
│   ├── 07_QA_TEST_LOGGING_SESSION.md
│   ├── 08_DOCS_GUIDE_SESSION.md
│   └── 09_GIT_VERSION_CONTROL_SESSION.md
├── references/
│   ├── endpoint_matrix.md
│   ├── data_model_dictionary.md
│   ├── error_and_rate_limit_notes.md
│   └── source_links.md
└── templates/
    ├── .env.example.md
    ├── implementation_report_template.md
    ├── test_result_template.md
    ├── error_log_template.md
    ├── stage_completion_checklist_template.md
    ├── micro_stage_completion_checklist_template.md
    ├── user_approval_request_template.md
    ├── development_status_board_template.md
    ├── micro_stage_test_summary_template.md
    ├── git_commit_checklist_template.md
    ├── git_push_approval_request_template.md
    └── user_input_request_template.md
```

---

## 3. v0.1 개발 원칙

- v0.1은 **로컬 전용**이다.
- v0.1은 **실주문 금지**다.
- 토스증권 주문 API는 문서화만 하고, 앱 기본 동작은 조회 + AI 추천 + 모의투자다.
- API Key, Client Secret, Access Token, 계좌번호, accountSeq는 로그·화면·리포트에 원문 출력하지 않는다.
- 모든 금액·수량·가격은 `float`가 아니라 `Decimal` 기반으로 처리한다.
- AI는 설명 생성과 후보 정렬 보조에만 사용한다.
- 추천 결과는 투자 조언이 아니라 개인용 분석 보조 정보다.
- Codex는 구현 후 반드시 테스트 결과와 구현 보고서를 `reports/`에 남긴다.
- Codex는 Micro Stage 하나를 완료하면 반드시 사용자 명령을 기다린다.
- Codex는 Micro Stage 단위로 Git commit 후보를 만들고, push는 사용자 승인 후에만 수행한다.

---

## 4. 확정 기술 스택 요약

```text
Local Only
Python 3.11+
Streamlit UI
No FastAPI by default
SQLite + SQLAlchemy
httpx + tenacity
pydantic-settings + python-dotenv
pytest + pytest-httpx/respx
ruff
Rule-based recommendation first
Mock LLM first
Real order disabled
```

자세한 내용은 `docs/21_TECH_STACK_AND_API_SCOPE.md`를 따른다.

---

## 5. 프론트엔드 결정

v0.1은 Streamlit을 사용한다.

단, Streamlit은 다음 역할만 담당한다.

- 화면 렌더링
- 사용자 입력 수집
- service layer 호출
- 결과 표시
- 로그/리포트 표시

Streamlit에서 직접 하지 않는 것:

- Toss API 직접 호출
- DB 직접 접근
- 추천 점수 직접 계산
- 모의투자 체결 직접 처리
- 실주문 관련 기능 구현

대안 검토는 `docs/24_FRONTEND_FRAMEWORK_DECISION.md`에 정리되어 있다.

---

## 6. 역할별 Codex 세션 운영

사용자는 여러 Codex 세션을 역할별로 나눠 운영할 수 있다.

권장 역할:

```text
Session A: PM/Integrator
Session B: Backend/API Client
Session C: Data/DB
Session D: AI Recommendation
Session E: Paper Trading/Risk
Session F: Frontend/UI
Session G: QA/Test/Logging
Session H: Docs/Guide
Session I: Git/Version Control
```

각 세션은 `roles/` 하위의 자기 역할 문서를 읽고, 자기 담당 파일만 수정한다.

자세한 규칙은 `docs/25_CODEX_MULTI_SESSION_ROLE_PROCESS.md`와 `roles/00_ROLE_INDEX.md`를 따른다.

---

## 7. Codex에게 줄 시작 지시 예시

### 전체 PM 세션

```text
CODEX.md, docs/21_TECH_STACK_AND_API_SCOPE.md, docs/22_PROJECT_SETUP_AND_USAGE_GUIDE.md, docs/25_CODEX_MULTI_SESSION_ROLE_PROCESS.md를 읽으세요.
MS-00.01 하나만 수행하고, 완료 체크리스트와 테스트 결과를 작성한 뒤 멈추세요.
```

### Backend/API Client 세션

```text
CODEX.md와 roles/02_BACKEND_API_CLIENT_SESSION.md를 읽으세요.
BE-MS-01 하나만 수행하세요.
실제 Toss API 키가 필요하면 사용자에게 요청하고 대기하세요.
```

### Frontend/UI 세션

```text
CODEX.md와 roles/03_FRONTEND_UI_SESSION.md를 읽으세요.
FE-MS-01 하나만 수행하세요.
백엔드 로직은 수정하지 말고 Streamlit UI shell만 구현하세요.
```

---

## 8. 단계별 사용자 승인 게이트

Codex는 각 Micro Stage를 완료할 때마다 자동으로 다음 단계로 넘어가지 않는다.

필수 절차:

1. 단계 완료 체크리스트 작성
2. 테스트 결과 저장
3. 구현 리포트 저장
4. 사용자 입력 필요 여부 판단
5. 다음 단계 후보 1개 제시
6. 사용자 명령 대기

실제 Toss API 토큰, Client ID/Secret, accountSeq, 실 API 호출 승인 등이 필요한 경우 Codex는 임의값으로 진행하지 않고 사용자에게 안전한 입력 방법을 안내한 뒤 대기한다.

---

## 9. 초세분화 개발 프로세스

기본 규칙:

```text
사용자 명령 1회 = Micro Stage 1개 수행 = 테스트/보고/체크리스트 작성 = 사용자 명령 대기
```

목적:

- 한 번에 너무 많은 파일이 바뀌는 것을 방지
- 사용자가 더 자주 결과를 검토
- 실제 토큰/API Key/계좌 정보가 필요한 순간에 즉시 중단
- Mock 테스트와 Live API 테스트를 명확히 분리
- 실주문 관련 위험 작업을 기본 차단

---

## 10. GitHub 단계별 커밋 정책

Repository:

```text
https://github.com/JaiIn/ai_stock
```

기본 규칙:

```text
Micro Stage 1개 완료 = 테스트/체크리스트/리포트 작성 = Git commit 후보 생성 = 사용자 push 승인 대기
```

Codex는 사용자 승인 없이 `git push`, `git rebase`, `git reset --hard`, `git push --force`, `main` 직접 커밋을 수행하지 않는다.

자세한 규칙은 아래 문서를 따른다.

- `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
- `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
- `roles/09_GIT_VERSION_CONTROL_SESSION.md`

권장 초기 지시:

```text
CODEX.md, docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md, docs/27_ROLE_BASED_GIT_WORKFLOW.md를 읽으세요.
MS-00.01 문서 초기 커밋 후보만 만들고, push는 하지 말고 사용자 승인 대기하세요.
```

---

## 11. 로컬 실행 명령 요약

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env.local
pytest -q
ruff check .
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
Copy-Item .env.example .env.local
pytest -q
ruff check .
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```
