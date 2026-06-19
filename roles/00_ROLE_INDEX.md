# 역할별 Codex 세션 인덱스

이 폴더는 사용자가 여러 Codex 세션을 동시에 또는 순차적으로 운영할 때 각 세션이 자신의 역할만 수행하도록 하기 위한 지침이다.

공통 규칙:

1. 모든 세션은 `CODEX.md`를 먼저 읽는다.
2. 모든 세션은 `docs/18_MICRO_STAGE_DEVELOPMENT_PROCESS.md`를 따른다.
3. 모든 세션은 자기 역할 문서를 읽는다.
4. 사용자 명령 1회당 Micro Stage 1개만 수행한다.
5. 자기 역할 범위 밖 파일을 수정하지 않는다.
6. 다른 역할 작업이 필요하면 `reports/session-handoff/`에 인수인계 문서를 작성한다.
7. 완료 후 사용자 명령을 기다린다.
8. 모든 세션은 GitHub push 전 사용자 승인을 받는다.
9. 모든 세션은 `docs/26_GITHUB_REPOSITORY_AND_COMMIT_POLICY.md`를 따른다.

역할 목록:

| 파일 | 역할 |
|---|---|
| `01_PM_INTEGRATOR_SESSION.md` | 전체 진행/충돌 조정 |
| `02_BACKEND_API_CLIENT_SESSION.md` | Toss API client/auth/http |
| `03_FRONTEND_UI_SESSION.md` | Streamlit UI |
| `04_DATA_DB_SESSION.md` | SQLite/Repository |
| `05_AI_RECOMMENDATION_SESSION.md` | 추천 엔진/LLM 설명 |
| `06_PAPER_TRADING_RISK_SESSION.md` | 모의투자/리스크 |
| `07_QA_TEST_LOGGING_SESSION.md` | 테스트/로그/리포트 |
| `08_DOCS_GUIDE_SESSION.md` | 문서/가이드 |
| `09_GIT_VERSION_CONTROL_SESSION.md` | Git/GitHub/커밋 정책 |
