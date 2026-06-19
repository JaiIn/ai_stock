# User Approval Required

## 0. 상태

- Request Type: APPROVAL_CONTINUE | APPROVAL_LIVE_API | APPROVAL_DB_CHANGE | DECISION_REQUIRED | BLOCKED_UNSAFE
- Current Micro Stage: MS-xx.xx
- Status: BLOCKED_APPROVAL_REQUIRED
- Created At: YYYY-MM-DD HH:mm:ss KST

---

## 1. 승인 또는 결정이 필요한 이유

```text
여기에 이유를 구체적으로 작성
```

---

## 2. 진행 시 수행할 작업

| Step | Action | Risk |
|---|---|---|
| 1 | 수행할 작업 | LOW/MEDIUM/HIGH |

---

## 3. 안전 조건

- [ ] 실주문 API 호출 없음
- [ ] Secret 원문 출력 없음
- [ ] 계좌 식별값 마스킹
- [ ] 변경 전 백업 또는 rollback 가능성 확인
- [ ] 실패 시 중단하고 보고

---

## 4. 사용자가 선택할 수 있는 명령

```text
승인, 진행
수정 후 진행
이번 단계 중단
mock 테스트만 진행
read-only live test 승인
DB 변경 승인
```

---

## 5. 대기 문구

사용자 승인이 필요합니다. 다음 명령을 기다립니다.
