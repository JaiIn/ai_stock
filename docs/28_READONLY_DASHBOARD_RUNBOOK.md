# 28. Read-Only Dashboard Local Runbook

## 1. 목적

이 문서는 local-only read-only Streamlit snapshot dashboard를 사용자가 안전하게
실행하고 확인하기 위한 runbook이다.

- dashboard는 실제 Toss API를 호출하지 않고 local SQLite snapshot DB만 조회한다.
- dashboard에는 AI 추천, 실제 주문, 계좌, 자산, 잔고, 체결 기능이 없다.
- dashboard 실행에 `.env.local`, API KEY, SECRET KEY, Client ID, Client Secret,
  Access Token, accountSeq가 필요하지 않다.
- DB row 전문, raw response body 전문, credential 또는 Authorization Bearer 원문을
  화면이나 로그에 출력하지 않는다.

## 2. 현재 지원 범위

| 항목 | 현재 계약 |
| --- | --- |
| Data source | `local_snapshot_latest_read_model` |
| Default DB path | `data/local/ai_stock.sqlite3` |
| Default symbol | `005930` |
| Default exchange pair | `USD/KRW` |
| Selector | symbol, base currency, quote currency |
| DB open mode | SQLite URI `mode=ro` |
| SQLite guard | `PRAGMA query_only=ON` |
| Missing DB | 파일을 생성하지 않고 safe warning 표시 |
| Partial data | 사용 가능한 summary와 completeness warning 표시 |

dashboard는 StockInfo, PriceSnapshot, Candle, ExchangeRate의 latest safe summary와
completeness, source counts, read-only diagnostics만 표시한다.

## 3. 실행 전 체크리스트

프로젝트 루트에서 다음 항목을 확인한다.

### 3.1 Git 기준 상태

```powershell
git branch --show-current
git log -1 --oneline
git status --short
```

- 승인된 최신 `main`에서 실행한다.
- `git status --short` 결과가 없어야 한다.
- 로컬 변경이 있으면 원인을 확인하기 전에는 실행하지 않는다.

### 3.2 Python 환경

Windows PowerShell에서는 프로젝트의 가상 환경을 활성화한다.

```powershell
.\.venv\Scripts\Activate.ps1
python --version
```

필요한 패키지가 이미 설치된 프로젝트 가상 환경을 사용한다. dashboard 실행을
위해 `.env.local`을 생성하거나 읽을 필요가 없다.

### 3.3 DB 존재 여부와 safe metadata

DB 내용을 열거나 row를 출력하지 않고 파일 존재 여부와 safe metadata만 확인한다.

```powershell
Test-Path -LiteralPath 'data/local/ai_stock.sqlite3'
Get-Item -LiteralPath 'data/local/ai_stock.sqlite3' |
    Select-Object Length, LastWriteTimeUtc
```

- 파일이 없더라도 schema initialize, migration 또는 빈 DB 생성을 수행하지 않는다.
- dashboard는 `database_not_found` 계열 safe warning을 표시한다.
- 파일이 존재하면 실행 전 size와 modified time을 기록해 종료 후 비교할 수 있다.

### 3.4 Git 추적 방지

```powershell
git ls-files -- data/local/ai_stock.sqlite3
git ls-files -- data
git check-ignore -v data/local/ai_stock.sqlite3
```

- 첫 두 명령의 결과는 없어야 한다.
- `git check-ignore`는 `data/` 또는 SQLite ignore 규칙 적용을 보여야 한다.
- `data/`, `*.sqlite`, `*.sqlite3`, `*.db` 파일을 Git에 추가하지 않는다.

### 3.5 불필요한 입력

- `.env.local`: 불필요
- API KEY / SECRET KEY / Client ID / Client Secret: 불필요
- Access Token: 불필요
- accountSeq: 불필요
- credential 입력 요청이 나타나면 dashboard 실행을 중단하고 범위를 확인한다.

## 4. 실행 명령

프로젝트 루트에서 다음 명령을 실행한다.

```powershell
python -m streamlit run app/streamlit_app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
```

이 명령은 localhost Streamlit UI만 기동한다. 외부 URL, Toss API 또는 OAuth token
endpoint를 호출하는 명령이 아니다.

## 5. 종료 방법

1. Streamlit을 실행한 터미널에서 `Ctrl+C`를 입력한다.
2. 종료 후 포트 `8501` listener가 남지 않았는지 확인한다.

```powershell
Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue
```

결과가 없어야 한다. listener가 남아 있다면 소유 프로세스를 먼저 확인하고,
실행한 Streamlit 프로세스가 맞을 때만 해당 PID를 종료한다. 다른 애플리케이션의
프로세스를 임의로 종료하지 않는다.

## 6. 화면 확인 체크리스트

- [ ] dashboard title이 표시된다.
- [ ] Symbol input이 표시된다.
- [ ] Base currency input이 표시된다.
- [ ] Quote currency input이 표시된다.
- [ ] default symbol이 `005930`이다.
- [ ] default base currency가 `USD`이다.
- [ ] default quote currency가 `KRW`이다.
- [ ] default pair가 `USD/KRW`이다.
- [ ] data source가 `local_snapshot_latest_read_model`이다.
- [ ] StockInfo summary가 표시된다.
- [ ] PriceSnapshot summary가 표시된다.
- [ ] Candle summary가 표시된다.
- [ ] ExchangeRate summary가 표시된다.
- [ ] completeness flags가 표시된다.
- [ ] source counts가 표시된다.
- [ ] read-only diagnostics가 표시된다.

데이터가 없는 section은 raw row 대신 safe warning 또는 completeness warning으로
표시될 수 있다.

## 7. Selector 사용법

### 7.1 Symbol

- 입력값 앞뒤 공백은 trim된다.
- 빈 symbol은 기본값 `005930`으로 처리된다.
- symbol은 화면 표시와 parameterized local query에만 사용된다.
- 허용되지 않은 문자가 있거나 길이 규칙을 벗어나면 safe validation warning을
  표시하고 DB query를 시작하지 않는다.

### 7.2 Base/quote currency

- base와 quote는 각각 ASCII 영문 3자리만 허용한다.
- 소문자 입력은 대문자로 정규화한다.
- 예: `usd`와 `krw`는 `USD/KRW`로 처리한다.
- 잘못된 길이 또는 문자는 safe validation warning으로 처리한다.

### 7.3 Selector 안전 경계

- 유효한 selector만 `local_snapshot_latest_read_model`의 local read-only query
  parameter로 전달한다.
- selector는 API refresh, OAuth, credential, accountSeq, AI 추천 또는 주문 기능과
  연결되지 않는다.
- 선택한 symbol/pair 데이터가 부족하면 partial completeness warning을 표시한다.

## 8. 금지 UI 및 기능

현재 dashboard에는 다음 control이 없어야 한다.

- API refresh 또는 live data refresh 버튼
- OAuth token 발급 버튼
- credential, API KEY, SECRET KEY, token 입력란
- accountSeq 입력란
- AI 추천 또는 매수/매도/보유 추천 버튼
- 주문 제출·정정·취소 버튼
- 계좌·자산·잔고·체결 조회 버튼
- 실주문 버튼
- DB write, schema initialize 또는 migration 버튼

위 control이 보이면 현재 승인된 read-only dashboard 범위를 벗어난 상태이므로
실행을 중단한다.

## 9. 민감정보 정책

- `.env.local`을 사용하거나 화면에 출력하지 않는다.
- API KEY / SECRET KEY / Client ID / Client Secret은 필요하지 않다.
- Access Token은 필요하지 않다.
- Authorization Bearer 원문을 출력하거나 저장하지 않는다.
- accountSeq를 요청·사용·저장하지 않는다.
- request body 또는 raw response body 전문을 저장하지 않는다.
- DB row 전문과 실제 계좌·자산·잔고·체결 정보를 출력하지 않는다.

## 10. DB 안전 정책

- DB는 read-only로만 연다.
- SQLite URI `mode=ro`를 사용한다.
- connection에 `PRAGMA query_only=ON`을 적용한다.
- schema initialize를 수행하지 않는다.
- migration을 수행하지 않는다.
- INSERT, UPDATE, DELETE 또는 DDL을 수행하지 않는다.
- 실행 전후 DB size와 modified time이 동일해야 한다.
- `data/local/ai_stock.sqlite3`와 `data/`는 Git 미추적 상태여야 한다.

종료 후 다음 safe metadata를 다시 확인하고 실행 전 값과 비교한다.

```powershell
Get-Item -LiteralPath 'data/local/ai_stock.sqlite3' |
    Select-Object Length, LastWriteTimeUtc
```

DB 내용이나 row를 검증 목적으로 출력하지 않는다.

## 11. Known non-blocking warnings

- pytest 임시 캐시 디렉터리 permission warning은 테스트 결과와 dashboard
  read-only 안전성에 영향을 주지 않는 비차단 경고다.
- LF/CRLF 안내는 Git/Windows 줄바꿈 변환 안내이며 기능, 테스트, read-only 정책,
  DB 안전성에 영향을 주지 않는다.
- workspace URI metadata 오류는 자동 브라우저 수동 확인만 제한할 수 있다.
  localhost HTTP와 별도 승인된 AppTest가 통과했다면 오류 사실과 대체 확인 결과를
  보고서에 기록할 수 있다.

## 12. Troubleshooting

### 12.1 DB 파일이 없을 때

- dashboard의 safe warning을 확인한다.
- DB 파일, schema 또는 디렉터리를 자동 생성하지 않는다.
- snapshot DB 생성은 별도 승인된 Micro Stage에서만 수행한다.

### 12.2 포트 8501이 이미 사용 중일 때

- Streamlit을 중복 실행하지 않는다.
- `Get-NetTCPConnection`으로 listener와 소유 PID를 확인한다.
- 자신이 실행한 이전 Streamlit 프로세스인지 확인한 뒤 종료한다.
- 소유자가 불명확하면 프로세스를 종료하지 말고 포트 충돌을 보고한다.

### 12.3 Selector invalid warning이 표시될 때

- symbol 앞뒤 공백과 허용 문자를 확인한다.
- base/quote가 각각 ASCII 영문 3자리인지 확인한다.
- credential이나 API 호출로 우회하지 않는다.

### 12.4 Partial data completeness warning이 표시될 때

- 선택한 symbol 또는 pair에 local snapshot 데이터가 부족할 수 있다.
- source counts와 component별 completeness flag를 확인한다.
- partial 상태는 DB write, live refresh 또는 schema initialize 사유가 아니다.

### 12.5 브라우저가 열리지 않을 때

- 터미널의 localhost URL을 직접 확인한다.
- 외부 URL이나 Toss API endpoint로 접속하지 않는다.
- 브라우저 자동 확인 도구의 workspace URI metadata 오류는 별도로 기록한다.
- 서버가 필요 없으면 `Ctrl+C`로 종료하고 listener가 정리됐는지 확인한다.

## 13. 다음 단계

- live API refresh 또는 AI 추천을 추가하려면 별도 Micro Stage, 명시적 사용자 승인,
  안전 정책과 테스트가 필요하다.
- 실제 API KEY / SECRET KEY가 필요한 작업은 live API/OAuth stage로 분리한다.
- 현재 read-only dashboard 실행에는 API KEY / SECRET KEY가 필요하지 않다.
- 계좌, 자산, 잔고, 체결 또는 주문 기능은 현재 dashboard 범위에 포함하지 않는다.
