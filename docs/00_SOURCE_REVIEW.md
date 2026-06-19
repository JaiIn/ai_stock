# 00. 소스 확인 요약

작성일: 2026-06-19

## 확인한 사용자 제공 링크

- `https://developers.tossinvest.com/docs`
- `https://developers.tossinvest.com/docs/auth#tag/auth/issueoauth2token`
- `https://developers.tossinvest.com/docs/market-data#tag/market-data`
- `https://developers.tossinvest.com/docs/stock-info#tag/stock-info/getstocks`
- `https://developers.tossinvest.com/docs/stock-info#tag/stock-info/getstockwarnings`
- `https://developers.tossinvest.com/docs/market-info#tag/market-info/getexchangerate`
- `https://developers.tossinvest.com/docs/account#tag/account/getaccounts`
- `https://developers.tossinvest.com/docs/asset#tag/asset/getholdings`
- `https://developers.tossinvest.com/docs/order#tag/order/createorder`
- `https://developers.tossinvest.com/docs/order#tag/order/modifyorder`
- `https://developers.tossinvest.com/docs/order#tag/order/cancelorder`
- `https://developers.tossinvest.com/docs/order-history#tag/order-history/getorders`
- `https://developers.tossinvest.com/docs/order-info#tag/order-info/getbuyingpower`

## 문서 렌더링 방식

토스증권 개발자 문서의 브라우저 페이지는 JavaScript로 API reference를 렌더링한다. 비브라우저/AI agent는 다음 LLM용 문서를 사용하도록 안내된다.

- `https://developers.tossinvest.com/llms.txt`
- `https://openapi.tossinvest.com/openapi-docs/overview.md`
- `https://openapi.tossinvest.com/openapi-docs/latest/api-reference/README.md`
- `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`

## Source of Truth 원칙

Codex는 개발 직전에 반드시 `latest/openapi.json`을 다시 받아서 endpoint path, schema, enum, rate limit group을 검증해야 한다.
이 문서 세트는 2026-06-19 기준 확인 내용을 바탕으로 한 개발 설계 문서이며, API는 변경될 수 있다.

## 핵심 확인 사항

- Base API server: `https://openapi.tossinvest.com`
- 인증 방식: OAuth 2.0 Client Credentials Grant
- 토큰 발급: `POST /oauth2/token`
- 모든 API 요청에는 `Authorization: Bearer {access_token}` 필요
- 계좌/자산/주문/주문정보 API에는 `X-Tossinvest-Account` 헤더 필요
- 공식 API는 REST API 중심이다. WebSocket은 문서상 아직 공개/사용 전제로 잡지 않는다.
- 응답은 성공 시 `{ "result": ... }` envelope을 사용한다. OAuth token 발급은 OAuth2 표준 응답이며 공통 envelope이 아니다.
- 실패 응답은 `{ "error": { requestId, code, message, data? } }` 형태다.
- 429 응답에는 `Retry-After`, `X-RateLimit-*` 계열 헤더가 내려올 수 있으므로 재시도 로직을 구현한다.

## 개발 시 주의

- 공식 문서와 OpenAPI JSON의 내용이 다르면 OpenAPI JSON을 우선한다.
- 블로그/비공식 라이브러리 정보는 참고만 한다.
- 실주문 기능은 문서화하되, v0.1 구현은 모의투자 중심으로 제한한다.
