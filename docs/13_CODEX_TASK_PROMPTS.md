# 13. Codex 작업 프롬프트 모음

## 공통 지시 — 모든 Prompt에 적용

아래 모든 작업 프롬프트에는 다음 지시가 공통으로 적용된다.

```text
작업을 완료한 뒤 자동으로 다음 단계로 넘어가지 마라.
반드시 reports/stage-gates/에 해당 단계 완료 체크리스트를 작성하라.
ruff/pytest 등 실행 가능한 테스트를 수행하고 결과를 reports/test-results/에 저장하라.
구현 요약은 reports/implementation/latest-implementation-report.md에 기록하라.
사용자 입력이 필요한 값이 있으면 임의값으로 대체하지 말고, 필요한 이유와 안전한 입력 방법을 설명한 뒤 사용자 명령을 기다려라.
실제 토큰, API Key, Client Secret, accountSeq, 실 API 호출 승인, 실주문 활성화가 필요한 경우 반드시 사용자에게 알리고 대기하라.
단계 종료 메시지에는 `현재 단계가 종료되었습니다. 다음 명령을 기다립니다.`를 포함하라.
```

## Prompt 1 — 프로젝트 생성

```text
이 저장소에 Python 3.11 기반 Streamlit 프로젝트를 생성해라.
문서의 04_PROJECT_STRUCTURE.md 구조를 따르고, requirements.txt, requirements-dev.txt, pyproject.toml, Makefile, .env.example을 작성해라.
실주문 기능은 v0.1에서 금지한다.
구현 후 ruff와 pytest가 실행될 수 있는 최소 테스트를 추가해라.
```

## Prompt 2 — 설정/로깅/마스킹

```text
src/ai_stock/config/settings.py와 src/ai_stock/core/logging.py, src/ai_stock/core/masking.py를 구현해라.
.env 기반 설정 로더, secret masking, 민감 헤더 마스킹, logs/app.log/error.log 생성을 포함해라.
tests/unit/test_config.py와 tests/unit/test_secret_masking.py를 작성하고 통과시켜라.
```

## Prompt 3 — Toss API Client

```text
토스증권 Open API client를 구현해라.
OAuth2 token 발급, token cache, 401 refresh, 429 Retry-After backoff, X-Request-Id 로깅을 포함해라.
read-only endpoint만 실제 구현하고, 주문 생성/정정/취소는 LiveTradingDisabledError를 발생시켜라.
respx fixture 기반 테스트를 작성해라.
```

## Prompt 4 — 추천 엔진

```text
추천 엔진을 구현해라.
캔들 기반 이동평균/변동성/모멘텀 점수를 계산하고, stock warnings에 따라 BLOCKED 또는 감점을 적용해라.
AI 설명 생성 모듈은 실패 시 fallback 템플릿을 사용하고, 금지 표현 guardrail을 적용해라.
```

## Prompt 5 — 모의투자 엔진

```text
paper portfolio, paper order, paper position 모델과 서비스를 구현해라.
MARKET/LIMIT 체결 시뮬레이션, 평균단가, 실현/미실현 손익, 수수료 추정을 포함해라.
Decimal만 사용하고 float 사용을 피하라.
```

## Prompt 6 — Streamlit UI

```text
app/streamlit_app.py를 구현해라.
탭은 Dashboard, Watchlist, Market Data, Recommendation, Paper Trading, Logs/Reports로 구성해라.
Secret은 절대 화면에 노출하지 말고, 실주문 버튼은 만들지 마라.
```

## Prompt 7 — 테스트/리포트 완성

```text
필수 테스트를 모두 작성하고 통과시켜라.
pytest 출력은 reports/test-results/latest-pytest-output.txt에 저장하고,
요약은 reports/test-results/latest-test-summary.md에 생성해라.
구현 내용은 reports/implementation/latest-implementation-report.md에 기록해라.
```


## Prompt 8 — 단계 게이트 유틸리티

```text
src/ai_stock/reports/stage_gate.py를 구현해라.
StageGate, StageStatus, TestResult, FileChange, UserInputRequirement 모델을 만들고,
단계 완료 체크리스트 markdown을 reports/stage-gates/에 생성하는 기능을 구현해라.
사용자 입력이 필요한 경우 BLOCKED_USER_INPUT_REQUIRED 상태로 기록하고,
다음 단계 자동 진행을 막는 STOP_AND_WAIT 메시지를 출력해라.
tests/unit/test_stage_gate.py를 작성하고 통과시켜라.
작업 완료 후 reports/stage-gates/M1-stage-gate-utility-completion-checklist.md를 작성하고 사용자 명령을 기다려라.
```

## Prompt 9 — 실제 Toss API 인증값 필요 시 대기

```text
Toss API 실제 OAuth2 token 발급 또는 계좌 조회 테스트가 필요한 시점이면 작업을 멈춰라.
필요한 값이 무엇인지 명확히 설명하고, 사용자가 .env 파일에 직접 입력하도록 안내하라.
민감값을 채팅에 붙여넣으라고 요구하지 마라.
사용자가 `설정 완료, 계속 진행`이라고 명령하기 전까지 live API 테스트를 실행하지 마라.
Mock 테스트는 완료 여부를 별도로 보고하라.
```


---

# Micro Stage 기반 Codex 프롬프트

## 기본 시작 프롬프트

```text
CODEX.md, docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md, docs/19_DETAILED_MICRO_WBS.md, docs/20_CODEX_STOP_AND_CONFIRMATION_RULES.md를 먼저 읽어라.

이 프로젝트는 Micro Stage 단위로만 진행한다.
사용자 명령 1회에 Micro Stage 1개만 수행하라.
완료 후 reports/micro-stages/에 체크리스트를 작성하고, 테스트 결과를 reports/test-results/에 저장하고, 다음 명령을 기다려라.

먼저 MS-00.01만 수행하라.
```

## 다음 단계 진행 프롬프트

```text
직전 Micro Stage의 보고서와 테스트 결과를 확인하라.
문제가 없으면 docs/19_DETAILED_MICRO_WBS.md 기준 다음 Micro Stage 1개만 진행하라.
완료 후 사용자 명령을 기다려라.
```

## 실제 인증 정보가 필요한 경우 프롬프트

```text
실제 Toss API Client ID/Secret, Access Token, accountSeq 또는 OpenAI API Key가 필요하면 즉시 작업을 중단하라.
templates/user_input_request_template.md 형식으로 사용자 입력 요청 파일을 만들고, 채팅에는 안전한 입력 방법만 안내하라.
민감값을 채팅이나 로그에 출력하지 말라.
```

## Live API 테스트 진행 프롬프트

```text
Live API 테스트는 사용자가 명시적으로 승인한 경우에만 진행한다.
read-only endpoint만 호출하라.
주문 생성/정정/취소 API는 절대 호출하지 말라.
호출 전 호출 대상, 호출 횟수, 안전 조건을 보고하고 사용자 승인을 받아라.
```

## 테스트 실패 시 프롬프트

```text
테스트가 실패하면 다음 Micro Stage로 넘어가지 말라.
실패 로그를 reports/errors/와 reports/test-results/에 저장하라.
원인, 수정 후보, 재실행 명령을 요약하고 사용자 명령을 기다려라.
```


## Prompt 10 — GitHub 단계별 커밋

```text
CODEX.md, docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md, docs/27_ROLE_BASED_GIT_WORKFLOW.md를 읽어라.
현재 Micro Stage 변경사항만 대상으로 git status와 git diff를 확인하라.
templates/git_commit_checklist_template.md 형식으로 reports/git/에 커밋 체크리스트를 작성하라.
테스트가 통과하고 민감정보가 없는 경우에만 Micro Stage 단위 커밋을 생성하라.
사용자 승인 없이 git push를 실행하지 마라.
커밋 후 branch, commit hash, 테스트 결과, push 대기 상태를 보고하고 멈춰라.
```

## Prompt 11 — 빈 GitHub Repository 초기화

```text
Repository는 https://github.com/JaiIn/ai_stock 이다.
빈 저장소를 clone하고 ai_stock 프로젝트 문서와 초기 구조를 배치하라.
MS-00.01 범위의 초기 문서/구조 커밋 후보만 생성하라.
.env.local, DB, logs, 민감정보는 절대 포함하지 마라.
커밋 후 push는 하지 말고 사용자에게 `push 진행` 명령을 요청한 뒤 대기하라.
```
