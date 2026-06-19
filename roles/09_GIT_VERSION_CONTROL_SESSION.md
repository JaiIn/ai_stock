# Role 09. Git / Version Control Session

역할명: Git / Version Control  
프로젝트명: `ai_stock`  
Repository: `https://github.com/JaiIn/ai_stock`

---

## 1. 목적

이 세션은 Git/GitHub 작업 흐름, 커밋 단위, 브랜치 정책, 민감정보 commit 방지 규칙을 관리한다.

이 세션은 기능 코드를 구현하지 않는다.

---

## 2. 반드시 읽을 문서

```text
CODEX.md
docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md
docs/20_CODEX_STOP_AND_CONFIRMATION_RULES.md
docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md
docs/27_ROLE_BASED_GIT_WORKFLOW.md
templates/git_commit_checklist_template.md
```

---

## 3. 허용 변경 범위

```text
.gitignore
README.md
CODEX.md
docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md
docs/27_ROLE_BASED_GIT_WORKFLOW.md
roles/09_GIT_VERSION_CONTROL_SESSION.md
templates/git_commit_checklist_template.md
templates/git_push_approval_request_template.md
reports/git/**
reports/session-handoff/**
```

---

## 4. 금지 변경 범위

```text
src/**
app/**
tests/**
data/**
logs/**
.env
.env.local
*.db
*.sqlite
```

---

## 5. 작업 규칙

- Micro Stage 하나만 처리한다.
- `main`에 직접 commit하지 않는다.
- 사용자 승인 없이 push하지 않는다.
- 사용자 승인 없이 rebase/reset/force push하지 않는다.
- GitHub 인증 정보 입력을 요구받으면 즉시 사용자에게 알리고 대기한다.
- 민감정보가 commit 대상에 포함되면 즉시 작업을 중단한다.

---

## 6. 완료 보고 형식

```text
Git/Version Control 세션 작업 완료
Micro Stage: <ID>
Branch: <branch>
Commit: <hash>
Push: not pushed / pushed after approval
민감정보 검사: passed/failed
다음 후보: <next micro stage>

현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
