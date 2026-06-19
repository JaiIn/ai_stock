# 20. Codex 중단점과 사용자 확인 규칙

이 문서는 Codex가 언제 멈춰야 하는지, 사용자에게 어떤 형식으로 확인을 받아야 하는지 정의한다.

---

## 1. 최상위 규칙

Codex는 다음 상황에서 반드시 작업을 중단하고 사용자에게 보고한다.

```text
1. Micro Stage 1개 완료
2. 테스트 실패
3. 실제 인증 정보 필요
4. 실제 API 호출 필요
5. DB 구조 변경 또는 기존 데이터 영향 가능성 있음
6. 실주문 관련 기능/설정 변경 가능성 있음
7. 보안상 민감한 값 처리 방식 결정 필요
8. 추천 기준, 수수료/세금, 초기 자본 등 사용자 정책 결정 필요
9. 외부 문서 스펙과 기존 코드가 불일치
10. 사용자의 기존 지시와 충돌 가능성 있음
```

---

## 2. 사용자 확인 유형

| 확인 유형 | 코드 | 필요한 상황 | 사용자 응답 예시 |
|---|---|---|---|
| 일반 진행 승인 | `APPROVAL_CONTINUE` | Micro Stage 완료 후 다음 단계 진행 | `다음 단계 진행` |
| 민감정보 입력 필요 | `INPUT_SECRET_REQUIRED` | Client ID/Secret/API Key 필요 | `.env 입력 완료` |
| 계좌 선택 필요 | `INPUT_ACCOUNT_REQUIRED` | accountSeq 또는 계좌 선택 필요 | `1번 계좌로 진행` |
| Live API 승인 | `APPROVAL_LIVE_API` | 실제 Toss API read-only 호출 전 | `read-only live test 승인` |
| DB 변경 승인 | `APPROVAL_DB_CHANGE` | DB 스키마/마이그레이션 변경 전 | `DB 변경 승인` |
| 정책 결정 필요 | `DECISION_REQUIRED` | 추천 기준/초기 자본/수수료 가정 필요 | `초기 자본 1000만원` |
| 위험 작업 차단 | `BLOCKED_UNSAFE` | 실주문/민감정보 노출 위험 | `중단` 또는 `설계만 진행` |

---

## 3. 중단 보고 형식

Codex는 중단 시 아래 형식을 사용한다.

```md
# Codex Stop Point

## 상태

- Stop Type: APPROVAL_CONTINUE | INPUT_SECRET_REQUIRED | INPUT_ACCOUNT_REQUIRED | APPROVAL_LIVE_API | APPROVAL_DB_CHANGE | DECISION_REQUIRED | BLOCKED_UNSAFE
- Current Micro Stage: MS-xx.xx
- Status: COMPLETED | BLOCKED | FAILED

## 완료한 작업

- 항목 1
- 항목 2

## 검증 결과

| Check | Result | Evidence |
|---|---|---|
| Unit Test | PASS/FAIL/SKIPPED | reports/test-results/... |
| Lint | PASS/FAIL/SKIPPED | reports/test-results/... |
| Secret Masking | PASS/FAIL/SKIPPED | reports/test-results/... |

## 사용자 확인이 필요한 이유

- 이유를 구체적으로 작성

## 사용자가 선택할 수 있는 명령

- `다음 단계 진행`
- `현재 단계 수정`
- `테스트 다시 실행`
- `여기서 중단`

## 대기 문구

현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 4. 실제 토큰이 필요한 경우 예시

```md
# User Input Required

## 상태

- Stop Type: INPUT_SECRET_REQUIRED
- Current Micro Stage: MS-02.04
- Task: Toss OAuth2 token live test 준비

## 필요한 값

- TOSS_INVEST_CLIENT_ID
- TOSS_INVEST_CLIENT_SECRET

## 필요한 이유

Mock 기반 OAuth client 테스트는 완료했지만, 실제 Toss API 토큰 발급 테스트는 공식 개발자 콘솔에서 발급받은 인증 정보가 있어야 수행할 수 있습니다.

## 안전한 입력 방법

`.env` 파일에 직접 입력하세요.

```env
TOSS_INVEST_CLIENT_ID=...
TOSS_INVEST_CLIENT_SECRET=...
ALLOW_REAL_ORDER=false
```

## 금지 사항

- 이 값을 채팅에 그대로 붙여넣지 마세요.
- 로그에 원문 출력하지 않습니다.
- 테스트 결과에도 원문을 저장하지 않습니다.

## 다음 명령

입력이 끝나면 아래처럼 알려주세요.

```text
.env 입력 완료, read-only token test 진행
```

현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 5. 계좌 정보가 필요한 경우 예시

```md
# Account Selection Required

## 상태

- Stop Type: INPUT_ACCOUNT_REQUIRED
- Current Micro Stage: LIVE-03
- Task: 계좌 목록 조회 후 사용할 계좌 선택

## 필요한 결정

조회된 계좌 중 어떤 계좌를 read-only 조회 대상으로 사용할지 선택해야 합니다.

## 표시 원칙

- 계좌번호 전체를 표시하지 않습니다.
- accountSeq 전체를 표시하지 않습니다.
- 앞/뒤 일부만 마스킹해서 보여줍니다.

## 사용자 명령 예시

```text
첫 번째 계좌로 진행
두 번째 계좌로 진행
계좌 조회 중단
```

현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 6. Live API 호출 전 확인 예시

```md
# Live API Approval Required

## 상태

- Stop Type: APPROVAL_LIVE_API
- Current Micro Stage: LIVE-04
- Task: Read-only 시세 조회 1회 테스트

## 호출 예정 API

- Market Data read-only endpoint 1회

## 안전 조건

- 실주문 API 호출 없음
- `ALLOW_REAL_ORDER=false`
- 토큰/계좌 식별값 로그 원문 출력 금지
- 결과는 마스킹 후 저장

## 사용자 명령 예시

```text
read-only live test 승인
live test 중단
mock test만 유지
```

현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 7. 테스트 실패 시 처리

테스트 실패 시 Codex는 다음 Micro Stage로 넘어가지 않는다.

필수 행동:

1. 실패 로그 저장
2. 실패 원인 요약
3. 수정 방안 1~3개 제시
4. 사용자 명령 대기

보고 예시:

```text
MS-03.04 Market Snapshot 모델 테스트가 실패했습니다.
원인: Decimal 컬럼 변환 테스트에서 예상값과 실제값이 다릅니다.
수정 후보:
1. DB Numeric scale 조정
2. 테스트 기대값 조정
3. Repository에서 Decimal 변환 명시
현재 Micro Stage가 실패 상태로 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 8. 사용자 명령 해석 규칙

| 사용자 명령 | Codex 행동 |
|---|---|
| `계속` | 다음 Micro Stage 1개만 진행 |
| `다음 단계 진행` | 다음 Micro Stage 1개만 진행 |
| `MS-02.05 진행` | 지정한 Micro Stage만 진행 |
| `이번 Milestone 다 해줘` | 기본적으로 거절하지 말고 첫 Micro Stage만 진행 후 대기. 단, 사용자가 묶음 허용 범위를 명시하면 최대 3개까지 가능 |
| `실제 API 테스트 진행` | 인증 정보/호출 범위/안전조건 확인 후 대기 또는 승인된 read-only만 수행 |
| `실주문도 해줘` | v0.1에서는 거부하고 설계/문서/차단 테스트만 제안 |

---

## 9. 완료 보고의 최소 형식

Codex의 모든 Micro Stage 완료 보고는 최소한 아래 정보를 포함해야 한다.

```text
완료 Micro Stage: MS-xx.xx <이름>
상태: COMPLETED / COMPLETED_WITH_WARNINGS / BLOCKED / FAILED
변경 파일: n개
테스트: PASS / FAIL / SKIPPED
보고서: reports/micro-stages/...
다음 후보: MS-xx.xx <이름>
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 10. 사용자 승인 없이 절대 하지 말 것

- 다음 Micro Stage 자동 진행
- 실제 Toss API 호출
- 실제 토큰 발급 요청
- 계좌 목록 조회
- 보유 자산 조회
- 주문 가능 금액 조회
- DB 파괴적 변경
- `ALLOW_REAL_ORDER=true` 변경
- 주문 생성/정정/취소 API 호출
- Secret 원문 출력
