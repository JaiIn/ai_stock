# 21. 확정 기술 스택 및 사용 API 범위

작성일: 2026-06-19  
적용 범위: v0.1 로컬 전용 AI 추천/모의투자 트레이딩 툴  
최우선 원칙: **배포하지 않는다. 로컬 PC에서만 실행한다.**

---

## 1. 이 문서의 목적

이 문서는 Codex가 기술 스택을 임의로 바꾸지 않도록 **v0.1 확정 기술 스택**과 **사용 가능한 Toss Invest API 범위**를 고정한다.

Codex는 이 문서에 없는 기술을 도입하려면 반드시 사용자에게 먼저 보고하고 승인을 받아야 한다.

---

## 2. v0.1 확정 실행 환경

| 항목 | 결정 | 비고 |
|---|---|---|
| 실행 방식 | 로컬 단일 PC 실행 | 배포, 서버 운영, 외부 접속 고려하지 않음 |
| OS | Windows 우선, Linux/macOS 호환 고려 | 사용자는 Windows 환경 가능성이 높음 |
| Python | Python 3.11 이상 | 3.12도 가능하되 호환성 확인 |
| 네트워크 바인딩 | `127.0.0.1` only | `0.0.0.0` 금지 |
| 데이터베이스 | SQLite | `data/local/app.db` |
| 설정 파일 | `.env.local` + `.env.example` | 실제 키는 `.env.local`에만 저장 |
| 로그 | 로컬 파일 | `logs/` 하위 저장 |
| 리포트 | 로컬 Markdown | `reports/` 하위 저장 |
| 배포 | 없음 | Docker, Nginx, 클라우드 배포 제외 |

---

## 3. v0.1 확정 기술 스택

### 3.1 Language / Runtime

```text
Python 3.11+
```

선정 이유:

- Toss API client, 데이터 처리, AI 추천, 모의투자 엔진을 한 언어로 구현 가능
- Codex가 빠르게 구현/수정하기 쉬움
- Streamlit, FastAPI, SQLAlchemy, pandas 등 생태계가 충분함

---

### 3.2 Frontend

v0.1 기본 선택:

```text
Streamlit
```

단, Streamlit은 **프론트엔드 레이어**로만 사용한다.

Streamlit 파일 안에 다음 로직을 직접 구현하지 않는다.

- Toss API 호출 상세 로직
- DB SQL 처리
- 추천 점수 계산 핵심 로직
- 모의투자 체결 로직
- 리스크 검증 로직
- secret masking 로직

Streamlit은 아래만 담당한다.

- 화면 렌더링
- 사용자 입력 수집
- 버튼/폼 이벤트 처리
- 백엔드 서비스 호출
- 결과 표시
- 로컬 로그/리포트 링크 표시

프론트엔드 대안 검토는 `docs/24_FRONTEND_FRAMEWORK_DECISION.md`를 따른다.

---

### 3.3 Backend / Application Core

v0.1은 외부 배포용 API 서버를 만들지 않는다.

기본 구조:

```text
Streamlit UI -> Python Service Layer -> Repository/API Client/Engine
```

FastAPI는 v0.1 필수 스택이 아니다.

다만 역할 분리를 위해 백엔드 코드는 `src/ai_stock/` 하위에 독립 패키지로 구현한다.

FastAPI 도입 조건:

- Streamlit UI와 백엔드 프로세스를 분리해야 할 필요가 생긴 경우
- 프론트엔드를 React/Vue 등으로 바꾸기로 결정한 경우
- 사용자가 명시적으로 승인한 경우

v0.1에서는 FastAPI를 설치하지 않는다. 필요 시 v0.2 후보로 문서화한다.

---

### 3.4 Database / Persistence

v0.1 확정:

```text
SQLite + SQLAlchemy 2.x
```

저장 위치:

```text
data/local/app.db
```

저장 대상:

- 관심종목
- 시세 스냅샷
- 캔들 캐시
- 종목 정보 캐시
- 계좌 스냅샷
- 보유 자산 스냅샷
- 추천 실행 이력
- 추천 결과
- 모의 포트폴리오
- 모의 주문
- 모의 포지션
- 테스트/실행 메타데이터

v0.1에서 사용하지 않는 것:

- PostgreSQL
- Redis
- Celery
- Kafka
- 외부 DB 서비스
- 클라우드 DB

---

### 3.5 HTTP Client

v0.1 확정:

```text
httpx
```

보조 패키지:

```text
tenacity
```

역할:

- Toss Invest Open API 호출
- timeout 설정
- 재시도 정책
- rate limit 대응
- request id / trace id 로깅
- 응답 검증

---

### 3.6 Config / Secret

v0.1 확정:

```text
pydantic-settings
python-dotenv
```

설정 파일:

```text
.env.example     # 샘플, Git 포함 가능
.env.local       # 실제 값, Git 제외 필수
```

`.env.local`에 저장 가능한 값:

- TOSS_CLIENT_ID
- TOSS_CLIENT_SECRET
- TOSS_ACCOUNT_SEQ
- OPENAI_API_KEY 또는 사용자가 선택한 LLM Provider Key
- ALLOW_LIVE_API
- ALLOW_REAL_ORDER
- DATABASE_URL

절대 금지:

- 실제 Client Secret을 문서/리포트/로그에 출력
- Access Token 원문 출력
- 계좌번호/accountSeq 원문 출력
- Codex가 임의로 secret 값 생성

---

### 3.7 AI / LLM Layer

v0.1 기본 정책:

```text
LLM Provider 추상화만 구현
실제 LLM 호출은 사용자 API Key 입력 후 별도 승인 시 수행
```

기본 구현:

- Rule-based scoring
- Template-based explanation fallback
- LLM provider interface
- Mock LLM provider

선택 구현:

- OpenAI API provider
- Local LLM provider
- 기타 provider

AI는 다음 작업에만 사용한다.

- 분석 요약 생성
- 추천 사유 설명
- 위험 요인 설명
- 사용자 친화적 문장 생성

AI가 직접 해서는 안 되는 작업:

- 실주문 실행 판단
- 주문 수량 최종 결정
- 투자 확정 지시
- 리스크 게이트 우회

---

### 3.8 Test / Quality

v0.1 확정:

```text
pytest
pytest-httpx 또는 respx
ruff
mypy optional
```

필수 테스트:

- config 로딩 테스트
- secret masking 테스트
- Toss API client mock contract test
- SQLite repository test
- 추천 점수 계산 test
- 모의주문 체결 test
- 실주문 차단 test
- Streamlit UI smoke test는 가능하면 최소 수준으로 작성

---

## 4. Toss Invest API 사용 범위

### 4.1 v0.1 허용 API

v0.1은 기본적으로 **Read-only + Paper Trading** 프로젝트다.

허용 API:

| API 영역 | 용도 | v0.1 사용 여부 | Live 호출 조건 |
|---|---|---:|---|
| Auth | OAuth2 token 발급 | 사용 | Client ID/Secret 입력 후 사용자 승인 |
| Market Data | 현재가/호가/체결/캔들 등 | 사용 | `ALLOW_LIVE_API=true` + 사용자 승인 |
| Stock Info | 종목 정보/경고 | 사용 | `ALLOW_LIVE_API=true` + 사용자 승인 |
| Market Info | 환율/장 정보 | 사용 | `ALLOW_LIVE_API=true` + 사용자 승인 |
| Account | 계좌 목록 | 사용 | 사용자 승인 + masking 필수 |
| Asset | 보유자산 조회 | 사용 | 사용자 승인 + masking 필수 |
| Order Info | 매수가능/매도가능/수수료 조회 | 사용 가능 | 사용자 승인 + masking 필수 |
| Order History | 주문 내역 조회 | 선택 | 사용자 승인 + masking 필수 |

---

### 4.2 v0.1 금지 API

실주문 관련 API는 v0.1에서 실제 호출 금지다.

| API 영역 | 엔드포인트 유형 | v0.1 정책 |
|---|---|---|
| Order | 주문 생성 | 실제 호출 금지 |
| Order | 주문 정정 | 실제 호출 금지 |
| Order | 주문 취소 | 실제 호출 금지 |

구현은 가능하되 다음 조건을 만족해야 한다.

- 기본값 `ALLOW_REAL_ORDER=false`
- 코드 레벨 safety gate 존재
- 테스트에서 실주문 호출 차단 확인
- UI에서 실주문 버튼 노출 금지
- 사용자가 명시적으로 v0.2 실주문 전환을 승인하기 전까지 비활성화

---

## 5. 로컬 전용으로 인해 제외되는 기술

v0.1에서 아래 기술은 사용하지 않는다.

| 기술 | 제외 이유 |
|---|---|
| Docker | 로컬 단일 PC 실행에는 과함. 초반 복잡도 증가 |
| Kubernetes | 배포 없음 |
| Nginx | 외부 서비스 없음 |
| PostgreSQL | SQLite로 충분 |
| Redis | background job/분산 캐시 없음 |
| Celery | 예약/비동기 분산 작업 없음 |
| Cloud Run/EC2/S3/RDS | 배포/클라우드 운영 없음 |
| OAuth redirect web app | 현재는 Client Credentials 중심 API 사용 |
| React/Vite | v0.1에서는 과함. 단 v0.2 대안 가능 |

---

## 6. 역할 분리를 위한 패키지 경계

```text
src/ai_stock/
├── config/              # 설정, env, secret masking
├── logging/             # 로컬 로그, trace id
├── toss_api/            # Toss Open API client
├── domain/              # 공통 domain model
├── repositories/        # SQLite 저장소
├── services/            # application service
├── recommendation/      # AI/rule-based 추천
├── paper_trading/       # 모의투자 엔진
├── risk/                # 안전장치, 주문 차단
├── reports/             # markdown report 생성
└── utils/               # 공통 유틸

app/
└── streamlit_app.py     # UI entrypoint only
```

중요:

- `src/ai_stock/`는 Streamlit을 import하지 않는다.
- `app/streamlit_app.py`는 DB에 직접 접근하지 않는다.
- UI는 service layer만 호출한다.
- API client는 UI에서 직접 호출하지 않는다.

---

## 7. Codex 변경 제한

Codex는 아래 변경을 임의로 하지 않는다.

- Streamlit을 React/Vue/NiceGUI 등으로 교체
- SQLite를 PostgreSQL로 교체
- 로컬 실행을 배포 구조로 변경
- Docker 도입
- FastAPI 서버 필수화
- 실주문 활성화
- 외부 접근 가능한 host/port 설정

필요하다고 판단하면 다음 형식으로 사용자에게 제안만 한다.

```text
[기술 변경 제안]
- 현재 결정: Streamlit + SQLite + 로컬 실행
- 제안 변경: NiceGUI 도입
- 이유:
- 영향 범위:
- 되돌리는 방법:
- 사용자 승인 필요 여부: 필요

사용자 승인 전까지 구현하지 않습니다.
```

---

## 8. v0.1 최종 기술 결정 요약

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
