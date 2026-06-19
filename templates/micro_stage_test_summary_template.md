# Micro Stage Test Summary

- Micro Stage ID: MS-xx.xx
- Test Date: YYYY-MM-DD HH:mm:ss KST
- Environment: local / mock / live-read-only
- Status: PASS | FAIL | SKIPPED

## Commands

```bash
pytest tests/... -q
ruff check .
```

## Results

| Command | Result | Output File |
|---|---|---|
| pytest | PASS/FAIL/SKIPPED | reports/test-results/MS-xx.xx-pytest-output.txt |
| ruff | PASS/FAIL/SKIPPED | reports/test-results/MS-xx.xx-ruff-output.txt |

## Notes

- Mock test와 Live API test를 반드시 구분한다.
- Secret 원문을 저장하지 않는다.
- 실패 시 다음 Micro Stage로 넘어가지 않는다.
