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

## 1.2 OAuth token endpoint 제한 예외

MS-05.04의 `POST /oauth2/token`은 주문·업무 API가 아닌 인증 endpoint이며,
사용자가 명시적으로 승인한 smoke test에서만 단일 호출할 수 있습니다.

- OAuth endpoint 외 Toss endpoint 호출 금지
- `ALLOW_LIVE_API=true` 필수
- `ALLOW_REAL_ORDER=false` 필수
- `DRY_RUN_ONLY=true` 필수
- accountSeq 사용 금지
- token 원문 출력·파일 저장 금지
- 주문, 계좌, 자산, 잔고, 체결, 시세 endpoint 호출 금지

이 제한 예외는 MS-05.03의 업무 API allowlist를 확장하지 않습니다.

## 1.3 최초 read-only live smoke 제한

MS-05.05에서는 사용자 승인에 따라 아래 두 호출만 허용합니다.

1. `POST /oauth2/token`
2. `GET /api/v1/exchange-rate`

환율 호출 전에 `LiveApiSafetyGate`가 아래 고정 metadata를 평가해야 합니다.

- method: `GET`
- path: `/api/v1/exchange-rate`
- category: `market_info`
- requires auth: true
- requires accountSeq: false

`DRY_RUN_ONLY=true`는 유지하며 전용 smoke client의 명시적 승인 flag가 있을 때만
이 단일 GET을 허용합니다. 다른 업무 endpoint, account-scoped endpoint와 주문
mutation은 계속 차단합니다.

실패 진단에는 phase, 성공 여부, HTTP status, 고정된 safe error type/message,
endpoint와 method만 포함할 수 있습니다. Token, credential, Authorization header,
request body와 raw response는 진단 객체·출력·보고서에 포함하지 않습니다. 진단
경로 보강 자체는 live 재시도를 허용하지 않으며 재시도에는 별도 사용자 승인이
필요합니다.

MS-05.07 공식 schema 재확인 이후 환율 read-only request에는 아래 query가
필수입니다.

- `baseCurrency`: `KRW` 또는 `USD`
- `quoteCurrency`: `KRW` 또는 `USD`
- 두 통화는 서로 달라야 함
- `dateTime`: optional

전용 smoke client는 다음 승인된 retry를 위해 `USD` → `KRW`를 기본 통화쌍으로
준비합니다. 이 기본값은 allowlist를 확장하지 않으며 실제 호출에는 매번 별도
사용자 승인이 필요합니다.

## 1.5 Stock Info read-only preflight

MS-05.09에서 공식 schema를 다시 확인한 Stock Info endpoint는 다음과 같습니다.

- `GET /api/v1/stocks`
- `GET /api/v1/stocks/{symbol}/warnings`
- OAuth2 인증 필요
- accountSeq 불필요
- read-only이며 order/write/mutation 범주가 아님

Safety Gate는 위 path를 metadata-only dry-run allowlist로 유지합니다.
`requires_account_seq=true` metadata가 전달되면 같은 path라도 차단합니다.
다음 live smoke 후보는 단일 `GET /api/v1/stocks?symbols=005930`이지만, 이번
단계에서는 실행하지 않으며 실제 호출에는 별도 사용자 승인이 필요합니다.

## 1.6 Prices read-only preflight

MS-05.12에서 `GET /api/v1/prices`는 공식 OpenAPI 기준 read-only endpoint로
재확인했습니다.

- OAuth2 인증 필요
- `accountSeq` 불필요
- `GET` 및 `market-data` category
- 주문, write, trading, mutation endpoint가 아님
- Live API Safety Gate의 기존 read-only allowlist 유지
- `requires_account_seq=true` metadata가 전달되면 동일 endpoint도 차단
- 다음 live 후보는 단일 query `symbols=005930`

이 preflight는 metadata와 fake response만 검증합니다. 실제 OAuth token 발급,
Prices 호출, 다른 업무 API 호출은 수행하지 않으며 다음 live smoke는 별도 사용자
승인이 필요합니다.

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
