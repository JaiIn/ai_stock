# 06. Toss API Client 설계

## 1. Client 책임

- token 발급/캐싱
- HTTP request 전송
- 공통 헤더 구성
- 에러 매핑
- 재시도/backoff
- pydantic model 변환
- secret masking 로그

## 2. 클래스 구조

```text
TossAuthClient
 ├── issue_token()
 └── get_valid_token()

TossInvestClient
 ├── get_prices(symbols)
 ├── get_candles(symbol, interval, count, before, adjusted)
 ├── get_orderbook(symbol)
 ├── get_trades(symbol, count)
 ├── get_price_limits(symbol)
 ├── get_stocks(symbols)
 ├── get_stock_warnings(symbol)
 ├── get_exchange_rate(base, quote, date_time)
 ├── get_market_calendar(country, date)
 ├── get_accounts()
 ├── get_holdings(account_seq, symbol=None)
 ├── get_orders(account_seq, status, ...)
 ├── get_order(account_seq, order_id)
 ├── get_buying_power(account_seq, currency)
 ├── get_sellable_quantity(account_seq, symbol)
 └── get_commissions(account_seq)
```

## 3. Token cache 정책

- `expires_in` 기준으로 만료 5분 전 refresh
- token 발급 실패 시 사용자에게 client id/secret 확인 안내
- 401 발생 시 1회 강제 refresh
- refresh storm 방지를 위해 lock 사용 가능

## 4. HTTP 공통 헤더

```python
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json',
}

if account_seq is not None:
    headers['X-Tossinvest-Account'] = str(account_seq)
```

## 5. 에러 클래스

```text
TossApiError
 ├── TossAuthError
 ├── TossRateLimitError
 ├── TossValidationError
 ├── TossNotFoundError
 ├── TossPermissionError
 ├── TossBusinessRuleError
 └── TossServerError
```

## 6. 응답 파싱 원칙

- 성공 응답은 `result` field를 꺼내 domain model로 변환
- 실패 응답은 `error.code`, `error.message`, `error.data`, `requestId`를 보존
- decimal string은 `Decimal`로 변환
- unknown enum은 문자열 그대로 보존

## 7. Contract test fixture

`tests/fixtures/toss/` 아래에 다음 fixture를 둔다.

```text
issue_token_success.json
prices_success.json
candles_success.json
stocks_success.json
stock_warnings_empty.json
exchange_rate_success.json
accounts_success.json
holdings_success.json
buying_power_success.json
sellable_quantity_success.json
commissions_success.json
rate_limit_error.json
expired_token_error.json
```

## 8. v0.1 mutation guard

주문 생성/정정/취소 메서드를 만들 경우 다음처럼 작성한다.

```python
def create_order(...):
    raise LiveTradingDisabledError('v0.1 does not allow live order creation')
```

테스트에서는 실제 HTTP POST가 호출되지 않는지 반드시 검증한다.
