# 26. GitHub Repository & 단계별 커밋 정책

작성일: 2026-06-19  
프로젝트명: `ai_stock`  
GitHub Repository: `https://github.com/JaiIn/ai_stock`  
실행 정책: 로컬 전용, 배포 없음

---

## 1. 목적

이 문서는 Codex가 `ai_stock` 프로젝트를 개발할 때 Git/GitHub를 어떻게 사용할지 정의한다.

목표는 다음과 같다.

1. 한 번에 너무 많은 변경이 커밋되지 않도록 한다.
2. Micro Stage 단위로 변경사항을 추적한다.
3. 여러 Codex 세션이 동시에 작업해도 충돌을 줄인다.
4. 사용자가 각 단계의 변경사항을 확인한 뒤 다음 작업을 지시할 수 있게 한다.
5. 민감정보가 GitHub에 올라가지 않도록 방지한다.

---

## 2. 저장소 기준

```text
Project Name: ai_stock
Repository: https://github.com/JaiIn/ai_stock
Default branch: main
Development mode: local only
Deployment: none
```

이 저장소는 현재 비어 있는 저장소로 가정한다.

Codex는 프로젝트 초기화 시 다음을 확인해야 한다.

```bash
git remote -v
git status
git branch --show-current
```

원격 저장소가 설정되어 있지 않으면 아래 명령을 사용한다.

```bash
git remote add origin https://github.com/JaiIn/ai_stock.git
```

이미 origin이 다른 곳을 가리키면 임의로 변경하지 말고 사용자에게 보고하고 대기한다.

---

## 3. 최우선 Git 규칙

Codex는 다음 규칙을 반드시 따른다.

```text
Micro Stage 1개 완료 = 테스트/보고서 작성 = Git diff 확인 = 커밋 후보 작성 = 사용자 확인 대기
```

Codex가 해도 되는 일:

- `git status` 확인
- `git diff` 확인
- Micro Stage 단위로 `git add` 수행
- Micro Stage 단위 커밋 생성
- 커밋 메시지 작성
- 사용자에게 push 여부 확인 요청

Codex가 하면 안 되는 일:

- 사용자 승인 없이 여러 Micro Stage를 한 커밋에 묶기
- 사용자 승인 없이 `git push` 실행
- 사용자 승인 없이 `main`에 직접 커밋
- 사용자 승인 없이 rebase, reset, force push 실행
- `.env.local`, token, secret, DB 파일, 로그 원문을 Git에 포함
- 실패한 테스트 상태를 정상 커밋으로 표시

---

## 4. 권장 브랜치 전략

로컬 개인 프로젝트이지만, 여러 Codex 세션을 나눠 사용할 예정이므로 브랜치를 역할별로 분리한다.

### 4.1 기본 브랜치

| 브랜치 | 용도 | 직접 작업 가능 여부 |
|---|---|---|
| `main` | 사용자가 승인한 안정본 | 직접 작업 금지 |
| `local/integration` | 여러 세션 결과를 모으는 로컬 통합 브랜치 | PM/Integrator만 |
| `codex/<role>/<micro-stage>` | 각 세션의 실제 작업 브랜치 | 해당 역할 세션만 |

### 4.2 역할별 브랜치 예시

```text
codex/pm/MS-00.01-source-review
codex/backend/MS-02.04-oauth-mock-client
codex/data/MS-03.01-sqlite-session
codex/ai/MS-05.04-rule-based-scoring
codex/paper/MS-06.02-paper-order-create
codex/frontend/MS-07.01-streamlit-shell
codex/qa/MS-08.02-pytest-all
codex/docs/MS-08.04-readme-guide
```

---

## 5. 빈 Repository 초기화 절차

처음 시작할 때는 PM/Integrator 세션이 수행한다.

### 5.1 clone

```bash
git clone https://github.com/JaiIn/ai_stock.git
cd ai_stock
```

### 5.2 초기 브랜치 생성

```bash
git checkout -b codex/pm/MS-00.01-project-docs-init
```

### 5.3 문서 세트 복사

이 문서 ZIP의 내용을 repository root에 복사한다.

복사 후 구조는 대략 아래와 같아야 한다.

```text
ai_stock/
├── CODEX.md
├── README.md
├── docs/
├── roles/
├── references/
└── templates/
```

### 5.4 초기 문서 커밋

```bash
git status
git add CODEX.md README.md docs roles references templates MANIFEST.json
git commit -m "docs(project): MS-00.01 initialize ai_stock planning docs"
```

### 5.5 push는 사용자 승인 후 수행

Codex는 아래처럼 사용자에게 확인을 요청한다.

```text
MS-00.01 초기 문서 커밋을 생성했습니다.
원격 저장소로 push하려면 `push 진행`이라고 지시해주세요.
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

사용자가 승인하면 다음을 수행한다.

```bash
git push -u origin codex/pm/MS-00.01-project-docs-init
```

---

## 6. Micro Stage별 표준 Git 절차

모든 Codex 세션은 Micro Stage 시작 전에 아래 절차를 따른다.

### 6.1 작업 전 확인

```bash
git status
git branch --show-current
git remote -v
```

작업 디렉토리에 다른 세션의 미커밋 변경사항이 있으면 즉시 멈추고 사용자에게 보고한다.

### 6.2 작업 브랜치 생성

```bash
git checkout local/integration
git pull --ff-only origin main
# 또는 사용자가 지정한 기준 브랜치 사용
git checkout -b codex/<role>/<micro-stage-id>-<short-name>
```

예시:

```bash
git checkout -b codex/backend/MS-02.04-oauth-mock-client
```

### 6.3 구현

해당 Micro Stage에 필요한 파일만 수정한다.

다른 역할의 파일을 수정해야 하면 직접 수정하지 말고 `reports/session-handoff/`에 요청서를 작성한다.

### 6.4 테스트

Micro Stage별 테스트를 실행한다.

예시:

```bash
pytest tests/unit/test_auth.py -q
ruff check src tests
```

테스트 결과는 `reports/test-results/`에 저장한다.

### 6.5 완료 체크리스트 작성

아래 템플릿을 사용한다.

```text
templates/micro_stage_completion_checklist_template.md
templates/git_commit_checklist_template.md
```

저장 위치:

```text
reports/micro-stages/MS-xx.xx-<name>.md
reports/git/MS-xx.xx-<name>-commit-checklist.md
```

### 6.6 Git diff 검토

```bash
git status
git diff --stat
git diff
```

확인 포인트:

- Micro Stage 범위를 벗어난 파일이 없는가?
- `.env.local`이 포함되지 않았는가?
- DB 파일이 포함되지 않았는가?
- 로그에 토큰/계좌번호/accountSeq가 포함되지 않았는가?
- 테스트 결과 보고서가 포함되었는가?

### 6.7 커밋 생성

```bash
git add <micro-stage-files>
git commit -m "feat(scope): MS-xx.xx short summary"
```

문서만 변경했다면:

```bash
git commit -m "docs(scope): MS-xx.xx short summary"
```

테스트만 변경했다면:

```bash
git commit -m "test(scope): MS-xx.xx short summary"
```

---

## 7. 커밋 메시지 규칙

형식:

```text
<type>(<scope>): <MicroStageID> <summary>
```

예시:

```text
docs(project): MS-00.01 initialize ai_stock planning docs
chore(project): MS-01.01 create local project skeleton
feat(config): MS-01.04 add settings loader
feat(toss-api): MS-02.04 add mock OAuth token client
test(toss-api): MS-02.06 add retry behavior tests
feat(db): MS-03.03 add watchlist model
feat(recommendation): MS-05.04 add rule-based scoring
feat(frontend): MS-07.01 add Streamlit shell
```

허용 type:

| type | 용도 |
|---|---|
| `docs` | 문서 |
| `chore` | 프로젝트 설정, 구조 |
| `feat` | 기능 추가 |
| `fix` | 버그 수정 |
| `test` | 테스트 |
| `refactor` | 동작 변경 없는 구조 개선 |
| `safety` | 보안/민감정보/실주문 방지 |
| `report` | 리포트/체크리스트 |

권장 scope:

```text
project
config
logging
masking
toss-api
db
market-data
recommendation
paper-trading
risk
frontend
qa
docs
git
```

---

## 8. Push 정책

기본 원칙:

```text
commit은 Micro Stage 완료 후 가능
push는 사용자 승인 후만 가능
```

Codex는 커밋 후 아래 형식으로 사용자에게 보고한다.

```text
Micro Stage: MS-02.04
Branch: codex/backend/MS-02.04-oauth-mock-client
Commit: <commit-hash>
Tests: passed
Sensitive file check: passed

원격 저장소에 push하려면 `push 진행`이라고 지시해주세요.
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

사용자가 승인하면:

```bash
git push -u origin codex/backend/MS-02.04-oauth-mock-client
```

---

## 9. Merge 정책

개인 프로젝트라도 여러 Codex 세션이 작업하므로 merge는 PM/Integrator 세션만 수행한다.

권장 흐름:

```text
role branch -> local/integration -> main
```

Merge 전 필수 조건:

- 해당 Micro Stage 체크리스트 존재
- 테스트 결과 존재
- 민감정보 검사 통과
- `git diff` 검토 완료
- 사용자 승인 존재

Merge 명령 예시:

```bash
git checkout local/integration
git merge --no-ff codex/backend/MS-02.04-oauth-mock-client
pytest -q
ruff check .
git status
```

`main` 반영은 사용자가 명시적으로 승인했을 때만 한다.

---

## 10. 금지 파일

아래 파일은 절대 Git에 포함하지 않는다.

```gitignore
.env
.env.local
.env.*.local
*.db
*.sqlite
*.sqlite3
*.log
logs/
data/*.db
data/*.sqlite
data/*.sqlite3
reports/**/raw-*.json
reports/**/token*.json
reports/**/account*.json
.cache/
__pycache__/
.pytest_cache/
.ruff_cache/
.venv/
```

단, 아래 보고서는 민감정보 마스킹 후 커밋 가능하다.

```text
reports/micro-stages/*.md
reports/test-results/*.md
reports/git/*.md
reports/implementation/*.md
reports/session-handoff/*.md
```

---

## 11. 사용자 입력이 필요한 Git 상황

Codex는 아래 상황에서 즉시 멈춘다.

- GitHub 로그인/인증 필요
- push 권한 없음
- remote URL이 예상과 다름
- merge conflict 발생
- rebase 필요
- force push 필요
- main branch 직접 수정 필요
- 민감정보가 이미 commit history에 들어간 가능성 있음
- GitHub repository visibility 변경 필요

보고 예시:

```text
GitHub push 중 인증이 필요합니다.
제가 대신 인증 정보를 입력하거나 저장할 수 없습니다.
사용자께서 로컬 터미널에서 인증을 완료한 뒤 `인증 완료, 계속`이라고 알려주세요.
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```

---

## 12. GitHub Issue/PR 사용 여부

v0.1에서는 필수는 아니다.

다만 사용자가 원하면 아래 방식으로 확장할 수 있다.

```text
Issue = Micro Stage 단위 작업 카드
Pull Request = role branch 검토 단위
main merge = 사용자 승인된 안정본
```

초기에는 로컬 커밋 + 브랜치 push만으로 충분하다.

---

## 13. 완료 조건

GitHub 커밋 정책이 적용되었다고 판단하려면 아래를 만족해야 한다.

- [ ] 프로젝트명이 `ai_stock`으로 정리되었다.
- [ ] repository URL이 `https://github.com/JaiIn/ai_stock`으로 명시되었다.
- [ ] Micro Stage별 commit 규칙이 정의되었다.
- [ ] push는 사용자 승인 후만 수행하도록 정의되었다.
- [ ] branch naming 규칙이 정의되었다.
- [ ] multi-session 충돌 방지 규칙이 정의되었다.
- [ ] 금지 파일 목록이 정의되었다.
- [ ] commit checklist template이 존재한다.
