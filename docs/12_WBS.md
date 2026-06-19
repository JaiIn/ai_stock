# 12. WBS




## 초세분화 실행 원칙

이 WBS의 Milestone은 큰 방향만 정의한다. 실제 Codex 실행은 `docs/19_DETAILED_MICRO_WBS.md`의 Micro Stage 단위를 따른다.

기본 실행 단위:

```text
사용자 명령 1회 = Micro Stage 1개
```

Milestone 전체를 한 번에 진행하지 않는다. 각 Micro Stage 종료 시 `reports/micro-stages/`에 완료 체크리스트를 작성하고 사용자 명령을 기다린다.

자세한 규칙:

- `docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md`
- `docs/19_DETAILED_MICRO_WBS.md`
- `docs/20_CODEX_STOP_AND_CONFIRMATION_RULES.md`


## 공통 Stage Gate 규칙

모든 Milestone은 완료 직후 다음 절차를 반드시 수행한다.

| Gate ID | 작업 | 완료 조건 |
|---|---|---|
| G-1 | 단계 완료 체크리스트 작성 | `reports/stage-gates/<milestone>-completion-checklist.md` 생성 |
| G-2 | 테스트 결과 저장 | `reports/test-results/`에 최신 결과 저장 |
| G-3 | 구현 리포트 저장 | `reports/implementation/latest-implementation-report.md` 갱신 |
| G-4 | 사용자 입력 필요 여부 판단 | 토큰/API Key/계좌정보/승인 필요 여부 명시 |
| G-5 | 사용자 명령 대기 | 다음 단계 자동 진행 금지, 사용자 명령 수신 후 진행 |

사용자 입력이 필요한 경우 상태를 `BLOCKED_USER_INPUT_REQUIRED`로 표시하고, `templates/user_input_request_template.md` 형식으로 요청한다.

## Milestone 0 — 문서/스펙 확인

| ID | 작업 | 완료 조건 |
|---|---|---|
| M0-1 | 공식 OpenAPI JSON 다운로드/저장 | `references/openapi.latest.json` 또는 링크 기록 |
| M0-2 | endpoint matrix 검증 | path/method/schema 최신화 |
| M0-3 | v0.1 실주문 제외 정책 확정 | `test_no_real_order_policy.py` 작성 |
| M0-G | M0 단계 종료 게이트 | `reports/stage-gates/M0-completion-checklist.md` 작성 후 사용자 명령 대기 |

## Milestone 1 — 프로젝트 초기화

| ID | 작업 | 완료 조건 |
|---|---|---|
| M1-1 | 디렉토리 생성 | 구조 문서와 일치 |
| M1-2 | 패키지 파일 생성 | install 성공 |
| M1-3 | 설정 로더 | `.env` 로딩 테스트 통과 |
| M1-4 | 로깅/마스킹 | secret masking 테스트 통과 |
| M1-G | M1 단계 종료 게이트 | `reports/stage-gates/M1-completion-checklist.md` 작성 후 사용자 명령 대기 |

## Milestone 2 — Toss API Client

| ID | 작업 | 완료 조건 |
|---|---|---|
| M2-1 | OAuth token client | token mock test 통과 |
| M2-2 | 공통 request wrapper | 401/429 retry 테스트 통과 |
| M2-3 | Market Data methods | fixture parsing 통과 |
| M2-4 | Stock/Market Info methods | fixture parsing 통과 |
| M2-5 | Account/Asset/Order Info methods | fixture parsing 통과 |
| M2-6 | Mutation guard | 실주문 차단 테스트 통과 |
| M2-G | M2 단계 종료 게이트 | `reports/stage-gates/M2-completion-checklist.md` 작성 후 사용자 명령 대기. 실제 토큰 필요 시 요청 후 대기 |

## Milestone 3 — DB/Repository

| ID | 작업 | 완료 조건 |
|---|---|---|
| M3-1 | SQLAlchemy models | DB 생성 성공 |
| M3-2 | watchlist repository | CRUD 테스트 통과 |
| M3-3 | market snapshot 저장 | 저장/조회 테스트 통과 |
| M3-4 | paper portfolio 저장 | 포트폴리오 테스트 통과 |
| M3-G | M3 단계 종료 게이트 | `reports/stage-gates/M3-completion-checklist.md` 작성 후 사용자 명령 대기 |

## Milestone 4 — 추천 엔진

| ID | 작업 | 완료 조건 |
|---|---|---|
| M4-1 | indicator 계산 | 샘플 캔들 테스트 통과 |
| M4-2 | score 계산 | rating 테스트 통과 |
| M4-3 | warning penalty | BLOCKED 테스트 통과 |
| M4-4 | AI explanation | prompt 생성 테스트 통과 |
| M4-5 | guardrail | 금지 표현 차단 테스트 통과 |
| M4-G | M4 단계 종료 게이트 | `reports/stage-gates/M4-completion-checklist.md` 작성 후 사용자 명령 대기. 추천 기준 확인 요청 |

## Milestone 5 — 모의투자

| ID | 작업 | 완료 조건 |
|---|---|---|
| M5-1 | paper order 생성 | 주문 저장 테스트 통과 |
| M5-2 | fill simulation | MARKET/LIMIT 테스트 통과 |
| M5-3 | position update | 평균단가/PnL 테스트 통과 |
| M5-4 | performance report | 수익률/MDD 계산 테스트 통과 |
| M5-G | M5 단계 종료 게이트 | `reports/stage-gates/M5-completion-checklist.md` 작성 후 사용자 명령 대기. 수수료/세금 가정 확인 요청 |

## Milestone 6 — UI

| ID | 작업 | 완료 조건 |
|---|---|---|
| M6-1 | Streamlit 기본 화면 | 앱 실행 |
| M6-2 | 관심종목 탭 | CRUD 가능 |
| M6-3 | 시세/추천 탭 | 추천 결과 표시 |
| M6-4 | 모의투자 탭 | paper order 생성/조회 |
| M6-5 | 로그/리포트 탭 | 최신 결과 표시 |
| M6-G | M6 단계 종료 게이트 | `reports/stage-gates/M6-completion-checklist.md` 작성 후 사용자 명령 대기. UI 확인 요청 |

## Milestone 7 — 품질/보고서

| ID | 작업 | 완료 조건 |
|---|---|---|
| M7-1 | ruff 적용 | `ruff check .` 통과 |
| M7-2 | pytest 통과 | `pytest -q` 통과 |
| M7-3 | test summary 생성 | reports 파일 존재 |
| M7-4 | implementation report 생성 | reports 파일 존재 |
| M7-5 | README 업데이트 | 설치/실행/테스트 문서화 |
| M7-G | M7 단계 종료 게이트 | `reports/stage-gates/M7-completion-checklist.md` 작성 후 v0.1 완료 승인 대기 |

---

## Local-only / role split WBS addendum

사용자 요구에 따라 v0.1 WBS는 로컬 전용 실행과 역할별 Codex 세션 분리를 반영한다.

추가 선행 작업:

| ID | 작업 | 담당 세션 | 완료 기준 |
|---|---|---|---|
| MS-00.00 | 로컬 전용 정책 확인 | PM/Integrator | 배포 관련 작업 제외 확인 |
| MS-00.01 | 확정 기술 스택 확인 | PM/Integrator | `docs/21` 검토 완료 |
| MS-00.02 | 로컬 세팅 가이드 확인 | PM/Integrator | `docs/22` 검토 완료 |
| MS-00.03 | 역할별 세션 배정 | PM/Integrator | `roles/` 문서 검토 완료 |
| MS-00.04 | 프론트엔드 결정 확인 | Frontend/UI | Streamlit v0.1 채택 확인 |

각 역할 세션은 자기 역할 문서에 정의된 파일 범위만 수정한다.
