# 05. 설정과 Secret 관리

## 1. 환경변수

| 변수명 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `TOSSINVEST_CLIENT_ID` | Y | 없음 | 토스증권 Open API Client ID |
| `TOSSINVEST_CLIENT_SECRET` | Y | 없음 | 토스증권 Open API Client Secret |
| `TOSSINVEST_ACCOUNT` | N | 없음 | 기본 accountSeq |
| `TOSSINVEST_API_BASE_URL` | N | `https://openapi.tossinvest.com` | API Base URL |
| `APP_ENV` | N | `local` | 실행 환경 |
| `DATABASE_URL` | N | `sqlite:///data/app.sqlite3` | DB URL |
| `ENABLE_LIVE_TRADING` | N | `false` | v0.1에서는 무조건 false 취급 |
| `DRY_RUN_ONLY` | N | `true` | paper trading only |
| `LLM_PROVIDER` | N | `none` | openai/compatible/none |
| `LLM_API_KEY` | N | 없음 | AI provider key |
| `LOG_LEVEL` | N | `INFO` | 로그 레벨 |

## 2. pydantic Settings 예시

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    tossinvest_client_id: str
    tossinvest_client_secret: str
    tossinvest_account: int | None = None
    tossinvest_api_base_url: str = 'https://openapi.tossinvest.com'

    enable_live_trading: bool = False
    dry_run_only: bool = True
    database_url: str = 'sqlite:///data/app.sqlite3'
    log_level: str = 'INFO'
```

## 3. Secret Masking

### 필수 마스킹 함수

```python
def mask_secret(value: str | None, keep: int = 4) -> str:
    if not value:
        return ''
    if len(value) <= keep * 2:
        return '*' * len(value)
    return f'{value[:keep]}...{value[-keep:]}'
```

### 헤더 마스킹

```python
SENSITIVE_HEADERS = {'authorization', 'x-tossinvest-account'}
```

### 로그 금지값

- client secret
- access token
- full account number
- full accountSeq
- raw Authorization header
- raw `.env` 내용

## 4. 운영 체크리스트

- `.env`는 Git에 올리지 않는다.
- Streamlit 화면에 secret 표시 금지.
- 에러 리포트에 request header 원문 저장 금지.
- `logs/`는 개인 PC 외부 공유 금지.
- Secret이 유출되면 즉시 토스증권 앱/콘솔에서 재발급.

## 5. MS-05.03 credential 비요구 원칙

MS-05.03 Live API Safety Gate는 request metadata와 아래 boolean 설정만 검사합니다.

- `ALLOW_LIVE_API`
- `ALLOW_REAL_ORDER`
- `DRY_RUN_ONLY`

이번 단계에서는 API KEY, SECRET KEY, Client ID, Client Secret, Access Token,
accountSeq가 필요하지 않습니다. `.env.local`도 생성하지 않습니다.

실제 credential은 MS-05.04 또는 사용자가 별도로 승인한 OAuth token 테스트
Micro Stage에서만 로컬 파일에 직접 입력하도록 안내합니다. 채팅, 로그, report에는
원문을 기록하지 않습니다.


## 사용자 입력이 필요한 Secret 처리

Codex는 실제 개발 중 다음 값이 필요한 경우 작업을 멈추고 사용자에게 `.env` 직접 입력을 요청한다.

- `TOSS_INVEST_CLIENT_ID`
- `TOSS_INVEST_CLIENT_SECRET`
- `TOSS_INVEST_ACCESS_TOKEN`
- `TOSS_INVEST_ACCOUNT_SEQ`
- 실 API 호출 승인 여부
- 실주문 기능 활성화 여부

원칙:

- 민감값을 채팅에 그대로 입력하라고 요구하지 않는다.
- 민감값을 로그/리포트/화면에 출력하지 않는다.
- mock 테스트는 진행할 수 있지만, live API 테스트는 사용자 입력 전까지 보류한다.
- 입력 완료 후 사용자의 명시적 명령이 있어야 다음 작업을 진행한다.

예시 안내 문구:

```text
실제 Toss API OAuth2 토큰 발급 테스트를 진행하려면 Client ID와 Client Secret이 필요합니다.
값은 채팅에 붙여넣지 말고 `.env` 파일에 직접 입력하세요.
입력 후 `설정 완료, 계속 진행`이라고 알려주세요.
사용자 명령을 기다립니다.
```


---

## Micro Stage 중 Secret 필요 시 중단 규칙

Codex는 개발 중 실제 Secret이 필요하면 임의값으로 계속 진행하지 않는다.

중단해야 하는 값:

- `TOSS_INVEST_CLIENT_ID`
- `TOSS_INVEST_CLIENT_SECRET`
- `TOSS_INVEST_ACCESS_TOKEN`
- `TOSS_INVEST_ACCOUNT_SEQ`
- `OPENAI_API_KEY` 또는 기타 LLM API Key

처리 절차:

1. 현재 Micro Stage를 `BLOCKED_USER_INPUT_REQUIRED`로 표시
2. `reports/user-requests/MS-xx.xx-user-input-required.md` 생성
3. 사용자가 `.env`에 직접 입력하도록 안내
4. 채팅/로그/리포트에는 원문 출력 금지
5. 사용자가 `입력 완료, 계속 진행`이라고 명령할 때까지 대기

Codex가 허용되는 일:

- `.env.example` 작성
- placeholder 값으로 설정 로더 테스트
- mock token response로 client 테스트
- secret masking 테스트

Codex가 금지되는 일:

- 실제 Secret 생성 또는 추측
- Secret을 채팅에 요청해서 붙여넣게 하기
- `.env` 내용을 통째로 출력
- 인증 실패를 숨기고 다음 단계 진행
