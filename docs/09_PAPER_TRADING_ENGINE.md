# 09. 모의투자 엔진 설계

## 1. 목표

실제 주문 없이 추천 전략을 검증한다.

## 2. 핵심 기능

- paper portfolio 생성
- cash balance 관리
- paper buy/sell order 생성
- 현재가 기반 체결 시뮬레이션
- 수수료/세금 추정
- position 평균단가 계산
- realized/unrealized PnL 계산
- 거래 내역 리포트

## 3. 체결 정책 v0.1

| 주문 유형 | 체결 방식 |
|---|---|
| MARKET BUY | 최신 현재가로 즉시 체결 |
| MARKET SELL | 최신 현재가로 즉시 체결 |
| LIMIT BUY | 현재가 <= 지정가면 체결 |
| LIMIT SELL | 현재가 >= 지정가면 체결 |

## 4. 수수료/세금

- 실제 수수료 API `/api/v1/commissions`가 있으면 시장별 수수료율 사용
- 없으면 설정값 사용
- 국내 매도세/거래세는 보수적으로 추정하거나 v0.1에서는 별도 필드로 분리
- 세금 계산은 정확한 신고용이 아님을 명시

## 5. 평균단가 계산

```text
new_avg_price = (old_qty * old_avg_price + buy_qty * fill_price) / (old_qty + buy_qty)
```

반드시 Decimal 사용.

## 6. 매도 처리

- 보유 수량보다 많이 팔 수 없음
- realized PnL 기록
- position quantity 감소
- quantity가 0이면 position closed 처리

## 7. 리스크 제한

- 종목당 최대 비중: 기본 20%
- 1회 모의 주문 최대 금액: 기본 총자산의 10%
- 일일 손실 제한: 기본 -3%
- 경고 종목 paper order도 기본 차단. 실험 모드에서만 허용

## 8. 결과 지표

- 총 평가금액
- 누적 수익률
- 실현 손익
- 미실현 손익
- 승률
- 평균 손익비
- 최대 낙폭 MDD
- 종목별 비중

## 9. 이벤트 로그

모든 paper order에는 audit log를 남긴다.

```json
{
  "event_type": "PAPER_ORDER_FILLED",
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": "1",
  "filled_price": "185.70",
  "reason": "recommendation_run_id=123"
}
```
