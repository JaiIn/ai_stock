# 17. 단계별 완료 체크리스트와 사용자 승인 게이트

이 문서는 Codex가 한 단계의 개발을 완료할 때마다 반드시 수행해야 하는 **완료 검증, 사용자 보고, 사용자 명령 대기** 절차를 정의한다.

핵심 원칙은 다음과 같다.

> Codex는 한 단계가 끝나면 다음 단계로 자동 진행하지 않는다.  
> 반드시 체크리스트와 결과 로그를 작성하고, 사용자에게 보고한 뒤, 사용자의 명시적인 다음 명령을 기다린다.

---

## 1. 적용 범위

이 규칙은 모든 개발 단계에 적용한다.

- 프로젝트 초기화
- 설정/로깅/마스킹
- Toss API 인증
- Toss API 조회 클라이언트
- DB/Repository
- 추천 엔진
- 모의투자 엔진
- UI
- 테스트/리포트
- 배포/실행
- 실제 API 연동 검증
- 실주문 기능 검토 또는 활성화 여부 판단

---

## 2. 절대 규칙

Codex는 아래 규칙을 어기면 안 된다.

1. **단계 완료 후 자동으로 다음 단계로 넘어가지 않는다.**
2. **단계마다 완료 체크리스트를 작성한다.**
3. **테스트 결과, 에러 로그, 구현 요약을 남긴다.**
4. **사용자 입력이 필요한 값은 임의로 만들지 않는다.**
5. **토큰, API Key, Client Secret, 계좌 식별값, 계좌 비밀번호, 실계좌 관련 값이 필요하면 사용자에게 요청하고 대기한다.**
6. **민감값을 채팅, 로그, 리포트, 화면에 원문 출력하지 않는다.**
7. **실제 주문 API는 v0.1에서 호출하지 않는다.**
8. **사용자의 명시적 승인 없이 `ALLOW_REAL_ORDER=true`로 변경하지 않는다.**
9. **테스트가 실패한 상태에서 완료로 표시하지 않는다.**
10. **임시 mock 값으로 통과한 테스트와 실제 API 연동 테스트를 구분해서 보고한다.**

---

## 3. 단계 완료 시 필수 산출물

각 단계가 끝날 때마다 아래 파일을 생성하거나 갱신한다.

```text
reports/
├── stage-gates/
│   ├── M0-completion-checklist.md
│   ├── M1-completion-checklist.md
│   ├── M2-completion-checklist.md
│   └── ...
├── test-results/
│   ├── latest-pytest-output.txt
│   └── latest-test-summary.md
├── implementation/
│   └── latest-implementation-report.md
└── errors/
    └── latest-error-log.md
```

단계별 파일명은 WBS ID와 일치시킨다.

예시:

```text
reports/stage-gates/M2-toss-api-client-completion-checklist.md
```

---

## 4. 단계 완료 체크리스트 템플릿

Codex는 각 단계 종료 시 아래 형식으로 체크리스트를 작성한다.

```md
# Stage Completion Checklist

## Stage

- Stage ID: M2
- Stage Name: Toss API Client
- Completed At: YYYY-MM-DD HH:mm:ss KST
- Status: COMPLETED | COMPLETED_WITH_WARNINGS | BLOCKED | FAILED

## 1. 구현 완료 항목

- [ ] 요구사항 문서 확인
- [ ] 관련 코드 구현
- [ ] 설정값 반영
- [ ] 테스트 코드 작성
- [ ] 문서 업데이트
- [ ] 로그/리포트 생성

## 2. 테스트 결과

| Test Type | Command | Result | Output File |
|---|---|---|---|
| Lint | `ruff check .` | PASS/FAIL/SKIPPED | `reports/test-results/latest-ruff-output.txt` |
| Unit Test | `pytest -q` | PASS/FAIL/SKIPPED | `reports/test-results/latest-pytest-output.txt` |
| Contract Test | `pytest tests/contract -q` | PASS/FAIL/SKIPPED | `reports/test-results/latest-contract-output.txt` |
| Manual Run | `streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501` | PASS/FAIL/SKIPPED | `reports/test-results/latest-manual-run.md` |

## 3. 생성/수정 파일

| Path | Action | Description |
|---|---|---|
| `src/...` | CREATED/MODIFIED | 설명 |
| `tests/...` | CREATED/MODIFIED | 설명 |
| `docs/...` | MODIFIED | 설명 |

## 4. 검증한 안전 조건

- [ ] Secret masking 동작 확인
- [ ] 실제 주문 API 비활성 상태 확인
- [ ] 민감 정보 로그 미출력 확인
- [ ] Decimal 기반 금액 계산 확인
- [ ] mock 테스트와 live 테스트 구분 확인

## 5. 사용자 입력 필요 여부

- Required: YES/NO
- Needed Item:
  - 예: Toss API Client ID
  - 예: Toss API Client Secret
  - 예: OAuth Access Token
  - 예: accountSeq 또는 계좌 선택
  - 예: 실제 API 호출 승인
- Why Needed:
  - 이 값이 없으면 실제 Toss API 연동 테스트를 수행할 수 없음
- Safe Input Method:
  - `.env`에 사용자가 직접 입력
  - 터미널 프롬프트에서 입력
  - OS secret manager 사용
- Do Not Print:
  - 입력값 원문 출력 금지

## 6. 남은 이슈

- [ ] 이슈 1
- [ ] 이슈 2

## 7. 다음 단계 제안

다음 단계 후보:

- `M3 DB/Repository 구현 진행`
- `M2 실제 API 연동 테스트 진행`
- `현재 단계 수정/보완`

## 8. 사용자 명령 대기

현재 단계가 종료되었습니다.  
다음 명령을 입력해 주세요.

예시 명령:

- `다음 단계 진행`
- `실제 API 연동 테스트 진행`
- `체크리스트를 보고 수정해줘`
- `여기서 중단`
- `M2부터 다시 진행`
```

---

## 5. 사용자 입력 요청 프로토콜

개발 중 사용자 입력이 필요한 경우 Codex는 즉시 작업을 멈추고 아래 형식으로 요청한다.

```md
# User Input Required

## 현재 작업

- Stage ID: M2
- Task: OAuth2 token 발급 테스트

## 필요한 사용자 입력

- Toss API Client ID
- Toss API Client Secret

## 필요한 이유

실제 Toss API 토큰 발급 테스트를 수행하려면 공식 개발자 콘솔에서 발급받은 인증 정보가 필요합니다.
Mock 테스트는 완료할 수 있지만, 실제 API 연동 검증은 이 값 없이는 진행할 수 없습니다.

## 안전한 입력 방법

아래 파일을 직접 수정하세요.

```bash
.env
```

필수 항목:

```env
TOSS_INVEST_CLIENT_ID=여기에_입력
TOSS_INVEST_CLIENT_SECRET=여기에_입력
TOSS_INVEST_BASE_URL=https://open-api.tossinvest.com
ALLOW_REAL_ORDER=false
```

## 보안 주의

- 이 값을 채팅에 그대로 붙여넣지 마세요.
- 로그, 리포트, 화면에 원문 출력하지 않습니다.
- 입력 후 `설정 완료, 계속 진행`이라고 알려주세요.

## 대기 상태

사용자 입력을 기다립니다.  
다음 명령이 오기 전까지 다음 단계로 진행하지 않습니다.
```

---

## 6. 사용자 승인 게이트 상태값

Codex는 단계 종료 시 상태를 명확히 표시한다.

| Status | 의미 | 다음 행동 |
|---|---|---|
| `COMPLETED` | 모든 구현/테스트 완료 | 사용자 승인 대기 |
| `COMPLETED_WITH_WARNINGS` | 핵심 기능은 완료, 경고/제약 존재 | 경고 설명 후 사용자 승인 대기 |
| `BLOCKED_USER_INPUT_REQUIRED` | 사용자 입력 필요 | 입력 요청 후 대기 |
| `BLOCKED_EXTERNAL_API_REQUIRED` | 실제 API/네트워크/계정 승인 필요 | 필요한 조건 설명 후 대기 |
| `FAILED` | 테스트 또는 구현 실패 | 실패 원인/수정안 보고 후 대기 |
| `SKIPPED_BY_POLICY` | 안전 정책상 수행하지 않음 | 이유 설명 후 대기 |

---

## 7. 실제 토큰/계정 정보가 필요한 대표 상황

아래 상황에서는 Codex가 임의값으로 진행하면 안 된다.

| 상황 | 필요한 사용자 입력 | Codex 행동 |
|---|---|---|
| OAuth2 토큰 실제 발급 | Client ID, Client Secret | `.env` 입력 요청 후 대기 |
| 계좌 목록 조회 | 유효한 Access Token | 입력 또는 발급 완료 요청 후 대기 |
| 보유 주식 조회 | accountSeq 또는 계좌 선택 | 계좌 목록 출력 시 마스킹 후 선택 요청 |
| 매수 가능 금액 조회 | accountSeq | 계좌 식별값 마스킹 후 선택 요청 |
| 실제 API rate limit 검증 | 사용자 승인 | 호출 횟수와 예상 위험 안내 후 대기 |
| 실주문 기능 검토 | 별도 명시 승인 | v0.1에서는 기본 거절, 문서화만 수행 |
| 실주문 활성화 | 별도 안전 설계/승인/환경 분리 | v0.1 범위 밖으로 보고 후 대기 |

---

## 8. Mock-first 개발 원칙

사용자 입력이 없어도 진행 가능한 범위는 다음과 같다.

- 프로젝트 구조 생성
- 설정 로더 구현
- secret masking 구현
- mock OAuth 응답 기반 token client 테스트
- fixture 기반 market data parsing 테스트
- repository/unit test
- 추천 엔진 unit test
- 모의투자 엔진 unit test
- Streamlit 화면 뼈대
- 주문 API 차단 테스트

사용자 입력이 없으면 진행하면 안 되는 범위는 다음과 같다.

- 실제 OAuth token 발급
- 실제 계좌 목록 조회
- 실제 보유 주식 조회
- 실제 매수 가능 금액 조회
- 실제 시세 API 대량 호출
- 실계좌 주문 생성/정정/취소

---

## 9. Codex가 사용자에게 보고해야 하는 메시지 형식

단계가 완료되면 Codex는 채팅 또는 `reports/stage-gates/*.md`에 아래 요약을 제공한다.

```md
## 단계 완료 보고

- 완료 단계: M2 Toss API Client
- 상태: COMPLETED_WITH_WARNINGS
- 구현 요약:
  - OAuth2 mock token client 구현
  - 401 refresh 처리 구현
  - 429 retry 처리 구현
  - read-only endpoint wrapper 구현
  - 주문 API mutation guard 구현
- 테스트:
  - ruff: PASS
  - pytest: PASS
  - contract mock test: PASS
  - live API test: SKIPPED
- 생성 리포트:
  - `reports/stage-gates/M2-toss-api-client-completion-checklist.md`
  - `reports/test-results/latest-test-summary.md`
  - `reports/implementation/latest-implementation-report.md`
- 사용자 입력 필요:
  - YES
  - 실제 Toss API 토큰 발급 검증을 위해 Client ID/Secret이 필요합니다.
- 다음 선택지:
  1. `실제 API 연동 테스트 진행`
  2. `다음 단계 진행`
  3. `현재 단계 보완`
  4. `중단`

사용자 명령을 기다립니다.
```

---

## 10. 단계별 권장 게이트

| Milestone | 종료 시 반드시 확인할 것 | 사용자 대기 조건 |
|---|---|---|
| M0 문서/스펙 확인 | OpenAPI 최신성, 실주문 제외 정책 | 스펙 검증 결과 보고 후 대기 |
| M1 프로젝트 초기화 | 설치, lint, 기본 pytest | 초기 구조 확인 요청 후 대기 |
| M2 Toss API Client | mock 테스트, token cache, retry, 주문 차단 | 실제 API 토큰 필요 시 대기 |
| M3 DB/Repository | migration/CRUD 테스트 | DB 구조 확인 요청 후 대기 |
| M4 추천 엔진 | 점수 산식/경고필터/AI 설명 테스트 | 추천 기준 확인 요청 후 대기 |
| M5 모의투자 | 체결/평단/PnL 계산 테스트 | 수수료/세금 가정 확인 요청 후 대기 |
| M6 UI | 앱 실행, 탭 동작 | 화면 구성 확인 요청 후 대기 |
| M7 품질/보고서 | 전체 테스트, 리포트 | v0.1 완료 승인 요청 후 대기 |

---

## 11. Codex 구현 요구사항

Codex는 프로젝트에 아래 유틸리티를 구현하는 것을 권장한다.

```text
src/ai_stock/stage_gate.py
```

역할:

- 단계 완료 체크리스트 생성
- 테스트 결과 요약 수집
- 사용자 입력 필요 여부 기록
- 다음 단계 진행 가능 여부 판단
- `STOP_AND_WAIT` 상태 출력

예시 인터페이스:

```python
from trader.stage_gate import StageGate, StageStatus

stage = StageGate(stage_id="M2", stage_name="Toss API Client")
stage.add_completed_item("OAuth2 mock token client implemented")
stage.add_test_result("pytest", "pytest -q", "PASS", "reports/test-results/latest-pytest-output.txt")
stage.require_user_input(
    item="TOSS_INVEST_CLIENT_ID / TOSS_INVEST_CLIENT_SECRET",
    reason="실제 OAuth2 token 발급 검증 필요",
    safe_method="사용자가 .env 파일에 직접 입력",
)
stage.write_report("reports/stage-gates/M2-toss-api-client-completion-checklist.md")
stage.stop_and_wait()
```

`stop_and_wait()`는 실제 애플리케이션에서는 다음 단계 자동 실행을 막고, Codex 작업에서는 사용자에게 명령 대기 메시지를 출력하는 의미로 사용한다.

---

## 12. 사용자 명령 예시

Codex가 대기 중일 때 사용자는 다음과 같이 명령할 수 있다.

```text
다음 단계 진행
```

```text
실제 API 연동 테스트 진행. .env에 값 입력 완료.
```

```text
현재 단계 체크리스트 보여줘.
```

```text
M2에서 실패한 테스트부터 수정해줘.
```

```text
여기서 중단하고 ZIP으로 묶어줘.
```

```text
실주문 관련 코드는 만들지 말고 문서만 남겨줘.
```

---

## 13. 완료 정의

각 단계는 아래 조건을 모두 만족해야 완료로 인정한다.

- 구현 항목이 WBS와 일치한다.
- 테스트 명령을 실행했거나, 실행 불가 사유를 명확히 기록했다.
- 실패한 테스트가 있으면 원인과 수정 계획을 기록했다.
- 민감정보가 노출되지 않았음을 확인했다.
- 실주문 차단 정책을 위반하지 않았다.
- 사용자 입력이 필요한 경우 그 이유와 안전한 입력 방법을 명확히 설명했다.
- 다음 단계로 넘어가기 전 사용자 명령 대기 상태에 진입했다.



---

## 9. Micro Stage 우선 적용

기존 Stage Gate는 Milestone 종료 시점의 큰 체크포인트다. 실제 개발 중에는 더 작은 단위인 Micro Stage Gate를 우선 적용한다.

우선순위:

```text
1순위: Micro Stage 완료 후 사용자 명령 대기
2순위: Milestone 완료 후 사용자 명령 대기
3순위: 최종 v0.1 완료 후 사용자 승인 대기
```

즉, `M2 Toss API Client` 전체를 완료한 뒤 한 번만 보고하는 것이 아니라, `MS-02.01`, `MS-02.02`, `MS-02.03`처럼 작은 작업 하나마다 보고하고 멈춘다.

Micro Stage 보고에는 아래 파일을 사용한다.

- `templates/micro_stage_completion_checklist_template.md`
- `templates/micro_stage_test_summary_template.md`
- `templates/user_approval_request_template.md`
- `templates/development_status_board_template.md`

자세한 Micro Stage 목록은 `docs/19_DETAILED_MICRO_WBS.md`를 따른다.
