# 03. 개발 아키텍처

## 1. 전체 구조

```text
User Browser
   ↓
Streamlit UI
   ↓
Application Services
   ├── RecommendationService
   ├── PaperTradingService
   ├── PortfolioService
   ├── WatchlistService
   └── ReportService
   ↓
Infrastructure
   ├── TossInvestClient
   ├── LLMClient
   ├── SQLite Repository
   ├── Logger / Audit Logger
   └── Config / Secret Masker
```

## 2. 계층별 책임

### UI Layer

- Streamlit page 구성
- 입력값 검증
- 서비스 호출
- 결과 표시
- secret 원문 표시 금지

### Service Layer

- 비즈니스 로직
- 추천 점수 계산
- 모의 주문 생성/체결
- 리포트 생성
- Toss API 직접 호출 금지. 반드시 client wrapper 사용

### Client Layer

- Toss API HTTP 호출
- 인증/token refresh
- retry/backoff
- request/response logging
- schema parsing

### Repository Layer

- SQLite CRUD
- transaction 관리
- 원본 API 응답 raw_json 저장

## 3. 추천 플로우

```text
watchlist symbols
  → get stock info
  → get warnings
  → get current prices
  → get candles
  → compute indicators
  → apply risk filters
  → generate rule-based score
  → generate AI explanation
  → save recommendation run
  → display result
```

## 4. 모의투자 플로우

```text
recommendation selected
  → user creates paper order
  → validate cash/position
  → fetch latest price
  → simulate fill
  → calculate fee/tax estimate
  → update paper position
  → save audit log
```

## 5. Toss API 호출 원칙

- 모든 API 호출은 `TossInvestClient`만 수행
- HTTP timeout 기본 10초
- 401은 1회 token refresh
- 429는 `Retry-After` 우선
- 5xx는 제한된 retry
- response model은 pydantic으로 검증하되 unknown enum은 허용

## 6. AI 사용 원칙

- AI는 `final_score`를 직접 결정하지 않는다.
- AI는 이미 계산된 수치와 근거를 받아 설명을 생성한다.
- AI 출력은 금지어 필터를 통과해야 한다.
- AI 실패 시 rule-based explanation으로 fallback한다.

## 7. 실주문 차단 구조

```text
OrderMutationRequest
  → LiveTradingGuard
      ├── ENABLE_LIVE_TRADING == false → raise LiveTradingDisabledError
      ├── DRY_RUN_ONLY == true → paper order only
      ├── manual confirmation missing → reject
      └── v0.1 policy → reject always
```

v0.1에서는 어떠한 설정값을 넣어도 실주문은 실행되지 않도록 테스트를 작성한다.

---

## Local-only architecture update

사용자 요구에 따라 v0.1은 배포를 고려하지 않는다.

변경된 아키텍처 원칙:

```text
Local Browser
  -> Streamlit UI on 127.0.0.1:8501
  -> Python Service Layer
  -> SQLite local DB
  -> Local logs/reports
  -> Toss API outbound only when user approves
```

v0.1에서 제외:

- FastAPI API server mandatory architecture
- Docker deployment
- Cloud hosting
- Public URL
- PostgreSQL/Redis/Celery
- Reverse proxy
- Multi-user authentication

프론트엔드와 백엔드의 역할 경계:

| Layer | 담당 | 금지 |
|---|---|---|
| `app/` Streamlit | 화면 렌더링, 사용자 입력, service 호출 | API 직접 호출, DB 직접 접근, 추천/체결 계산 |
| `src/ai_stock/services/` | 유스케이스 조합 | UI 렌더링 |
| `src/ai_stock/toss_api/` | Toss API HTTP client | UI 의존성 |
| `src/ai_stock/repositories/` | SQLite 저장소 | Streamlit import |
| `src/ai_stock/recommendation/` | 추천 점수/설명 | 실주문 실행 |
| `src/ai_stock/paper_trading/` | 모의주문/포지션 | 실제 주문 호출 |
| `src/ai_stock/risk/` | safety gate | UI 의존성 |

세부 지침은 다음 문서를 따른다.

- `docs/21_TECH_STACK_AND_API_SCOPE.md`
- `docs/23_LOCAL_ONLY_EXECUTION_POLICY.md`
- `docs/24_FRONTEND_FRAMEWORK_DECISION.md`
- `docs/25_CODEX_MULTI_SESSION_ROLE_PROCESS.md`
