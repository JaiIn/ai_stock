# Git Commit Checklist Template

Micro Stage: `MS-xx.xx`  
Role: `<PM | Backend | Data | AI | Paper | Frontend | QA | Docs | Git>`  
Branch: `codex/<role>/MS-xx.xx-<short-name>`  
Date: `YYYY-MM-DD`

---

## 1. 변경 요약

- 변경 목적:
- 변경 파일:
- 생성 파일:
- 삭제 파일:

---

## 2. Micro Stage 범위 확인

- [ ] 이번 커밋은 Micro Stage 1개 범위만 포함한다.
- [ ] 다른 역할의 파일을 직접 수정하지 않았다.
- [ ] 범위를 벗어난 변경은 `reports/session-handoff/`에 기록했다.
- [ ] 사용자 입력이 필요한 항목을 무시하지 않았다.

---

## 3. 테스트 확인

실행한 명령:

```bash
# 예시
pytest -q
ruff check .
```

결과:

- [ ] 통과
- [ ] 실패, 사용자 보고 필요
- [ ] 일부 skip, 사유 기록 완료

테스트 결과 파일:

```text
reports/test-results/MS-xx.xx-<name>.md
```

---

## 4. 민감정보 확인

- [ ] `.env.local`이 commit 대상에 없다.
- [ ] Access Token 원문이 없다.
- [ ] Client Secret 원문이 없다.
- [ ] accountSeq 원문이 없다.
- [ ] 계좌번호 원문이 없다.
- [ ] DB 파일이 없다.
- [ ] 로그 원문 파일이 없다.
- [ ] 리포트 내 민감정보는 마스킹되어 있다.

확인 명령 예시:

```bash
git status
git diff --cached --stat
git diff --cached
```

---

## 5. 커밋 정보

권장 커밋 메시지:

```text
<type>(<scope>): MS-xx.xx <summary>
```

실제 커밋 메시지:

```text

```

Commit Hash:

```text

```

---

## 6. Push 여부

- [ ] 아직 push하지 않음
- [ ] 사용자 승인 후 push 완료

Push 명령:

```bash
git push -u origin codex/<role>/MS-xx.xx-<short-name>
```

---

## 7. 사용자 보고 문구

```text
Micro Stage: MS-xx.xx
Branch: codex/<role>/MS-xx.xx-<short-name>
Commit: <hash or not-yet-committed>
Tests: <passed/failed/skipped>
Sensitive file check: <passed/failed>

원격 저장소에 push하려면 `push 진행`이라고 지시해주세요.
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
