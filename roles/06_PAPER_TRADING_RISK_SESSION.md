# Session E — Paper Trading/Risk 역할 지침

## 1. 책임

- 모의 포트폴리오
- 모의 주문 생성/체결
- 모의 포지션/손익 계산
- 수수료/세금 추정
- 실주문 차단 safety gate
- 리스크 정책 구현

## 2. 수정 가능 영역

```text
src/ai_stock/paper_trading/
src/ai_stock/risk/
src/ai_stock/services/paper_trading_service.py
tests/unit/test_paper_trading*.py
tests/unit/test_risk*.py
```

## 3. 수정 금지 영역

```text
app/
src/ai_stock/toss_api/
src/ai_stock/recommendation/
src/ai_stock/repositories/ schema 직접 변경
```

## 4. 절대 규칙

- `ALLOW_REAL_ORDER=false` 기본값 유지
- 실주문 API 실제 호출 금지
- 실주문 버튼/경로 생성 금지
- safety gate 우회 금지
- 실주문 관련 변경은 사용자 승인 없이는 진행 금지

## 5. 중단 조건

- 수수료/세금 정책 확정 필요
- 초기 모의투자 자본금 결정 필요
- 주문 체결 방식 정책 결정 필요
- 실주문 관련 요청 발생

## 6. 완료 기준

- paper buy/sell test 통과
- position PnL test 통과
- real order blocked test 통과
- Decimal 기반 계산 확인

## 7. 종료 문구

```text
현재 Paper Trading/Risk Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
