# 15. 관측성 및 리포트

## 1. 로그 파일

| 파일 | 내용 |
|---|---|
| `logs/app.log` | 앱 일반 로그 |
| `logs/toss_api.log` | API 호출/응답 요약 |
| `logs/ai.log` | AI prompt/response 요약. 민감정보 제외 |
| `logs/error.log` | 에러/스택트레이스 |

## 2. API 로그 필드

```json
{
  "ts": "2026-06-19T15:00:00+09:00",
  "method": "GET",
  "path": "/api/v1/prices",
  "status_code": 200,
  "rate_group": "MARKET_DATA",
  "elapsed_ms": 153,
  "request_id": "01HXYZ...",
  "retry_count": 0
}
```

## 3. 추천 리포트

`reports/implementation/recommendation-run-{id}.md`

포함 항목:

- 실행 시각
- 입력 종목
- API 성공/실패 목록
- 점수 테이블
- BLOCKED 사유
- AI 설명 생성 여부
- fallback 여부

## 4. 모의투자 리포트

`reports/implementation/paper-portfolio-{date}.md`

포함 항목:

- 초기 자산
- 현재 평가금액
- 누적 수익률
- 실현/미실현 손익
- 종목별 비중
- 거래 내역
- 리스크 제한 위반 여부

## 5. 에러 요약 리포트

`reports/error-logs/latest-error-summary.md`

```markdown
# Error Summary

## Top Errors

| Count | Code | Message | Last Seen |
|---:|---|---|---|

## API Failures

| Endpoint | Status | Request ID | Action |
|---|---:|---|---|

## Recommended Fixes
```

## 6. 테스트 리포트 자동 생성

테스트 실행 후 다음 정보를 자동 기록한다.

- Python version
- OS
- package versions
- pytest 결과
- coverage
- 실패 테스트
- 다음 조치
