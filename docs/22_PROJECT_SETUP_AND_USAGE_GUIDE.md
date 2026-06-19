# 22. 로컬 프로젝트 세팅 및 사용 가이드

작성일: 2026-06-19  
대상: 사용자 / Codex / 역할별 Codex 세션  
적용 범위: v0.1 로컬 전용 실행

---

## 1. 이 문서의 목적

이 문서는 프로젝트를 로컬 PC에서 실행하기 위한 표준 절차를 정의한다.

중요:

- 이 프로젝트는 배포하지 않는다.
- 외부 사용자를 받지 않는다.
- 로컬 브라우저에서만 실행한다.
- 실제 API Key, Client Secret, Token은 사용자가 직접 `.env.local`에 입력한다.
- Codex는 사용자 대신 실제 secret 값을 생성하거나 추측하지 않는다.

---

## 2. 권장 디렉토리 구조

```text
ai_stock/
├── app/
│   ├── streamlit_app.py
│   └── pages/
├── src/
│   └── ai_stock/
│       ├── config/
│       ├── logging/
│       ├── toss_api/
│       ├── domain/
│       ├── repositories/
│       ├── services/
│       ├── recommendation/
│       ├── paper_trading/
│       ├── risk/
│       ├── reports/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   └── fixtures/
├── data/
│   └── local/
├── logs/
├── reports/
│   ├── implementation/
│   ├── test-results/
│   ├── error-logs/
│   ├── micro-stages/
│   └── session-handoff/
├── scripts/
├── .env.example
├── .env.local
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
└── README.md
```

---

## 3. 로컬 환경 준비

### 3.1 Python 확인

```bash
python --version
```

권장:

```text
Python 3.11 이상
```

---

### 3.2 가상환경 생성

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

---

### 3.3 패키지 설치

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

설치 후 확인:

```bash
python -c "import sys; print(sys.version)"
python -c "import streamlit; print(streamlit.__version__)"
```

---

## 4. `.env.local` 설정

### 4.1 샘플 파일 복사

```bash
cp .env.example .env.local
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env.local
```

---

### 4.2 기본 설정 예시

```dotenv
APP_ENV=local
APP_HOST=127.0.0.1
APP_PORT=8501
DATABASE_URL=sqlite:///data/local/app.db

ALLOW_LIVE_API=false
ALLOW_REAL_ORDER=false

TOSS_CLIENT_ID=
TOSS_CLIENT_SECRET=
TOSS_ACCOUNT_SEQ=

LLM_PROVIDER=mock
OPENAI_API_KEY=

LOG_LEVEL=INFO
MASK_SECRETS=true
```

---

### 4.3 사용자 입력이 필요한 값

다음 값이 필요한 순간 Codex는 멈추고 사용자에게 요청해야 한다.

| 값 | 필요한 단계 | Codex 동작 |
|---|---|---|
| TOSS_CLIENT_ID | OAuth live test | 요청 후 대기 |
| TOSS_CLIENT_SECRET | OAuth live test | 요청 후 대기 |
| TOSS_ACCOUNT_SEQ | 계좌/보유/주문가능 조회 | 요청 후 대기 |
| OPENAI_API_KEY | 실제 LLM 설명 생성 | 요청 후 대기 |
| ALLOW_LIVE_API=true | 실제 Toss API 호출 | 사용자 승인 필요 |
| ALLOW_REAL_ORDER=true | v0.1 금지 | 사용자가 요청해도 별도 정책 문서 필요 |

---

## 5. 로컬 실행 방법

### 5.1 Mock 모드 실행

기본 실행은 Mock 모드다.

```bash
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

브라우저 접속:

```text
http://127.0.0.1:8501
```

---

### 5.2 Live API 모드 전환

Live API 호출은 사용자가 명시적으로 승인한 경우에만 진행한다.

`.env.local`:

```dotenv
ALLOW_LIVE_API=true
TOSS_CLIENT_ID=사용자직접입력
TOSS_CLIENT_SECRET=사용자직접입력
```

그 후 사용자가 Codex에게 다음과 같이 명령한다.

```text
.env.local 입력 완료. OAuth live test Micro Stage 1개만 진행하세요.
```

Codex는 해당 Micro Stage만 수행하고 다시 멈춘다.

---

## 6. 테스트 실행

전체 테스트:

```bash
pytest -q
```

정적 검사:

```bash
ruff check .
```

특정 테스트:

```bash
pytest tests/unit -q
pytest tests/contract -q
pytest tests/integration -q
```

테스트 결과 저장 위치:

```text
reports/test-results/
```

---

## 7. 로그와 리포트 확인

로그:

```text
logs/app.log
logs/api.log
logs/error.log
```

구현 리포트:

```text
reports/implementation/
```

Micro Stage 완료 체크리스트:

```text
reports/micro-stages/
```

역할별 Codex 세션 인수인계:

```text
reports/session-handoff/
```

---

## 8. Codex 세션별 사용 방식

사용자는 여러 Codex 세션을 역할별로 나누어 사용할 수 있다.

권장 방식:

```text
세션 A: PM/Integrator
세션 B: Backend/API Client
세션 C: Data/DB
세션 D: AI Recommendation
세션 E: Paper Trading/Risk
세션 F: Frontend/UI
세션 G: QA/Test/Logging
세션 H: Docs/Guide
```

각 세션은 `roles/` 하위의 자기 역할 문서를 먼저 읽는다.

예시:

```text
roles/03_FRONTEND_UI_SESSION.md를 읽고, FE-MS-01 하나만 수행하세요.
완료 후 체크리스트 작성하고 다음 명령을 기다리세요.
```

---

## 9. 사용자 승인 대기 규칙

Codex는 다음 상황에서 반드시 멈춘다.

- 실제 secret 입력 필요
- 실제 Toss API 호출 필요
- DB schema migration 필요
- 기존 데이터 삭제/변경 가능성 있음
- 프론트엔드 프레임워크 변경 필요
- 실주문 관련 코드 변경 필요
- 테스트 실패
- 역할 경계를 넘어 다른 세션 담당 파일 수정 필요

종료 문구:

```text
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 10. 로컬 전용 보안 체크리스트

- [ ] `.env.local`은 `.gitignore`에 포함되어 있다.
- [ ] `APP_HOST=127.0.0.1`이다.
- [ ] `ALLOW_REAL_ORDER=false`이다.
- [ ] 실제 secret은 로그에 출력되지 않는다.
- [ ] SQLite DB는 `data/local/`에 저장된다.
- [ ] 외부 배포 스크립트가 없다.
- [ ] Docker/Nginx/Cloud 관련 파일을 만들지 않았다.
- [ ] 테스트 결과가 `reports/test-results/`에 저장된다.

---

## 11. 문제 발생 시 확인 순서

1. 가상환경이 활성화되었는지 확인
2. Python 버전 확인
3. 패키지 설치 여부 확인
4. `.env.local` 존재 여부 확인
5. `ALLOW_LIVE_API` 값 확인
6. 로그 확인
7. pytest 실패 로그 확인
8. 최근 Micro Stage 리포트 확인
9. 역할별 인수인계 문서 확인

---

## 12. 초기 실행 명령 요약

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

Windows PowerShell에서는 `source .venv/bin/activate` 대신 아래를 사용한다.

```powershell
.\.venv\Scripts\Activate.ps1
```
