# 04. 프로젝트 구조

작성일: 2026-06-19  
프로젝트명: `ai_stock`  
실행 정책: 로컬 전용, 배포 없음

---

## 1. 최종 권장 디렉토리

v0.1은 로컬 실행만 고려한다. 배포, Docker, 클라우드, 외부 접속 구조는 만들지 않는다.

```text
ai_stock/
├── app/
│   ├── streamlit_app.py
│   ├── pages/
│   │   ├── settings_page.py
│   │   ├── watchlist_page.py
│   │   ├── market_page.py
│   │   ├── recommendation_page.py
│   │   ├── paper_order_page.py
│   │   ├── portfolio_page.py
│   │   └── reports_page.py
│   └── ui_components/
├── src/
│   └── ai_stock/
│       ├── __init__.py
│       ├── config/
│       │   └── settings.py
│       ├── core/
│       │   ├── logging.py
│       │   ├── masking.py
│       │   └── decimal_utils.py
│       ├── toss_api/
│       │   ├── client.py
│       │   ├── auth.py
│       │   ├── token_store.py
│       │   ├── request.py
│       │   ├── errors.py
│       │   ├── market_data.py
│       │   ├── stock_info.py
│       │   ├── market_info.py
│       │   ├── account.py
│       │   ├── asset.py
│       │   ├── order_info.py
│       │   ├── order_history.py
│       │   ├── order.py
│       │   └── order_guard.py
│       ├── domain/
│       │   ├── api_models.py
│       │   ├── entities.py
│       │   └── db_models.py
│       ├── db/
│       │   ├── base.py
│       │   └── session.py
│       ├── repositories/
│       ├── services/
│       │   ├── watchlist_service.py
│       │   ├── market_data_service.py
│       │   ├── recommendation_service.py
│       │   └── paper_trading_service.py
│       ├── recommendation/
│       │   ├── schemas.py
│       │   ├── indicators.py
│       │   ├── scoring.py
│       │   ├── ranking.py
│       │   ├── risk_filter.py
│       │   ├── prompts.py
│       │   ├── explainer.py
│       │   └── guardrails.py
│       ├── llm/
│       │   └── provider.py
│       ├── paper_trading/
│       │   ├── account.py
│       │   ├── order_service.py
│       │   ├── fill_engine.py
│       │   ├── position_service.py
│       │   ├── fee_model.py
│       │   └── performance.py
│       ├── risk/
│       ├── reports/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── safety/
│   ├── ui/
│   └── fixtures/
├── scripts/
│   ├── init_db.py
│   └── check_secrets.py
├── data/
│   └── local/
├── logs/
├── reports/
│   ├── implementation/
│   ├── test-results/
│   ├── error-logs/
│   ├── micro-stages/
│   ├── stage-gates/
│   ├── session-handoff/
│   └── git/
├── docs/
├── roles/
├── references/
├── templates/
├── .env.example
├── .env.local
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── CODEX.md
└── README.md
```

---

## 2. 핵심 경계

### 2.1 Frontend

```text
app/
src/ai_stock/ui/  # 필요한 경우만
```

역할:

- Streamlit 화면 렌더링
- 사용자 입력 수집
- service layer 호출
- 결과 표시

금지:

- Toss API 직접 호출
- SQLite 직접 접근
- 추천 점수 직접 계산
- 모의체결 직접 처리
- 실주문 API 경로 활성화

### 2.2 Backend / Core Package

```text
src/ai_stock/
```

역할:

- Toss API client
- 설정/로깅/마스킹
- DB repository
- 추천 엔진
- 모의투자 엔진
- risk/safety gate
- report 생성

### 2.3 Data

```text
data/local/
```

역할:

- 로컬 SQLite DB 저장
- 임시 캐시 저장

주의:

- DB 파일은 Git에 포함하지 않는다.
- 샘플 fixture만 `tests/fixtures/`에 저장한다.

### 2.4 Reports

```text
reports/
```

역할:

- Micro Stage 체크리스트
- 테스트 결과
- 에러 로그 요약
- 구현 리포트
- Git commit checklist
- 세션 간 인수인계

민감정보는 반드시 마스킹한다.

---

## 3. requirements.txt

```txt
streamlit>=1.36
httpx>=0.27
pydantic>=2.7
pydantic-settings>=2.3
SQLAlchemy>=2.0
pandas>=2.2
numpy>=1.26
tenacity>=8.3
python-dotenv>=1.0
rich>=13.7
```

---

## 4. requirements-dev.txt

```txt
pytest>=8.2
pytest-httpx>=0.30
respx>=0.21
ruff>=0.5
coverage>=7.5
mypy>=1.10
```

---

## 5. Makefile 권장 명령

```makefile
.PHONY: install test lint run check-secrets init-db

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check .

run:
	streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501

check-secrets:
	python scripts/check_secrets.py

init-db:
	python scripts/init_db.py
```

---

## 6. .gitignore 필수

```gitignore
.env
.env.local
.env.*.local
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
logs/
*.log
data/local/*.db
data/local/*.sqlite
data/local/*.sqlite3
*.db
*.sqlite
*.sqlite3
reports/**/raw-*.json
reports/**/token*.json
reports/**/account*.json
.DS_Store
```

---

## 7. v0.1에서 생성 금지

```text
Dockerfile
docker-compose.yml
nginx.conf
kubernetes/
terraform/
.github/workflows/deploy.yml
cloudbuild.yaml
Procfile
```

---

## 8. 실행 명령

```bash
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Windows PowerShell:

```powershell
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

---

## 9. GitHub repository 연결

```text
https://github.com/JaiIn/ai_stock
```

초기 clone:

```bash
git clone https://github.com/JaiIn/ai_stock.git
cd ai_stock
```

자세한 Git 규칙은 아래 문서를 따른다.

- `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
- `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
