# Session B — Backend/API Client 역할 지침

## 1. 책임

- Toss Invest API client 구현
- OAuth2 token 발급/캐시/만료 처리
- HTTP timeout/retry/rate limit 처리
- API request/response DTO 구현
- secret masking 연동
- mock 기반 contract test 작성

## 2. 수정 가능 영역

```text
src/ai_stock/toss_api/
src/ai_stock/config/
src/ai_stock/logging/
src/ai_stock/domain/api_models.py
tests/contract/
tests/unit/test_config*.py
tests/unit/test_secret*.py
```

## 3. 수정 금지 영역

```text
app/
src/ai_stock/recommendation/
src/ai_stock/paper_trading/
src/ai_stock/repositories/
src/ai_stock/risk/ 실주문 정책
```

## 4. 중단 조건

- 실제 TOSS_CLIENT_ID 필요
- 실제 TOSS_CLIENT_SECRET 필요
- Access Token live 발급 필요
- 계좌 정보/accountSeq 필요
- Toss live API 호출 필요
- 응답 스펙이 문서와 다름

## 5. 완료 기준

- mock contract test 통과
- secret masking test 통과
- live API는 사용자 승인 전까지 미수행
- 테스트 결과를 `reports/test-results/`에 저장

## 6. 종료 문구

```text
현재 Backend/API Client Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
