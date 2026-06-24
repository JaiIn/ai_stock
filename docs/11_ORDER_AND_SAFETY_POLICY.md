# 11. 주문과 안전 정책

## 1. v0.1 원칙

v0.1은 실주문 금지다. 주문 API는 학습/문서화/미래 확장을 위해 정리하지만, 실제 호출은 코드와 테스트로 차단한다.

## 1.1 Live API Safety Gate

`LiveApiSafetyGate`는 미래의 실제 전송 경로 앞에서 endpoint metadata만 검사하는
fail-closed 정책입니다. 현재 단계에서는 network client, token, authenticated
request context 또는 send 기능과 연결하지 않습니다.

허용 조건:

- 공식 확인된 read-only allowlist의 `GET` endpoint
- accountSeq 불필요
- `ALLOW_LIVE_API=true`
- `ALLOW_REAL_ORDER=false`
- `DRY_RUN_ONLY=true`에서는 send 요청이 아닌 metadata 평가만 허용

항상 차단:

- `POST /api/v1/orders`
- `POST /api/v1/orders/{orderId}/modify`
- `POST /api/v1/orders/{orderId}/cancel`
- `order`, `write`, `trading`, `mutation` category
- 주문 또는 계좌 변경 성격의 `POST`, `PUT`, `PATCH`, `DELETE`
- accountSeq 필요 endpoint
- unknown 또는 pending endpoint
- `ALLOW_REAL_ORDER=true`

주문 API는 설정값이나 dry-run 여부와 무관하게 차단합니다.

## 2. 미래 v0.2+ 실주문을 고려할 때 필요한 조건

실주문 기능은 다음 조건이 모두 충족될 때만 고려한다.

- 사용자가 명시적으로 실주문 모드 활성화
- API 이용약관 검토 완료
- 소액 테스트 완료
- 주문 전 `buying-power`, `sellable-quantity`, `commissions`, `market-calendar`, `stock-warnings` 확인
- 주문 프리뷰 화면에서 사용자가 수동 확인
- 2단계 확인 문구 입력
- kill switch 제공
- 일일 손실 제한
- 종목당/일별 주문 횟수 제한
- 모든 주문에 `clientOrderId` 사용
- 주문 후 `getOrder`로 상태 확인

## 3. 주문 생성 API 문서상 고려사항

`POST /api/v1/orders`

주요 필드:

- `clientOrderId`: 멱등성 키. 최대 36자, 영숫자/하이픈/언더스코어.
- `symbol`: KRX 6자리 또는 US ticker.
- `side`: BUY/SELL.
- `orderType`: LIMIT/MARKET.
- `timeInForce`: DAY/CLS.
- `quantity`: 수량 기반 주문.
- `orderAmount`: 금액 기반 주문. 미국 주식 시장가 조건 등 제한 가능.
- `price`: 지정가 주문 가격.
- `confirmHighValueOrder`: 고액 주문 확인 플래그.

## 4. 주문 전 필수 체크

```text
check_account_selected
check_market_open
check_stock_exists
check_stock_warnings
check_price_limit
check_buying_power_or_sellable_quantity
check_commission
check_position_limit
check_daily_loss_limit
check_duplicate_client_order_id
manual_confirm
```

## 5. 금지 주문 패턴

- 경고/정리매매 종목 자동 주문
- 짧은 시간 내 반복 주문
- 가격을 왜곡할 수 있는 허수성 주문
- 반대 방향 미체결 주문이 있는데 신규 반대 주문
- 고액 주문 확인 없이 주문
- 장 운영 시간 외 무조건 주문
- AI 문장 하나만 근거로 주문

## 6. Kill Switch

다음 파일이 존재하면 모든 주문성 동작을 중단한다.

```text
./KILL_SWITCH
```

v0.1에서는 paper order도 경고 후 차단할 수 있도록 옵션화한다.

## 7. 감사 로그

실주문 기능이 들어가는 버전에서는 다음을 반드시 기록한다.

- 주문 요청 전 검증 결과
- 주문 요청 payload 마스킹본
- response requestId
- orderId 마스킹본
- 사용자 확인 시각
- 주문 상태 조회 결과
