# 23. 로컬 전용 실행 정책

작성일: 2026-06-19  
적용 범위: v0.1 전체

---

## 1. 핵심 결정

이 프로젝트는 **배포를 고려하지 않는다.**

v0.1은 사용자의 로컬 PC에서만 실행한다.

```text
지원: 로컬 실행
제외: 서버 배포, 클라우드 배포, 외부 사용자 접속, 상시 운영 서비스화
```

---

## 2. 로컬 전용 원칙

### 2.1 실행 주소

허용:

```text
127.0.0.1
localhost
```

금지:

```text
0.0.0.0
public IP
cloud domain
reverse proxy domain
```

Streamlit 실행 예시:

```bash
streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

---

### 2.2 데이터 저장

모든 데이터는 로컬 디스크에 저장한다.

```text
data/local/app.db
logs/
reports/
```

외부 저장소 사용 금지:

- S3
- RDS
- Cloud SQL
- Supabase
- Firebase
- MongoDB Atlas
- 외부 Redis

---

### 2.3 Secret 저장

실제 secret은 `.env.local`에만 저장한다.

```text
.env.example  -> 샘플만 포함
.env.local    -> 실제 값, Git 제외
```

Codex는 `.env.local` 내용을 출력하지 않는다.

---

## 3. 배포 관련 산출물 생성 금지

Codex는 v0.1에서 아래 파일을 만들지 않는다.

```text
Dockerfile
docker-compose.yml
kubernetes/*.yaml
nginx.conf
Procfile
render.yaml
fly.toml
cloudbuild.yaml
.github/workflows/deploy.yml
terraform/
helm/
```

예외:

- 사용자가 명시적으로 “배포 검토 문서만 작성”하라고 한 경우 문서 작성은 가능
- 실제 배포 스크립트나 설정 파일 생성은 별도 승인 필요

---

## 4. 로컬 실행 구조

권장 구조:

```text
[Local Browser]
      |
      v
[Streamlit UI: 127.0.0.1:8501]
      |
      v
[Python Service Layer]
      |
      +--> [SQLite: data/local/app.db]
      +--> [Toss API Client: outbound HTTPS only]
      +--> [LLM Provider: optional outbound HTTPS]
      +--> [Reports/Logs: local files]
```

외부에서 들어오는 inbound traffic은 허용하지 않는다.

Toss API와 LLM API는 사용자가 승인한 경우에만 outbound HTTPS 요청을 보낼 수 있다.

---

## 5. 로컬 전용으로 인한 설계 단순화

| 항목 | 로컬 전용 결정 |
|---|---|
| 인증 | 앱 로그인 기능 없음. OS 사용자 개인 실행 전제 |
| 사용자 관리 | 다중 사용자 없음 |
| DB | SQLite 단일 파일 |
| 캐시 | 메모리/SQLite 캐시 |
| 백그라운드 작업 | 수동 새로고침 우선 |
| 스케줄러 | v0.1 제외 또는 로컬 수동 실행 |
| 모니터링 | 로컬 로그/리포트 |
| 장애 대응 | 로그 확인 + 재실행 |
| 백업 | DB 파일 수동 복사 |

---

## 6. 로컬 전용이어도 반드시 지켜야 할 보안

로컬 실행이라고 해서 보안이 사라지는 것은 아니다.

필수:

- secret masking
- `.env.local` Git 제외
- 실주문 기본 차단
- API 호출 로그에서 토큰/계좌 마스킹
- DB 백업 파일에도 계좌 정보 포함 가능성 표시
- 리포트에 계좌번호/accountSeq 원문 금지

---

## 7. Codex 중단 조건

Codex는 다음 상황에서 중단한다.

- 외부 접속을 위한 설정이 필요하다고 판단한 경우
- `0.0.0.0` 바인딩을 추가하려는 경우
- Docker/배포 관련 파일을 만들려는 경우
- 클라우드 저장소를 사용하려는 경우
- DB를 외부 DB로 바꾸려는 경우
- 앱 로그인/사용자 관리 기능을 추가하려는 경우

중단 메시지 예시:

```text
이 변경은 로컬 전용 정책을 벗어납니다.
현재 v0.1 정책에서는 배포/외부 접속/클라우드 리소스를 사용하지 않습니다.
진행하려면 사용자 승인이 필요합니다.
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
