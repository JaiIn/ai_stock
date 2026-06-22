# 10. 테스트 실행과 로그 생성

## 1. 필수 테스트 파일

| 파일 | 목적 |
|---|---|
| `tests/test_config.py` | 환경변수/기본값 검증 |
| `tests/test_secret_masking.py` | Secret 마스킹 검증 |
| `tests/test_toss_client_auth.py` | OAuth token 발급/refresh 검증 |
| `tests/test_toss_client_contract.py` | endpoint 응답 parsing 검증 |
| `tests/test_rate_limit_retry.py` | 429 Retry-After/backoff 검증 |
| `tests/test_recommendation_engine.py` | score/rating 계산 검증 |
| `tests/test_ai_prompt_guardrails.py` | 금지 표현 필터 검증 |
| `tests/test_paper_portfolio.py` | paper order/position/PnL 검증 |
| `tests/test_no_real_order_policy.py` | 실주문 차단 검증 |
| `tests/test_reports_generation.py` | 리포트 생성 검증 |

## 2. 테스트 명령

```bash
ruff check .
pytest -q
coverage run -m pytest
coverage report
```

### 로컬 표준 검증 명령

Windows PowerShell에서 프로젝트 로컬 가상환경을 사용한다.

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/dev_check.py
```

`scripts/dev_check.py`는 저장소 루트에서 아래 명령을 순서대로 실행한다.

```text
python -m compileall -q src tests
python -m unittest discover -s tests
python -m pytest
git diff --check
```

각 단계는 콘솔에 `PASS` 또는 `FAIL`을 출력한다. 하나라도 실패하면 전체 명령은 non-zero exit code로 종료한다. pytest 캐시는 통합 검증 중 생성하지 않으며 실제 API는 호출하지 않는다.

## 3. 테스트 결과 파일

Codex는 구현 완료 후 반드시 아래 파일을 생성한다.

```text
reports/test-results/latest-test-summary.md
reports/test-results/latest-pytest-output.txt
reports/test-results/latest-coverage.txt
```

## 4. 에러 로그 파일

```text
logs/app.log
logs/toss_api.log
logs/ai.log
logs/error.log
reports/error-logs/latest-error-summary.md
```

## 5. latest-test-summary.md 형식

```markdown
# Test Summary

- Date:
- Commit/Run ID:
- Python Version:
- Total Tests:
- Passed:
- Failed:
- Skipped:
- Coverage:

## Failed Tests

| Test | Reason | Fix |
|---|---|---|

## Notes
```

## 6. 실주문 차단 테스트 예시

```python
def test_create_order_is_blocked_even_if_env_enabled(monkeypatch):
    monkeypatch.setenv('ENABLE_LIVE_TRADING', 'true')
    client = TossInvestClient(...)
    with pytest.raises(LiveTradingDisabledError):
        client.create_order(...)
```

## 7. Secret masking 테스트 예시

```python
def test_secret_is_masked_in_logs(caplog):
    secret = 's_abcdefghijklmnopqrstuvwxyz'
    logger.info('secret=%s', mask_secret(secret))
    assert secret not in caplog.text
```

## 8. Mock API 원칙

- 실제 토스증권 API를 CI 테스트에서 호출하지 않는다.
- `respx` 또는 `pytest-httpx`로 응답을 mock한다.
- 실제 API 통합 테스트는 `RUN_TOSS_INTEGRATION_TESTS=true`일 때만 수동 실행한다.


## 단계 완료 체크리스트 로그

각 개발 단계 종료 시 테스트 결과와 별도로 `reports/stage-gates/`에 단계 완료 체크리스트를 생성한다.

필수 파일 예시:

```text
reports/stage-gates/M2-toss-api-client-completion-checklist.md
```

체크리스트에는 다음 항목을 포함한다.

- 완료 단계 ID/이름
- 구현 완료 항목
- 실행한 테스트 명령과 결과
- 생성/수정 파일
- 안전 조건 검증 결과
- 사용자 입력 필요 여부
- 다음 단계 후보
- 사용자 명령 대기 메시지

사용자 입력이 필요한 경우 `BLOCKED_USER_INPUT_REQUIRED` 상태로 기록하고, 실제 토큰/API Key/계좌정보를 임의값으로 대체하지 않는다.


---

## Micro Stage별 테스트 결과 저장 규칙

각 Micro Stage는 테스트 결과를 독립적으로 저장한다.

파일명 규칙:

```text
reports/test-results/MS-xx.xx-pytest-output.txt
reports/test-results/MS-xx.xx-ruff-output.txt
reports/test-results/MS-xx.xx-test-summary.md
reports/implementation/MS-xx.xx-implementation-report.md
reports/micro-stages/MS-xx.xx-<slug>.md
```

`latest-*` 파일은 가장 최근 실행 결과를 복사한 편의 파일로만 사용한다. 근거 자료는 반드시 Micro Stage ID가 포함된 파일로 남긴다.

테스트 실패 시:

1. 실패 output 저장
2. `reports/errors/MS-xx.xx-error-log.md` 생성
3. 다음 Micro Stage 진행 금지
4. 사용자에게 실패 원인과 수정 후보 보고
5. 사용자 명령 대기

Live API 테스트 결과는 별도 표시한다.

```text
Environment: mock
Environment: live-read-only
Environment: live-mutation-forbidden
```

v0.1에서 `live-mutation` 테스트는 금지한다. 주문 API는 차단 테스트만 수행한다.
