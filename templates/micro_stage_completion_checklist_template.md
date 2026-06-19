# Micro Stage Completion Checklist

## 0. 기본 정보

- Micro Stage ID: MS-xx.xx
- Micro Stage Name:
- Parent Milestone: Mx
- Started At: YYYY-MM-DD HH:mm:ss KST
- Completed At: YYYY-MM-DD HH:mm:ss KST
- Status: NOT_STARTED | IN_PROGRESS | COMPLETED | COMPLETED_WITH_WARNINGS | BLOCKED_USER_INPUT_REQUIRED | BLOCKED_APPROVAL_REQUIRED | FAILED | SKIPPED

---

## 1. 이번 Micro Stage 목표

- 목표:
- 하지 않은 것:
- 다음 단계로 미룬 것:

---

## 2. 변경 범위

| Path | Action | Description |
|---|---|---|
| `src/...` | CREATED/MODIFIED/DELETED | 설명 |
| `tests/...` | CREATED/MODIFIED/DELETED | 설명 |
| `docs/...` | CREATED/MODIFIED/DELETED | 설명 |

---

## 3. 구현 내용

- [ ] 요구사항 문서 확인
- [ ] 구현 전 영향 범위 확인
- [ ] 최소 단위로 코드 변경
- [ ] 예외 처리 반영
- [ ] 로그/마스킹 영향 확인
- [ ] 문서 또는 주석 갱신

상세 요약:

```text
여기에 구현 요약 작성
```

---

## 4. 테스트/검증 결과

| Test Type | Command | Result | Output File |
|---|---|---|---|
| Unit Test | `pytest tests/... -q` | PASS/FAIL/SKIPPED | `reports/test-results/MS-xx.xx-pytest-output.txt` |
| Lint | `ruff check .` | PASS/FAIL/SKIPPED | `reports/test-results/MS-xx.xx-ruff-output.txt` |
| Type Check | `mypy src` | PASS/FAIL/SKIPPED | `reports/test-results/MS-xx.xx-mypy-output.txt` |
| Manual Check | 직접 실행 | PASS/FAIL/SKIPPED | `reports/test-results/MS-xx.xx-manual-check.md` |

테스트 요약:

```text
여기에 테스트 결과 요약 작성
```

---

## 5. 안전 조건 확인

- [ ] Secret 원문 출력 없음
- [ ] 계좌번호/accountSeq 원문 출력 없음
- [ ] `ALLOW_REAL_ORDER=false` 유지
- [ ] 실제 주문 API 호출 없음
- [ ] Mock test와 Live API test 구분
- [ ] 금액/수량/가격 계산에 `Decimal` 사용
- [ ] 에러 로그에 민감값 없음

---

## 6. 사용자 입력/승인 필요 여부

- Required: YES/NO
- Type: APPROVAL_CONTINUE | INPUT_SECRET_REQUIRED | INPUT_ACCOUNT_REQUIRED | APPROVAL_LIVE_API | APPROVAL_DB_CHANGE | DECISION_REQUIRED | BLOCKED_UNSAFE | NONE

필요한 경우:

| Needed Item | Why Needed | Safe Input Method |
|---|---|---|
| 예: TOSS_INVEST_CLIENT_ID | 실제 OAuth token test | `.env` 직접 입력 |

---

## 7. 남은 이슈/주의사항

- [ ] 이슈 1
- [ ] 이슈 2

---

## 8. 다음 Micro Stage 후보

| Candidate | Description | Requires User Approval |
|---|---|---|
| MS-xx.xx | 다음 작업 | YES |

---

## 9. 사용자 대기 문구

현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
