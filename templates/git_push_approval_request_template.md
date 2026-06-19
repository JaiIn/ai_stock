# Git Push Approval Request Template

Micro Stage: `MS-xx.xx`  
Role: `<role>`  
Branch: `codex/<role>/MS-xx.xx-<short-name>`  
Commit: `<commit-hash>`

---

## 1. Push 요청 사유

이번 Micro Stage의 변경사항을 GitHub 원격 저장소에 올리기 위해 사용자 승인이 필요하다.

Repository:

```text
https://github.com/JaiIn/ai_stock
```

---

## 2. 커밋 요약

- 변경 목적:
- 주요 변경 파일:
- 테스트 결과:
- 민감정보 검사 결과:

---

## 3. 실행 예정 명령

```bash
git push -u origin codex/<role>/MS-xx.xx-<short-name>
```

---

## 4. 사용자에게 요청할 문구

```text
위 커밋을 GitHub 원격 저장소에 push하려면 `push 진행`이라고 지시해주세요.
아직 push하지 않았습니다.
현재 Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
