# Stage Completion Checklist

## Stage

- Stage ID:
- Stage Name:
- Completed At:
- Status: COMPLETED | COMPLETED_WITH_WARNINGS | BLOCKED_USER_INPUT_REQUIRED | BLOCKED_EXTERNAL_API_REQUIRED | FAILED | SKIPPED_BY_POLICY

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
| Lint | `ruff check .` |  |  |
| Unit Test | `pytest -q` |  |  |
| Contract Test |  |  |  |
| Manual Run |  |  |  |

## 3. 생성/수정 파일

| Path | Action | Description |
|---|---|---|
|  |  |  |

## 4. 검증한 안전 조건

- [ ] Secret masking 동작 확인
- [ ] 실제 주문 API 비활성 상태 확인
- [ ] 민감 정보 로그 미출력 확인
- [ ] Decimal 기반 금액 계산 확인
- [ ] mock 테스트와 live 테스트 구분 확인

## 5. 사용자 입력 필요 여부

- Required: YES/NO
- Needed Item:
- Why Needed:
- Safe Input Method:
- Do Not Print:

## 6. 남은 이슈

- [ ]

## 7. 다음 단계 제안

- 

## 8. 사용자 명령 대기

현재 단계가 종료되었습니다. 다음 명령을 입력해 주세요.

- `다음 단계 진행`
- `실제 API 연동 테스트 진행`
- `현재 단계 보완`
- `중단`
