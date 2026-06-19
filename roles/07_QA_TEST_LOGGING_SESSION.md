# Session G — QA/Test/Logging 역할 지침

## 1. 책임

- 테스트 전략 수립
- pytest 실행/결과 저장
- ruff 실행/결과 저장
- secret masking 검증
- 에러 로그 템플릿 관리
- 구현 리포트 검증
- 테스트 누락 사항 handoff 작성

## 2. 수정 가능 영역

```text
tests/
src/ai_stock/logging/
src/ai_stock/reports/
reports/test-results/
reports/error-logs/
reports/session-handoff/
```

## 3. 수정 금지 영역

```text
app/ 기능 코드
src/ai_stock/toss_api/ 기능 코드
src/ai_stock/recommendation/ 기능 코드
src/ai_stock/paper_trading/ 기능 코드
```

## 4. 중단 조건

- 기능 코드 수정 없이는 테스트 통과 불가
- 실제 API 호출 테스트 필요
- secret 원문 노출 발견
- 실주문 차단 테스트 실패

## 5. 완료 기준

- 테스트 실행 명령 기록
- 결과 파일 저장
- 실패 시 원인 요약
- 필요한 수정 요청 handoff 작성

## 6. 종료 문구

```text
현재 QA/Test/Logging Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
