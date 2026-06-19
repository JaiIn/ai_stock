# 27. 역할별 Codex 세션 Git Workflow

작성일: 2026-06-19  
프로젝트명: `ai_stock`  
Repository: `https://github.com/JaiIn/ai_stock`

---

## 1. 목적

사용자는 여러 Codex 세션을 역할별로 나누어 사용할 예정이다.

이 문서는 각 세션이 Git 브랜치, 커밋, 파일 소유권, 인수인계 방식을 어떻게 가져가야 하는지 정의한다.

핵심 원칙:

```text
한 세션 = 한 역할 = 한 Micro Stage = 한 브랜치 = 한 커밋 후보
```

---

## 2. 세션별 Git 역할

| 세션 | 역할 | 브랜치 prefix | main merge 가능 여부 |
|---|---|---|---|
| Session A | PM/Integrator | `codex/pm/` | 가능, 사용자 승인 필요 |
| Session B | Backend/API Client | `codex/backend/` | 불가 |
| Session C | Data/DB | `codex/data/` | 불가 |
| Session D | AI Recommendation | `codex/ai/` | 불가 |
| Session E | Paper Trading/Risk | `codex/paper/` | 불가 |
| Session F | Frontend/UI | `codex/frontend/` | 불가 |
| Session G | QA/Test/Logging | `codex/qa/` | 불가 |
| Session H | Docs/Guide | `codex/docs/` | 불가 |
| Session I | Git/Version Control | `codex/git/` | 제한적, PM 승인 필요 |

---

## 3. PM/Integrator 세션

참조 문서:

```text
roles/01_PM_INTEGRATOR_SESSION.md
```

담당:

- repository 초기화
- 문서 세트 최초 커밋
- `local/integration` 브랜치 관리
- role branch 병합 검토
- 파일 충돌 조정
- main 반영 전 최종 테스트
- 사용자 승인 요청

허용 파일:

```text
CODEX.md
README.md
docs/**
roles/**
templates/**
references/**
reports/stage-gates/**
reports/session-handoff/**
```

PM 세션은 기능 코드를 직접 구현하지 않는다. 기능 코드 수정이 필요하면 해당 역할 세션에 인수인계한다.

---

## 4. Backend/API Client 세션

브랜치 예시:

```text
codex/backend/MS-02.04-oauth-mock-client
```

담당:

- Toss API client
- OAuth mock/live 준비
- request wrapper
- retry/rate limit
- read-only endpoint client
- mutation guard

허용 파일:

```text
src/ai_stock/toss_api/**
src/ai_stock/config/**
src/ai_stock/core/logging.py
src/ai_stock/core/masking.py
src/ai_stock/domain/api_models.py
tests/unit/test_toss_*.py
tests/contract/test_toss_*.py
reports/micro-stages/**
reports/test-results/**
reports/git/**
```

금지:

```text
app/**
src/ai_stock/recommendation/**
src/ai_stock/paper_trading/**
src/ai_stock/repositories/**
실제 주문 API 활성화
```

---

## 5. Data/DB 세션

브랜치 예시:

```text
codex/data/MS-03.03-watchlist-model
```

담당:

- SQLite local DB
- SQLAlchemy models
- repository
- DB init script
- local schema 검증

허용 파일:

```text
src/ai_stock/db/**
src/ai_stock/repositories/**
src/ai_stock/domain/entities.py
src/ai_stock/domain/db_models.py
scripts/init_db.py
tests/unit/test_db_*.py
tests/unit/test_repository_*.py
reports/micro-stages/**
reports/test-results/**
reports/git/**
```

금지:

```text
실제 DB 파일 commit
Toss API client 직접 수정
Streamlit UI 직접 수정
```

---

## 6. AI Recommendation 세션

브랜치 예시:

```text
codex/ai/MS-05.04-rule-based-scoring
```

담당:

- 추천 입력 DTO
- 기술지표 계산
- rule-based scoring
- risk penalty
- LLM prompt/provider abstraction
- 설명 생성
- 금지 표현 guardrail

허용 파일:

```text
src/ai_stock/recommendation/**
src/ai_stock/llm/**
src/ai_stock/services/recommendation_service.py
tests/unit/test_recommendation_*.py
tests/unit/test_llm_*.py
reports/micro-stages/**
reports/test-results/**
reports/git/**
```

금지:

```text
Toss API 직접 호출
실주문 연결
DB schema 직접 변경
```

---

## 7. Paper Trading/Risk 세션

브랜치 예시:

```text
codex/paper/MS-06.02-paper-order-create
```

담당:

- 모의 계좌
- 모의 주문
- 체결 시뮬레이션
- 포지션/PnL
- 수수료/세금 모델
- 실주문 격리 검증

허용 파일:

```text
src/ai_stock/paper_trading/**
src/ai_stock/risk/**
src/ai_stock/services/paper_trading_service.py
tests/unit/test_paper_*.py
tests/safety/**
reports/micro-stages/**
reports/test-results/**
reports/git/**
```

금지:

```text
POST /orders 실제 호출
ALLOW_REAL_ORDER 기본값 변경
Toss order client 활성화
```

---

## 8. Frontend/UI 세션

브랜치 예시:

```text
codex/frontend/MS-07.01-streamlit-shell
```

담당:

- Streamlit shell
- sidebar/settings
- watchlist page
- market page
- recommendation page
- paper trading page
- portfolio page
- reports page

허용 파일:

```text
app/**
src/ai_stock/ui/**
tests/ui/**
reports/micro-stages/**
reports/test-results/**
reports/git/**
```

금지:

```text
src/ai_stock/toss_api/** 직접 수정
src/ai_stock/repositories/** 직접 수정
src/ai_stock/recommendation/** 핵심 로직 직접 수정
src/ai_stock/paper_trading/** 핵심 로직 직접 수정
```

프론트엔드는 service layer만 호출한다.

---

## 9. QA/Test/Logging 세션

브랜치 예시:

```text
codex/qa/MS-08.02-pytest-all
```

담당:

- pytest 실행
- ruff 실행
- coverage 요약
- 테스트 리포트 작성
- 민감정보 검사
- 로그 포맷 검증

허용 파일:

```text
tests/**
src/ai_stock/core/logging.py
src/ai_stock/core/masking.py
scripts/check_secrets.py
reports/test-results/**
reports/git/**
reports/implementation/**
```

기능 코드 수정은 원칙적으로 금지한다. 테스트를 통과시키기 위해 기능 수정이 필요하면 해당 세션에 인수인계한다.

---

## 10. Docs/Guide 세션

브랜치 예시:

```text
codex/docs/MS-08.04-readme-guide
```

담당:

- README
- 사용자 실행 가이드
- 오류 대응 가이드
- Codex 작업 프롬프트
- 템플릿 정리

허용 파일:

```text
README.md
CODEX.md
docs/**
roles/**
templates/**
references/**
reports/git/**
```

금지:

```text
src/** 기능 코드 직접 수정
tests/** 직접 수정
```

---

## 11. Git/Version Control 세션

브랜치 예시:

```text
codex/git/MS-00.02-git-policy
```

담당:

- `.gitignore`
- branch/commit policy
- GitHub repository 연결 안내
- commit checklist
- secret leak 예방 명령
- Git 충돌 상황 보고

허용 파일:

```text
.gitignore
README.md
CODEX.md
docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md
docs/27_ROLE_BASED_GIT_WORKFLOW.md
templates/git_commit_checklist_template.md
reports/git/**
```

금지:

```text
기능 코드 수정
임의 push
force push
main 직접 commit
```

---

## 12. 여러 Codex 세션 동시 작업 시 권장 방식

가장 안전한 방법은 세션별로 작업 디렉토리를 분리하는 것이다.

### 12.1 git worktree 권장

PM 세션이 아래처럼 worktree를 만들 수 있다.

```bash
git worktree add ../ai_stock_backend codex/backend/MS-02.04-oauth-mock-client
git worktree add ../ai_stock_frontend codex/frontend/MS-07.01-streamlit-shell
git worktree add ../ai_stock_ai codex/ai/MS-05.04-rule-based-scoring
```

각 Codex 세션은 자기 worktree만 사용한다.

장점:

- 작업 파일 충돌 감소
- branch 혼동 감소
- 각 세션의 `git status`가 독립적

주의:

- 같은 파일을 여러 세션이 동시에 수정하지 않는다.
- PM 세션이 병합 순서를 관리한다.
- worktree 삭제는 사용자 승인 후만 수행한다.

### 12.2 단일 폴더 사용 시

단일 폴더에서 여러 세션을 번갈아 사용할 경우, 매번 작업 전 아래를 확인한다.

```bash
git status
git branch --show-current
```

미커밋 변경사항이 있으면 다른 세션은 작업을 시작하지 않는다.

---

## 13. 세션 간 인수인계 규칙

다른 역할의 변경이 필요하면 아래 파일을 작성한다.

```text
reports/session-handoff/<from-role>_to_<to-role>_<micro-stage>.md
```

예시:

```text
reports/session-handoff/frontend_to_backend_MS-07.04.md
```

내용:

```text
요청 역할: Frontend/UI
대상 역할: Backend/API Client
관련 Micro Stage: MS-07.04
필요 변경: market data service에 get_latest_snapshots() 함수 필요
사유: UI 표시용 mock 데이터를 service layer에서 받기 위함
수정 금지 파일: app/**에서 Toss API 직접 호출 금지
```

---

## 14. 충돌 발생 시 처리

merge conflict가 발생하면 Codex는 임의로 해결하지 않는다.

허용:

- 충돌 파일 목록 보고
- 충돌 원인 추정
- 해결안 제시

금지:

- 사용자 승인 없는 conflict resolution commit
- 사용자 승인 없는 `git reset --hard`
- 사용자 승인 없는 `git rebase`
- 사용자 승인 없는 `git push --force`

보고 예시:

```text
local/integration 병합 중 충돌이 발생했습니다.
충돌 파일:
- README.md
- docs/19_DETAILED_MICRO_WBS.md

원인:
- Docs 세션과 PM 세션이 같은 Micro Stage 설명을 수정했습니다.

해결 방안 후보:
1. PM 세션 변경을 기준으로 병합
2. Docs 세션 변경을 기준으로 병합
3. 두 내용을 수동 통합

사용자 지시를 기다립니다.
```

---

## 15. 완료 조건

역할별 Git Workflow가 준비되었다고 판단하려면 아래를 만족해야 한다.

- [ ] 각 역할별 브랜치 prefix가 정의되어 있다.
- [ ] 각 역할별 허용 파일 범위가 정의되어 있다.
- [ ] 각 역할별 금지 파일 범위가 정의되어 있다.
- [ ] PM/Integrator만 merge를 담당하도록 정의되어 있다.
- [ ] push는 사용자 승인 후만 수행하도록 정의되어 있다.
- [ ] worktree 사용 방식이 안내되어 있다.
- [ ] conflict 발생 시 중단 규칙이 정의되어 있다.
