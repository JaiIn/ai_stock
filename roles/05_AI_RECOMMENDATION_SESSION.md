# Session D — AI Recommendation 역할 지침

## 1. 책임

- rule-based 추천 점수 계산
- 경고 종목 필터링
- 추천 사유 생성
- LLM Provider interface 구현
- Mock LLM provider 구현
- LLM 실패 시 fallback 문구 생성

## 2. 수정 가능 영역

```text
src/ai_stock/recommendation/
src/ai_stock/services/recommendation_service.py
tests/unit/test_recommendation*.py
tests/unit/test_llm_provider*.py
```

## 3. 수정 금지 영역

```text
app/
src/ai_stock/toss_api/
src/ai_stock/repositories/
src/ai_stock/paper_trading/
src/ai_stock/risk/ 실주문 정책
```

## 4. 중단 조건

- 실제 LLM API Key 필요
- 추천 기준 변경 필요
- 사용자 투자 성향/리스크 정책 결정 필요
- 실주문 판단과 연결될 위험 있음

## 5. 완료 기준

- mock LLM test 통과
- rule score test 통과
- 추천 결과에 투자 조언 아님 문구 포함
- 위험 요인 설명 포함

## 6. 종료 문구

```text
현재 AI Recommendation Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
