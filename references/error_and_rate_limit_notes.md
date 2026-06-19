# Error and Rate Limit Notes

## 1. 공통 실패 응답

토스증권 API 실패 응답은 대체로 다음 envelope을 사용한다.

```json
{
  "error": {
    "requestId": "01HXYZABCDEFG123456789",
    "code": "invalid-request",
    "message": "요청이 올바르지 않습니다.",
    "data": {
      "field": "symbols"
    }
  }
}
```

## 2. 반드시 저장할 필드

- `error.requestId`
- `error.code`
- `error.message`
- `error.data`
- 응답 헤더 `X-Request-Id`
- 응답 헤더 `Retry-After`
- 응답 헤더 `X-RateLimit-Limit`
- 응답 헤더 `X-RateLimit-Remaining`
- 응답 헤더 `X-RateLimit-Reset`

## 3. 클라이언트 정책

| HTTP | 정책 |
|---:|---|
| 400 | 사용자 입력/파라미터 오류로 처리. 재시도하지 않음 |
| 401 | 토큰 만료 가능성. 1회 token refresh 후 재시도 |
| 403 | 권한 부족. 재시도하지 않음 |
| 404 | 종목/주문/계좌 없음. UI에 명확히 표시 |
| 409 | 중복/처리 중. 멱등성 키 확인 |
| 422 | 비즈니스 규칙 위반. 재시도하지 않음 |
| 429 | `Retry-After` 기반 backoff 후 재시도 |
| 500/503 | 지수 backoff. 최대 2~3회만 재시도 |

## 4. 주요 에러 코드 예시

- `invalid-request`
- `invalid-token`
- `expired-token`
- `account-header-required`
- `account-not-found`
- `stock-not-found`
- `order-not-found`
- `rate-limit-exceeded`
- `insufficient-buying-power`
- `order-hours-closed`
- `stock-restricted`
- `confirm-high-value-required`
- `max-order-amount-exceeded`
- `request-in-progress`
- `idempotency-key-conflict`

## 5. 재시도 의사코드

```python
async def request_with_retry(req):
    for attempt in range(max_attempts):
        res = await send(req)
        if res.status_code == 401 and attempt == 0:
            await token_cache.refresh(force=True)
            continue
        if res.status_code == 429:
            await sleep(parse_retry_after(res.headers) or backoff(attempt))
            continue
        if res.status_code in {500, 503}:
            await sleep(backoff(attempt))
            continue
        return res
```

## 6. 로그 마스킹

마스킹 대상:

- `TOSSINVEST_CLIENT_SECRET`
- `access_token`
- `Authorization` 헤더
- `X-Tossinvest-Account`
- 계좌번호
- 주문 ID 일부

예시:

```text
Authorization: Bearer eyJ...REDACTED
X-Tossinvest-Account: ***
accountNo: 1234******01
```
