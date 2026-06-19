# User Input Required

## 현재 작업

- Stage ID:
- Task:

## 필요한 사용자 입력

- 

## 필요한 이유


## 안전한 입력 방법

`.env` 파일 또는 OS secret manager에 사용자가 직접 입력한다.

```env
# 예시. 실제 값은 채팅/로그/리포트에 출력하지 않는다.
TOSS_INVEST_CLIENT_ID=
TOSS_INVEST_CLIENT_SECRET=
TOSS_INVEST_BASE_URL=https://open-api.tossinvest.com
ALLOW_REAL_ORDER=false
```

## 보안 주의

- 민감값을 채팅에 그대로 붙여넣지 않는다.
- 로그, 리포트, 화면에 원문 출력하지 않는다.
- 입력 후 `설정 완료, 계속 진행`이라고 사용자에게 요청한다.

## 대기 상태

사용자 입력을 기다린다. 다음 명령이 오기 전까지 다음 단계로 진행하지 않는다.
