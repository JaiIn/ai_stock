# 25. Codex 다중 세션 역할 분리 프로세스

작성일: 2026-06-19  
적용 범위: 사용자가 여러 Codex 세션을 병렬/순차 운영하는 경우

---

## 1. 목적

사용자는 Codex의 여러 세션을 활용해 역할별로 개발을 나눌 수 있다.

이 문서는 각 세션의 책임, 수정 가능 파일, 금지 영역, 인수인계 방식을 정의한다.

목표:

- 한 세션이 너무 많은 영역을 변경하지 않도록 제한
- 프론트/백엔드/DB/AI/QA 역할 충돌 방지
- 작은 Micro Stage 단위로 검토 가능
- 사용자 승인 없이 다음 단계로 넘어가지 않도록 통제

---

## 2. 전체 역할 구조

| 세션 | 역할 | 주요 책임 |
|---|---|---|
| Session A | PM/Integrator | 전체 진행, 충돌 조정, 문서 정합성 |
| Session B | Backend/API Client | Toss API client, auth, HTTP, DTO |
| Session C | Data/DB | SQLite, SQLAlchemy, repository, migration |
| Session D | AI Recommendation | 추천 점수, LLM 설명, fallback |
| Session E | Paper Trading/Risk | 모의주문, 포지션, 리스크 게이트 |
| Session F | Frontend/UI | Streamlit 화면, 컴포넌트, UX |
| Session G | QA/Test/Logging | 테스트, 로그, 리포트, 품질 |
| Session H | Docs/Guide | README, 사용 가이드, 운영 문서 |
| Session I | Git/Version Control | 브랜치, 커밋, push 승인, secret commit 방지 |

---

## 2.1 GitHub 연동 공통 규칙

Repository는 `https://github.com/JaiIn/ai_stock`이다.

모든 세션은 Micro Stage 단위로 작업 브랜치를 만들고, 완료 후 commit 후보를 작성한다.

```text
한 세션 = 한 역할 = 한 Micro Stage = 한 브랜치 = 한 커밋 후보
```

Push는 사용자 승인 후에만 수행한다. 자세한 규칙은 다음 문서를 따른다.

- `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
- `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
- `templates/git_commit_checklist_template.md`

---

## 3. 공통 규칙

모든 세션은 다음 규칙을 따른다.

1. 자기 역할 문서를 먼저 읽는다.
2. `CODEX.md`와 `docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md`를 따른다.
3. 사용자 명령 1회당 Micro Stage 1개만 수행한다.
4. 자기 담당 파일 범위 밖을 수정하지 않는다.
5. 다른 역할 파일 수정이 필요하면 직접 수정하지 말고 인수인계 문서를 작성한다.
6. 완료 후 테스트/체크리스트/인수인계 문서를 남기고 멈춘다.
7. push는 사용자 승인 후에만 수행한다.
8. main 브랜치에 직접 commit하지 않는다.

---

## 4. 세션별 수정 가능 영역

### 4.1 Session A — PM/Integrator

허용:

```text
README.md
CODEX.md
docs/*
reports/session-handoff/*
reports/implementation/*
```

금지:

```text
src/ 핵심 코드 직접 구현
tests/ 핵심 테스트 직접 변경
app/ UI 코드 직접 변경
```

예외:

- 충돌 해결 또는 전체 정합성 패치가 필요하고 사용자가 승인한 경우

---

### 4.2 Session B — Backend/API Client

허용:

```text
src/ai_stock/toss_api/
src/ai_stock/config/
src/ai_stock/logging/
src/ai_stock/domain/api_models.py
tests/unit/test_config*.py
tests/contract/test_toss_api*.py
```

금지:

```text
app/
src/ai_stock/recommendation/
src/ai_stock/paper_trading/
src/ai_stock/risk/ 실주문 정책 변경
```

---

### 4.3 Session C — Data/DB

허용:

```text
src/ai_stock/repositories/
src/ai_stock/domain/entities.py
src/ai_stock/domain/db_models.py
scripts/init_db.py
tests/unit/test_repository*.py
tests/integration/test_db*.py
```

주의:

- DB schema 변경 시 사용자 승인 필요
- 기존 DB 삭제/초기화 금지
- migration/report 작성 필수

---

### 4.4 Session D — AI Recommendation

허용:

```text
src/ai_stock/recommendation/
src/ai_stock/services/recommendation_service.py
tests/unit/test_recommendation*.py
```

금지:

```text
실주문 호출
Toss API 직접 호출
DB 직접 SQL 실행
```

AI provider key가 필요하면 멈추고 사용자에게 요청한다.

---

### 4.5 Session E — Paper Trading/Risk

허용:

```text
src/ai_stock/paper_trading/
src/ai_stock/risk/
src/ai_stock/services/paper_trading_service.py
tests/unit/test_paper_trading*.py
tests/unit/test_risk*.py
```

주의:

- `ALLOW_REAL_ORDER=false` 기본값 유지
- 실주문 safety gate 약화 금지
- 수수료/세금 정책 변경 시 사용자 확인 필요

---

### 4.6 Session F — Frontend/UI

허용:

```text
app/
app/pages/
app/ui_components/
tests/ui/
```

금지:

```text
src/ai_stock/toss_api/ 직접 수정
src/ai_stock/repositories/ 직접 수정
src/ai_stock/risk/ 직접 수정
```

규칙:

- UI는 service layer만 호출
- UI에서 Toss API 직접 호출 금지
- UI에서 DB 직접 접근 금지
- UI에서 추천 점수/체결 로직 직접 계산 금지

---

### 4.7 Session G — QA/Test/Logging

허용:

```text
tests/
src/ai_stock/logging/
src/ai_stock/reports/
reports/test-results/
reports/error-logs/
```

금지:

```text
기능 로직 대규모 변경
UI 기능 추가
API client 동작 변경
```

---

### 4.8 Session H — Docs/Guide

허용:

```text
README.md
docs/
references/
templates/
roles/
```

금지:

```text
src/
app/
tests/
```

---

## 5. 인수인계 문서 규칙

다른 세션의 작업이 필요하면 아래 위치에 문서를 생성한다.

```text
reports/session-handoff/YYYYMMDD-HHMM-<from>-to-<to>.md
```

템플릿:

```markdown
# Session Handoff

- From:
- To:
- Related Micro Stage:
- Date:

## 요청 내용

## 필요한 이유

## 수정이 필요한 파일 후보

## 주의사항

## 완료 기준

## 사용자 승인 필요 여부
```

---

## 6. 충돌 방지 규칙

- 같은 파일을 두 세션이 동시에 수정하지 않는다.
- 역할 경계가 겹치면 PM/Integrator 세션이 조정한다.
- 공통 모델 변경은 PM/Integrator 승인 후 수행한다.
- DB schema 변경은 Data/DB 세션만 수행한다.
- UI 표시 변경은 Frontend/UI 세션만 수행한다.
- 실주문 safety gate 변경은 Paper Trading/Risk 세션도 단독으로 변경하지 않는다. 사용자 승인 필요.

---

## 7. 사용자 명령 예시

### Backend/API Client 세션

```text
roles/02_BACKEND_API_CLIENT_SESSION.md를 읽고, BE-MS-01 하나만 수행하세요.
완료 후 테스트 결과와 체크리스트를 작성하고 멈추세요.
```

### Frontend/UI 세션

```text
roles/03_FRONTEND_UI_SESSION.md를 읽고, FE-MS-01 하나만 수행하세요.
백엔드 로직은 수정하지 말고 service 호출부가 없으면 TODO로 남기세요.
```

### QA 세션

```text
roles/07_QA_TEST_LOGGING_SESSION.md를 읽고, 현재 구현된 범위의 테스트 누락만 점검하세요.
기능 코드는 수정하지 말고 필요한 수정 요청을 handoff로 남기세요.
```

---

## 8. 최종 원칙

```text
역할은 작게
변경은 작게
테스트는 매번
보고는 명확하게
사용자 승인은 자주
다음 단계는 기다리기
```


---

### 4.9 Session I — Git/Version Control

허용:

```text
.gitignore
README.md
CODEX.md
docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md
docs/27_ROLE_BASED_GIT_WORKFLOW.md
roles/09_GIT_VERSION_CONTROL_SESSION.md
templates/git_commit_checklist_template.md
templates/git_push_approval_request_template.md
reports/git/**
```

금지:

```text
src/** 기능 코드 수정
app/** UI 코드 수정
tests/** 테스트 코드 수정
사용자 승인 없는 push
main 직접 commit
force push
```

참조 문서:

- `roles/09_GIT_VERSION_CONTROL_SESSION.md`
- `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`
- `docs/27_ROLE_BASED_GIT_WORKFLOW.md`
