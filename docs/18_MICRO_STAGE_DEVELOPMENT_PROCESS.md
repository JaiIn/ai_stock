# 18. 초세분화 개발 단계와 사용자 확인 프로세스

이 문서는 한 번에 너무 많은 코드 변경이 발생하는 것을 막고, 사용자가 더 자주 확인할 수 있도록 Codex의 개발 단위를 **Micro Stage**로 세분화하는 규칙을 정의한다.

핵심 원칙은 다음과 같다.

> 큰 Milestone을 바로 완료하려고 하지 않는다.  
> Milestone을 여러 개의 Micro Stage로 나누고, 각 Micro Stage마다 구현 → 테스트 → 보고 → 사용자 승인 대기를 반복한다.

---

## 1. Micro Stage 정의

Micro Stage는 Codex가 한 번에 처리할 수 있는 가장 작은 개발 단위다.

권장 크기:

- 변경 파일: 1~5개 이내
- 구현 범위: 하나의 기능 또는 하나의 설정 단위
- 테스트 범위: 해당 기능에 대한 최소 테스트 1개 이상
- 예상 결과: 사용자가 변경 내용을 이해하고 승인할 수 있을 정도로 작아야 함

예시:

| 나쁜 단위 | 좋은 Micro Stage |
|---|---|
| Toss API Client 전체 구현 | OAuth 토큰 응답 모델만 구현 |
| UI 전체 구현 | 관심종목 목록 화면만 구현 |
| 추천 엔진 전체 구현 | RSI 계산 함수와 테스트만 구현 |
| 모의투자 전체 구현 | 모의 주문 데이터 모델만 구현 |

---

## 2. Micro Stage 실행 순서

Codex는 모든 개발 작업을 아래 순서로 수행한다.

```text
1. 현재 Micro Stage 목표 확인
2. 영향 범위 확인
3. 구현 전 계획 작성
4. 최소 코드 변경
5. 최소 테스트 작성 또는 갱신
6. 테스트 실행
7. 결과 로그 저장
8. Micro Stage 완료 체크리스트 작성
9. 사용자에게 요약 보고
10. 사용자의 다음 명령 대기
```

사용자가 `다음 단계 진행`, `계속`, `승인`, `MS-xx 진행` 같은 명령을 주기 전까지 다음 Micro Stage로 넘어가면 안 된다.

---

## 3. Micro Stage 상태값

모든 Micro Stage는 아래 상태 중 하나를 가진다.

| Status | 의미 | 다음 행동 |
|---|---|---|
| `NOT_STARTED` | 아직 시작하지 않음 | 사용자 명령 후 시작 |
| `IN_PROGRESS` | 진행 중 | 구현/테스트 수행 |
| `COMPLETED` | 정상 완료 | 사용자 승인 대기 |
| `COMPLETED_WITH_WARNINGS` | 완료했지만 주의사항 있음 | 사용자 확인 후 다음 단계 |
| `BLOCKED_USER_INPUT_REQUIRED` | 사용자 입력 필요 | 입력 요청 후 대기 |
| `BLOCKED_APPROVAL_REQUIRED` | 위험 작업 승인 필요 | 승인 요청 후 대기 |
| `FAILED` | 테스트 또는 구현 실패 | 수정 방향 보고 후 대기 |
| `SKIPPED` | 사용자 승인으로 건너뜀 | 사유 기록 |

---

## 4. 사용자 확인이 필요한 시점

아래 경우에는 반드시 멈추고 사용자 확인을 받아야 한다.

### 4.1 모든 Micro Stage 완료 시

작은 구현 단위 하나가 끝날 때마다 멈춘다.

예시:

```text
MS-02.01 OAuth 설정 모델 구현을 완료했습니다.
테스트 결과: PASS
생성/수정 파일: src/config/settings.py, tests/test_settings.py
다음 후보: MS-02.02 Secret masking 구현
현재 단계가 종료되었습니다. 다음 명령을 기다립니다.
```

### 4.2 실제 인증 정보가 필요한 경우

다음 값이 필요한 경우 Codex는 임의값을 만들지 않는다.

- Toss API Client ID
- Toss API Client Secret
- OAuth Access Token
- Refresh Token이 존재하는 경우 해당 값
- accountSeq 또는 계좌 선택값
- 실 API 호출 승인 여부
- OpenAI API Key 또는 다른 LLM API Key

Codex는 사용자가 안전하게 `.env` 또는 OS Secret Manager에 직접 입력하도록 안내하고 대기한다.

### 4.3 외부 API Live Test가 필요한 경우

Mock/fixture 테스트가 끝났더라도 실제 Toss API를 호출하기 전에는 사용자 확인을 받아야 한다.

필수 확인 항목:

- `.env`에 인증 정보 입력 완료 여부
- 호출 대상 API가 read-only인지 여부
- 호출 횟수와 예상 API 범위
- 로그에 민감값이 남지 않는지 여부
- 실주문 API를 호출하지 않는지 여부

### 4.4 스키마/DB 마이그레이션이 필요한 경우

로컬 DB 스키마가 바뀌거나 기존 데이터가 영향을 받을 수 있으면 사용자에게 알려야 한다.

예시:

```text
다음 작업은 DB 테이블 구조를 변경합니다.
기존 로컬 데이터가 있으면 백업이 필요할 수 있습니다.
진행하려면 `DB 변경 승인`이라고 입력해 주세요.
```

### 4.5 실주문 기능 관련 작업

v0.1에서는 실제 주문 API 호출을 금지한다.

다만 코드상 주문 API 타입/guard/test를 작성하는 경우에도 아래를 명확히 보고한다.

- 실제 API 호출 없음
- Mutation guard 적용
- `ALLOW_REAL_ORDER=false` 기본값 유지
- 주문 생성/정정/취소는 mock 또는 차단 테스트만 수행

---

## 5. Micro Stage 완료 기준 Definition of Done

각 Micro Stage는 아래 조건을 만족해야 완료로 표시할 수 있다.

```text
[필수]
- 요구사항 문서와 연결되어 있음
- 변경 파일 목록이 기록되어 있음
- 최소 1개 이상의 테스트 또는 검증 방법이 있음
- 테스트 결과가 reports/test-results/에 저장되어 있음
- 실패/경고/제약사항이 숨겨지지 않았음
- 민감 정보가 로그에 출력되지 않았음
- 다음 단계 후보가 제시되어 있음
- 사용자 명령 대기 상태로 종료됨

[해당 시]
- API live test 여부가 mock/live로 구분되어 있음
- DB 변경이면 백업/마이그레이션 안내가 있음
- 실주문 관련이면 safety gate 검증이 있음
- 사용자 입력이 필요하면 user input request 문서가 생성됨
```

---

## 6. 보고 파일 구조

Micro Stage 단위 보고 파일은 아래 구조를 사용한다.

```text
reports/
├── micro-stages/
│   ├── MS-00.01-source-sync.md
│   ├── MS-01.01-project-skeleton.md
│   ├── MS-02.01-oauth-settings.md
│   └── ...
├── stage-gates/
│   ├── M0-completion-checklist.md
│   └── ...
├── test-results/
│   ├── MS-02.01-pytest-output.txt
│   ├── MS-02.01-test-summary.md
│   └── latest-test-summary.md
├── implementation/
│   ├── MS-02.01-implementation-report.md
│   └── latest-implementation-report.md
├── user-requests/
│   ├── MS-02.04-user-input-required.md
│   └── MS-02.07-user-approval-required.md
└── errors/
    ├── MS-02.01-error-log.md
    └── latest-error-log.md
```

---

## 7. 명령 대기 규칙

Codex는 Micro Stage 종료 후 아래 문장을 반드시 포함한다.

```text
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

사용자가 내릴 수 있는 명령 예시:

```text
다음 단계 진행
계속
MS-02.02 진행
현재 단계 수정
테스트 다시 실행
실제 API 테스트 진행
여기서 중단
WBS 다시 보여줘
```

사용자의 명령이 모호하면 가장 안전한 방향으로 해석한다.

- `계속` → 다음 Micro Stage 1개만 진행
- `다음 단계 진행` → 다음 Micro Stage 1개만 진행
- `전부 진행` → 금지. 여러 단계 자동 진행 금지. 첫 번째 Micro Stage만 진행 후 다시 대기
- `실제 API 테스트까지 진행` → 필요한 인증 정보와 read-only 범위를 확인한 뒤 대기

---

## 8. 사용자 입력 요청 시 금지 사항

Codex는 아래 행동을 하지 않는다.

- Secret을 채팅에 붙여넣으라고 요구하지 않는다.
- 실제 토큰을 로그에 출력하지 않는다.
- `.env` 내용을 통째로 보여주지 않는다.
- 계좌번호/accountSeq 원문을 리포트에 쓰지 않는다.
- 사용자의 명시적 승인 없이 live API를 호출하지 않는다.
- 사용자의 명시적 승인 없이 실주문 관련 플래그를 변경하지 않는다.

---

## 9. 사용자 확인이 너무 잦아지는 경우의 처리

이 프로젝트는 안전성을 우선하므로 확인이 잦아지는 것을 허용한다.

다만 사용자가 명시적으로 다음과 같이 요청할 수 있다.

```text
M1 안에서는 3개 Micro Stage까지 묶어서 진행해도 돼
```

이 경우에도 Codex는 다음 제한을 지킨다.

- 인증 정보 필요 시 즉시 중단
- live API 호출 전 즉시 중단
- DB 파괴적 변경 전 즉시 중단
- 실주문 관련 설정 변경 전 즉시 중단
- 최대 3개 Micro Stage까지만 묶음 진행
- 묶음 진행 후 반드시 보고하고 대기

---

## 10. Codex 운영 요약

Codex는 개발자가 아니라 안전한 자동화 작업자처럼 행동해야 한다.

```text
작게 변경한다.
작게 테스트한다.
작게 보고한다.
자주 멈춘다.
사용자 승인 후 다음으로 간다.
```
