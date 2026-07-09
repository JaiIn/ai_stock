# AI Stock Next Roadmap: MS-09 to MS-20

## Required Roadmap Stage Titles

- MS-09 Candidate / Watchlist Foundation
- MS-10 Feature & Data Quality Model
- MS-11 Deterministic Scoring Model
- MS-12 Recommendation List UI
- MS-13 Toss Read-only API Preflight
- MS-14 Toss Read-only Market Data Integration
- MS-15 Local Snapshot Refresh Pipeline
- MS-16 Paper Trading Engine
- MS-17 Backtest & Performance Review
- MS-18 Optional LLM / AI Reasoning Layer
- MS-19 Integrated Strategy Dashboard
- MS-20 Final Local MVP Release

## 문서 메타데이터

- 프로젝트명: `ai_stock`
- 권장 저장 위치: `docs/29_AI_STOCK_NEXT_ROADMAP_MS09_MS20.md`
- 기준 커밋: `7630d20 docs(ai): MS-08.07 add recommendation panel final checkpoint`
- 목적: MS-08 이후 local-only MVP 완료까지의 MS-09~MS-20 장기 개발 계획 정의
- 이번 문서 작성에서는 OpenAI API KEY, Toss API KEY, Toss SECRET KEY, accountSeq가 필요하지 않음

---

## 1. 문서 개요

이 문서는 MS-08에서 완료한 mock-only recommendation panel 안전 UI 흐름 이후, `ai_stock` 프로젝트를 local-only MVP로 완성하기 위한 장기 로드맵을 정의한다.

핵심 진행 방향은 다음과 같다.

```text
후보군/관심종목 → feature/data quality → deterministic scoring → recommendation list UI → Toss read-only → local snapshot refresh → paper trading → backtest → optional LLM → integrated dashboard → final release
```

---

## 2. 현재 완료 지점

```text
origin/main = 7630d20
MS-08.07 recommendation panel final checkpoint 완료
```

현재 가능한 범위:

- read-only dashboard에 mock-only recommendation panel 표시
- observation-only / not investment advice / no real recommendation 정책 유지
- AppTest smoke 완료
- local Streamlit server smoke 완료

현재 불가능한 범위:

- 실제 AI 추천
- 실제 매수/매도/보유 지시
- LLM/OpenAI 호출
- Toss API 호출
- OAuth
- accountSeq
- 주문/계좌/자산/잔고/체결
- DB write
- 실주문 버튼

---

## 3. MS-08 완료 상태 요약

- MS-08.01: recommendation safety preflight 완료
- MS-08.02: deterministic mock-only policy model 완료
- MS-08.03: explanation UI preflight contract 완료
- MS-08.04: mock-only recommendation panel UI integration 완료
- MS-08.05: AppTest smoke 완료
- MS-08.06: local Streamlit server smoke 완료
- MS-08.07: final checkpoint 완료

---

## 4. 전체 프로젝트 완료를 위한 남은 큰 흐름

| Stage | 이름 | 핵심 목적 |
|---|---|---|
| MS-09 | Candidate / Watchlist Foundation | 분석 대상 후보군과 관심종목 입력 구조를 정의한다. |
| MS-10 | Feature & Data Quality Model | 후보 종목을 평가하기 위한 가격/거래량/데이터 충분성/리스크/추세 feature를 정의한다. |
| MS-11 | Deterministic Scoring Model | AI 없이 deterministic score, risk-adjusted score, data-completeness penalty, safe label mapping을 만든다. |
| MS-12 | Recommendation List UI | 여러 후보 종목을 read-only dashboard에서 observation list / candidate list로 비교 표시한다. |
| MS-13 | Toss Read-only API Preflight | Toss API 실제 호출 전 read-only endpoint, auth/token, credential handling, response sanitization 정책을 설계한다. |
| MS-14 | Toss Read-only Market Data Integration | 실제 Toss read-only market data를 최소 범위로 연동한다. |
| MS-15 | Local Snapshot Refresh Pipeline | sanitized read-only market data를 local snapshot DB에 안전하게 저장/갱신한다. |
| MS-16 | Paper Trading Engine | 실제 주문 없이 local-only simulated order/fill/ledger/PnL을 구현한다. |
| MS-17 | Backtest & Performance Review | historical local snapshot 기반 strategy replay와 성과/리스크 report를 만든다. |
| MS-18 | Optional LLM / AI Reasoning Layer | 선택적으로 OpenAI/LLM을 설명·요약 보조 역할로 붙인다. |
| MS-19 | Integrated Strategy Dashboard | candidate, scoring, explanation, paper trading, backtest/performance를 하나의 local dashboard로 통합한다. |
| MS-20 | Final Local MVP Release | local-only MVP의 safety/credential/DB/test/runbook/release checkpoint를 완료한다. |

---

## 09. MS-09: Candidate / Watchlist Foundation

### 09.1 목적

분석 대상 후보군과 관심종목 입력 구조를 정의한다.

### 09.2 왜 이 단계가 필요한가

후보군 계약 없이 scoring/UI/API/paper trading으로 가면 분석 대상 기준이 흔들리기 때문이다.

### 09.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 09.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 09.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 09.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 09.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 09.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-09.*.md
```

### 09.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-09.01 | candidate input contract preflight | 후보 입력 source, 금지 source, credential 불필요 정책을 정의한다. |
| MS-09.02 | watchlist data model | symbol/name/market/source/reason/tags/enabled 기반 watchlist item 모델을 정의한다. |
| MS-09.03 | manual/local watchlist source | 수동 또는 local-only watchlist source를 만든다. |
| MS-09.04 | candidate normalization and validation | 종목코드/종목명 정규화, 중복 제거, unsupported/data-missing 처리 정책을 구현한다. |
| MS-09.05 | candidate selector UI preflight | 후보 selector UI의 safe/forbidden contract를 정의한다. |
| MS-09.06 | candidate selector UI integration | read-only dashboard에 후보 selector를 안전하게 표시한다. |
| MS-09.07 | AppTest smoke | 후보 selector 렌더링과 forbidden UI 부재를 검증한다. |
| MS-09.08 | server smoke | local Streamlit server 기동/health/종료를 검증한다. |
| MS-09.09 | final checkpoint | MS-09 완료 범위와 미지원 범위를 문서화한다. |

### 09.10 하위 Micro Stage 상세

#### MS-09.01 candidate input contract preflight

- 목적: 후보 입력 source, 금지 source, credential 불필요 정책을 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.02 watchlist data model

- 목적: symbol/name/market/source/reason/tags/enabled 기반 watchlist item 모델을 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.03 manual/local watchlist source

- 목적: 수동 또는 local-only watchlist source를 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.04 candidate normalization and validation

- 목적: 종목코드/종목명 정규화, 중복 제거, unsupported/data-missing 처리 정책을 구현한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.05 candidate selector UI preflight

- 목적: 후보 selector UI의 safe/forbidden contract를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.06 candidate selector UI integration

- 목적: read-only dashboard에 후보 selector를 안전하게 표시한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.07 AppTest smoke

- 목적: 후보 selector 렌더링과 forbidden UI 부재를 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.08 server smoke

- 목적: local Streamlit server 기동/health/종료를 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-09.09 final checkpoint

- 목적: MS-09 완료 범위와 미지원 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 09.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 09.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 09.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 09.14 DB write 허용 여부

- 원칙 불허

### 09.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 09.16 OpenAI/LLM 사용 여부

- 불사용

### 09.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 09.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 09.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 10. MS-10: Feature & Data Quality Model

### 10.1 목적

후보 종목을 평가하기 위한 가격/거래량/데이터 충분성/리스크/추세 feature를 정의한다.

### 10.2 왜 이 단계가 필요한가

후보만으로는 비교가 불가능하며, 추천 전 데이터 품질 판단이 먼저 필요하기 때문이다.

### 10.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 10.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 10.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 10.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 10.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 10.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-10.*.md
```

### 10.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-10.01 | feature contract preflight | feature 입력/출력/금지 범위를 정의한다. |
| MS-10.02 | price summary feature | 최근 가격, 변화율, 가격 존재 여부를 요약한다. |
| MS-10.03 | volume summary feature | 거래량 존재 여부와 이상치를 요약한다. |
| MS-10.04 | data completeness feature | 데이터 부족/결측/분석 불가 사유를 산출한다. |
| MS-10.05 | volatility/risk flag feature | 급등락/변동성/리스크 flag를 산출한다. |
| MS-10.06 | recent trend feature | 최근 1주/1개월 등 추세 feature를 산출한다. |
| MS-10.07 | feature validation tests | 동일 입력 동일 출력과 데이터 부족 fallback을 검증한다. |
| MS-10.08 | final checkpoint | MS-10 완료 범위를 문서화한다. |

### 10.10 하위 Micro Stage 상세

#### MS-10.01 feature contract preflight

- 목적: feature 입력/출력/금지 범위를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.02 price summary feature

- 목적: 최근 가격, 변화율, 가격 존재 여부를 요약한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.03 volume summary feature

- 목적: 거래량 존재 여부와 이상치를 요약한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.04 data completeness feature

- 목적: 데이터 부족/결측/분석 불가 사유를 산출한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.05 volatility/risk flag feature

- 목적: 급등락/변동성/리스크 flag를 산출한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.06 recent trend feature

- 목적: 최근 1주/1개월 등 추세 feature를 산출한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.07 feature validation tests

- 목적: 동일 입력 동일 출력과 데이터 부족 fallback을 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-10.08 final checkpoint

- 목적: MS-10 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 10.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 10.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 10.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 10.14 DB write 허용 여부

- 불허

### 10.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 10.16 OpenAI/LLM 사용 여부

- 불사용

### 10.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 10.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 10.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 11. MS-11: Deterministic Scoring Model

### 11.1 목적

AI 없이 deterministic score, risk-adjusted score, data-completeness penalty, safe label mapping을 만든다.

### 11.2 왜 이 단계가 필요한가

외부 AI나 실시간 API 이전에 재현 가능하고 테스트 가능한 관찰 점수 모델이 필요하기 때문이다.

### 11.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 11.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 11.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 11.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 11.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 11.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-11.*.md
```

### 11.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-11.01 | scoring policy preflight | 점수 정책과 금지 문구를 정의한다. |
| MS-11.02 | deterministic score model | 기본 score model을 구현한다. |
| MS-11.03 | risk-adjusted score | risk flag를 반영한 점수를 만든다. |
| MS-11.04 | data-completeness penalty | 데이터 부족 penalty를 적용한다. |
| MS-11.05 | label mapping | observation_only/risk_review/insufficient_data 같은 safe label로 매핑한다. |
| MS-11.06 | scoring validation tests | buy/sell/hold label과 action_allowed=true를 실패시킨다. |
| MS-11.07 | final checkpoint | MS-11 완료 범위를 문서화한다. |

### 11.10 하위 Micro Stage 상세

#### MS-11.01 scoring policy preflight

- 목적: 점수 정책과 금지 문구를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-11.02 deterministic score model

- 목적: 기본 score model을 구현한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-11.03 risk-adjusted score

- 목적: risk flag를 반영한 점수를 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-11.04 data-completeness penalty

- 목적: 데이터 부족 penalty를 적용한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-11.05 label mapping

- 목적: observation_only/risk_review/insufficient_data 같은 safe label로 매핑한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-11.06 scoring validation tests

- 목적: buy/sell/hold label과 action_allowed=true를 실패시킨다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-11.07 final checkpoint

- 목적: MS-11 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 11.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 11.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 11.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 11.14 DB write 허용 여부

- 불허

### 11.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 11.16 OpenAI/LLM 사용 여부

- 불사용

### 11.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 11.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 11.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 12. MS-12: Recommendation List UI

### 12.1 목적

여러 후보 종목을 read-only dashboard에서 observation list / candidate list로 비교 표시한다.

### 12.2 왜 이 단계가 필요한가

단일 mock panel을 넘어서 후보군 비교 화면이 필요하기 때문이다.

### 12.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 12.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 12.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 12.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 12.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 12.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-12.*.md
```

### 12.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-12.01 | recommendation list UI preflight | 복수 후보 UI의 safe contract를 정의한다. |
| MS-12.02 | candidate table UI | 후보 테이블을 표시한다. |
| MS-12.03 | score/risk/completeness display | 점수/리스크/데이터 충분성을 표시한다. |
| MS-12.04 | safe explanation expansion | 후보별 안전 설명 확장을 제공한다. |
| MS-12.05 | AppTest smoke | 테이블 렌더링과 forbidden UI 부재를 검증한다. |
| MS-12.06 | server smoke | local server 기동/종료를 검증한다. |
| MS-12.07 | final checkpoint | MS-12 완료 범위를 문서화한다. |

### 12.10 하위 Micro Stage 상세

#### MS-12.01 recommendation list UI preflight

- 목적: 복수 후보 UI의 safe contract를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-12.02 candidate table UI

- 목적: 후보 테이블을 표시한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-12.03 score/risk/completeness display

- 목적: 점수/리스크/데이터 충분성을 표시한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-12.04 safe explanation expansion

- 목적: 후보별 안전 설명 확장을 제공한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-12.05 AppTest smoke

- 목적: 테이블 렌더링과 forbidden UI 부재를 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-12.06 server smoke

- 목적: local server 기동/종료를 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-12.07 final checkpoint

- 목적: MS-12 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 12.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 12.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 12.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 12.14 DB write 허용 여부

- 불허

### 12.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 12.16 OpenAI/LLM 사용 여부

- 불사용

### 12.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 12.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 12.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 13. MS-13: Toss Read-only API Preflight

### 13.1 목적

Toss API 실제 호출 전 read-only endpoint, auth/token, credential handling, response sanitization 정책을 설계한다.

### 13.2 왜 이 단계가 필요한가

실제 키 사용 전 endpoint 경계와 token/secret 출력 금지 정책을 고정해야 하기 때문이다.

### 13.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 13.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 13.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 13.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 13.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 13.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-13.*.md
```

### 13.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-13.01 | Toss read-only endpoint matrix review | read-only endpoint allowlist와 forbidden endpoint blocklist를 정리한다. |
| MS-13.02 | auth/token safety policy | token 발급/저장/출력 금지 정책을 정의한다. |
| MS-13.03 | credential handling policy | API KEY/SECRET KEY 입력·저장·마스킹 정책을 정의한다. |
| MS-13.04 | read-only client interface design | 실제 호출 없이 client interface를 설계한다. |
| MS-13.05 | no-live mock adapter | no-live mock adapter를 구현한다. |
| MS-13.06 | contract tests | read-only/forbidden endpoint contract를 검증한다. |
| MS-13.07 | final checkpoint | MS-13 완료 범위를 문서화한다. |

### 13.10 하위 Micro Stage 상세

#### MS-13.01 Toss read-only endpoint matrix review

- 목적: read-only endpoint allowlist와 forbidden endpoint blocklist를 정리한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-13.02 auth/token safety policy

- 목적: token 발급/저장/출력 금지 정책을 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-13.03 credential handling policy

- 목적: API KEY/SECRET KEY 입력·저장·마스킹 정책을 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-13.04 read-only client interface design

- 목적: 실제 호출 없이 client interface를 설계한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-13.05 no-live mock adapter

- 목적: no-live mock adapter를 구현한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-13.06 contract tests

- 목적: read-only/forbidden endpoint contract를 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-13.07 final checkpoint

- 목적: MS-13 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 13.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 13.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 13.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 13.14 DB write 허용 여부

- 불허

### 13.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 13.16 OpenAI/LLM 사용 여부

- 불사용

### 13.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 13.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 13.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 14. MS-14: Toss Read-only Market Data Integration

### 14.1 목적

실제 Toss read-only market data를 최소 범위로 연동한다.

### 14.2 왜 이 단계가 필요한가

local snapshot을 최신화하려면 실제 read-only market data 수집이 필요하기 때문이다.

### 14.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 14.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 14.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 14.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 14.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 14.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-14.*.md
```

### 14.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-14.01 | Toss auth dry-run preflight | live 직전 credential/safety를 재확인한다. |
| MS-14.02 | Access Token issue smoke | 사용자 승인 후 최소 token issue smoke를 수행한다. |
| MS-14.03 | market data read-only smoke | 시장 데이터 read-only smoke를 수행한다. |
| MS-14.04 | symbol info read-only smoke | 종목 정보 read-only smoke를 수행한다. |
| MS-14.05 | response sanitization | raw response를 저장하지 않고 sanitize한다. |
| MS-14.06 | local snapshot import preflight | DB import 전 safety preflight를 수행한다. |
| MS-14.07 | final checkpoint | MS-14 완료 범위를 문서화한다. |

### 14.10 하위 Micro Stage 상세

#### MS-14.01 Toss auth dry-run preflight

- 목적: live 직전 credential/safety를 재확인한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-14.02 Access Token issue smoke

- 목적: 사용자 승인 후 최소 token issue smoke를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-14.03 market data read-only smoke

- 목적: 시장 데이터 read-only smoke를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-14.04 symbol info read-only smoke

- 목적: 종목 정보 read-only smoke를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-14.05 response sanitization

- 목적: raw response를 저장하지 않고 sanitize한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-14.06 local snapshot import preflight

- 목적: DB import 전 safety preflight를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-14.07 final checkpoint

- 목적: MS-14 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 14.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 14.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 14.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: MS-14.02부터 필요 가능
- accountSeq: 불필요

### 14.14 DB write 허용 여부

- 원칙 불허

### 14.15 Toss API 사용 여부

- read-only로 제한 가능

### 14.16 OpenAI/LLM 사용 여부

- 불사용

### 14.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 14.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 14.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 15. MS-15: Local Snapshot Refresh Pipeline

### 15.1 목적

sanitized read-only market data를 local snapshot DB에 안전하게 저장/갱신한다.

### 15.2 왜 이 단계가 필요한가

dashboard와 scoring이 갱신 데이터를 사용하려면 local snapshot refresh가 필요하기 때문이다.

### 15.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 15.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 15.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 15.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 15.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 15.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-15.*.md
```

### 15.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-15.01 | snapshot schema review | local snapshot schema를 검토한다. |
| MS-15.02 | market data import pipeline | sanitized data import pipeline을 만든다. |
| MS-15.03 | idempotent local DB write | 중복/재실행 안전한 local DB write를 구현한다. |
| MS-15.04 | refresh log/report | refresh 결과와 실패 사유를 기록한다. |
| MS-15.05 | read-only dashboard compatibility | dashboard read-only 호환성을 검증한다. |
| MS-15.06 | rollback/safety tests | rollback과 DB tracking 안전성을 검증한다. |
| MS-15.07 | final checkpoint | MS-15 완료 범위를 문서화한다. |

### 15.10 하위 Micro Stage 상세

#### MS-15.01 snapshot schema review

- 목적: local snapshot schema를 검토한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-15.02 market data import pipeline

- 목적: sanitized data import pipeline을 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-15.03 idempotent local DB write

- 목적: 중복/재실행 안전한 local DB write를 구현한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-15.04 refresh log/report

- 목적: refresh 결과와 실패 사유를 기록한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-15.05 read-only dashboard compatibility

- 목적: dashboard read-only 호환성을 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-15.06 rollback/safety tests

- 목적: rollback과 DB tracking 안전성을 검증한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-15.07 final checkpoint

- 목적: MS-15 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 15.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 15.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 15.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 필요 가능
- accountSeq: 불필요

### 15.14 DB write 허용 여부

- local snapshot 한정 허용

### 15.15 Toss API 사용 여부

- read-only로 제한 가능

### 15.16 OpenAI/LLM 사용 여부

- 불사용

### 15.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 없음
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 15.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 15.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 16. MS-16: Paper Trading Engine

### 16.1 목적

실제 주문 없이 local-only simulated order/fill/ledger/PnL을 구현한다.

### 16.2 왜 이 단계가 필요한가

실거래 없이 전략 동작과 가상 성과를 확인할 수 있어야 하기 때문이다.

### 16.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 16.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 16.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 16.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 16.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 16.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-16.*.md
```

### 16.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-16.01 | paper trading safety preflight | real order와 paper order 경계를 정의한다. |
| MS-16.02 | virtual cash model | 가상 현금 모델을 만든다. |
| MS-16.03 | virtual position model | 가상 포지션 모델을 만든다. |
| MS-16.04 | simulated order model | 모의 주문 모델을 만든다. |
| MS-16.05 | simulated fill model | 모의 체결 모델을 만든다. |
| MS-16.06 | paper portfolio ledger | paper ledger를 저장한다. |
| MS-16.07 | paper PnL calculation | paper PnL을 계산한다. |
| MS-16.08 | dashboard integration | dashboard에 paper portfolio를 표시한다. |
| MS-16.09 | AppTest/server smoke | 렌더/서버 smoke를 수행한다. |
| MS-16.10 | final checkpoint | MS-16 완료 범위를 문서화한다. |

### 16.10 하위 Micro Stage 상세

#### MS-16.01 paper trading safety preflight

- 목적: real order와 paper order 경계를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.02 virtual cash model

- 목적: 가상 현금 모델을 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.03 virtual position model

- 목적: 가상 포지션 모델을 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.04 simulated order model

- 목적: 모의 주문 모델을 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.05 simulated fill model

- 목적: 모의 체결 모델을 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.06 paper portfolio ledger

- 목적: paper ledger를 저장한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.07 paper PnL calculation

- 목적: paper PnL을 계산한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.08 dashboard integration

- 목적: dashboard에 paper portfolio를 표시한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.09 AppTest/server smoke

- 목적: 렌더/서버 smoke를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-16.10 final checkpoint

- 목적: MS-16 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 16.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 16.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 16.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 16.14 DB write 허용 여부

- paper ledger 한정 허용

### 16.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 16.16 OpenAI/LLM 사용 여부

- 불사용

### 16.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 금지
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 16.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 16.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 17. MS-17: Backtest & Performance Review

### 17.1 목적

historical local snapshot 기반 strategy replay와 성과/리스크 report를 만든다.

### 17.2 왜 이 단계가 필요한가

paper strategy가 유용한지 검증하려면 과거 데이터 기반 replay가 필요하기 때문이다.

### 17.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 17.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 17.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 17.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 17.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 17.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-17.*.md
```

### 17.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-17.01 | backtest policy preflight | backtest 정책과 금지 문구를 정의한다. |
| MS-17.02 | historical snapshot loader | 과거 snapshot loader를 만든다. |
| MS-17.03 | strategy replay engine | strategy replay engine을 구현한다. |
| MS-17.04 | performance metrics | 수익률/승률/drawdown 지표를 계산한다. |
| MS-17.05 | drawdown/risk report | 리스크 report를 만든다. |
| MS-17.06 | dashboard/report integration | dashboard/report에 표시한다. |
| MS-17.07 | final checkpoint | MS-17 완료 범위를 문서화한다. |

### 17.10 하위 Micro Stage 상세

#### MS-17.01 backtest policy preflight

- 목적: backtest 정책과 금지 문구를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-17.02 historical snapshot loader

- 목적: 과거 snapshot loader를 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-17.03 strategy replay engine

- 목적: strategy replay engine을 구현한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-17.04 performance metrics

- 목적: 수익률/승률/drawdown 지표를 계산한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-17.05 drawdown/risk report

- 목적: 리스크 report를 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-17.06 dashboard/report integration

- 목적: dashboard/report에 표시한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-17.07 final checkpoint

- 목적: MS-17 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 17.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 17.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 17.13 필요한 credential 여부

- OpenAI API KEY: 불필요
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 17.14 DB write 허용 여부

- backtest result 한정 가능

### 17.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 17.16 OpenAI/LLM 사용 여부

- 불사용

### 17.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 금지
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 17.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 17.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 18. MS-18: Optional LLM / AI Reasoning Layer

### 18.1 목적

선택적으로 OpenAI/LLM을 설명·요약 보조 역할로 붙인다.

### 18.2 왜 이 단계가 필요한가

자연어 설명은 유용하지만 AI가 직접 투자 지시를 내리지 않도록 안전장치가 필요하기 때문이다.

### 18.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 18.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 18.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 18.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 18.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 18.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-18.*.md
```

### 18.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-18.01 | LLM safety preflight | LLM 안전 정책을 정의한다. |
| MS-18.02 | prompt contract | prompt 입력/출력/금지 범위를 정의한다. |
| MS-18.03 | no-key mock LLM adapter | API key 없는 mock adapter를 만든다. |
| MS-18.04 | explanation sanitizer | LLM 출력 sanitizer를 만든다. |
| MS-18.05 | OpenAI adapter preflight | OpenAI adapter live 전 preflight를 수행한다. |
| MS-18.06 | OpenAI live smoke | 명시 승인 후 최소 live smoke를 수행한다. |
| MS-18.07 | LLM output validation | LLM 출력 validation을 수행한다. |
| MS-18.08 | final checkpoint | MS-18 완료 범위를 문서화한다. |

### 18.10 하위 Micro Stage 상세

#### MS-18.01 LLM safety preflight

- 목적: LLM 안전 정책을 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.02 prompt contract

- 목적: prompt 입력/출력/금지 범위를 정의한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.03 no-key mock LLM adapter

- 목적: API key 없는 mock adapter를 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.04 explanation sanitizer

- 목적: LLM 출력 sanitizer를 만든다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.05 OpenAI adapter preflight

- 목적: OpenAI adapter live 전 preflight를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.06 OpenAI live smoke

- 목적: 명시 승인 후 최소 live smoke를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.07 LLM output validation

- 목적: LLM 출력 validation을 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-18.08 final checkpoint

- 목적: MS-18 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 18.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 18.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 18.13 필요한 credential 여부

- OpenAI API KEY: MS-18.06부터 필요 가능
- Toss API KEY / SECRET KEY: 불필요
- accountSeq: 불필요

### 18.14 DB write 허용 여부

- 원칙 불허

### 18.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 18.16 OpenAI/LLM 사용 여부

- 명시 승인된 live smoke 하위 단계에서만 가능

### 18.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 금지
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 18.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 18.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 19. MS-19: Integrated Strategy Dashboard

### 19.1 목적

candidate, scoring, explanation, paper trading, backtest/performance를 하나의 local dashboard로 통합한다.

### 19.2 왜 이 단계가 필요한가

개별 기능을 실제 사용 가능한 local dashboard 흐름으로 묶어야 하기 때문이다.

### 19.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 19.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 19.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 19.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 19.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 19.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-19.*.md
```

### 19.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-19.01 | dashboard information architecture | 통합 화면 구조를 설계한다. |
| MS-19.02 | candidate list + score + risk panel | 후보/점수/리스크 패널을 통합한다. |
| MS-19.03 | paper portfolio panel | paper portfolio panel을 통합한다. |
| MS-19.04 | backtest/performance panel | 성과 패널을 통합한다. |
| MS-19.05 | recommendation explanation panel v2 | 설명 패널 v2를 구성한다. |
| MS-19.06 | AppTest smoke | 통합 dashboard AppTest를 수행한다. |
| MS-19.07 | server smoke | 통합 dashboard server smoke를 수행한다. |
| MS-19.08 | final checkpoint | MS-19 완료 범위를 문서화한다. |

### 19.10 하위 Micro Stage 상세

#### MS-19.01 dashboard information architecture

- 목적: 통합 화면 구조를 설계한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.02 candidate list + score + risk panel

- 목적: 후보/점수/리스크 패널을 통합한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.03 paper portfolio panel

- 목적: paper portfolio panel을 통합한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.04 backtest/performance panel

- 목적: 성과 패널을 통합한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.05 recommendation explanation panel v2

- 목적: 설명 패널 v2를 구성한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.06 AppTest smoke

- 목적: 통합 dashboard AppTest를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.07 server smoke

- 목적: 통합 dashboard server smoke를 수행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-19.08 final checkpoint

- 목적: MS-19 완료 범위를 문서화한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 19.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 19.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 19.13 필요한 credential 여부

- OpenAI API KEY: 조건부
- Toss API KEY / SECRET KEY: 조건부
- accountSeq: 불필요

### 19.14 DB write 허용 여부

- dashboard 자체는 read-only

### 19.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 19.16 OpenAI/LLM 사용 여부

- 불사용

### 19.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 금지
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 19.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 19.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태


## 20. MS-20: Final Local MVP Release

### 20.1 목적

local-only MVP의 safety/credential/DB/test/runbook/release checkpoint를 완료한다.

### 20.2 왜 이 단계가 필요한가

릴리스 가능한 로컬 MVP 상태를 검증하고 사용 문서를 완성해야 하기 때문이다.

### 20.3 선행 조건

- 이전 MS final checkpoint 완료
- `origin/main` clean 상태
- `.env.local`, `data/`, SQLite DB 파일 Git 미추적 유지
- 실제 주문/계좌/accountSeq 경계 유지
- credential은 필요한 하위 stage 전까지 요청하지 않음

### 20.4 입력

- 이전 MS의 안전한 output
- local-only 또는 read-only로 준비된 summary/model/result
- raw credential, raw token, raw response body, raw DB row는 입력으로 사용하지 않음

### 20.5 출력

- stage 목적에 맞는 model/contract/UI/report
- 검증 결과
- final checkpoint report
- 다음 stage로 넘길 sanitized output

### 20.6 허용 범위

- local-only 처리
- deterministic validation
- 문서/테스트/보고서
- 해당 stage에서 명시 허용된 코드 또는 UI 변경
- 필요한 경우에만 별도 승인된 local DB write 또는 read-only API smoke

### 20.7 금지 범위

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 조회
- accountSeq 사용
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- 승인 전 외부 API/LLM 호출

### 20.8 생성/수정 예상 파일

```text
src/ai_stock/...        # 해당 stage에서 명시 허용된 경우만
app/streamlit_app.py    # UI integration stage에서만
tests/test_*.py         # 검증 stage에서만
docs/19_DETAILED_MICRO_WBS.md
references/endpoint_matrix.md
reports/MS-20.*.md
```

### 20.9 하위 Micro Stage 목록

| Micro Stage | 이름 | 목적 |
|---|---|---|
| MS-20.01 | full safety audit | 전체 안전 정책을 점검한다. |
| MS-20.02 | credential audit | credential 노출/사용 시점을 점검한다. |
| MS-20.03 | DB/file tracking audit | DB/data/.env Git 추적을 점검한다. |
| MS-20.04 | full test suite | full test suite를 실행한다. |
| MS-20.05 | local runbook | local 실행 runbook을 작성한다. |
| MS-20.06 | troubleshooting guide | 문제 해결 문서를 작성한다. |
| MS-20.07 | final release checkpoint | final local MVP checkpoint를 작성한다. |

### 20.10 하위 Micro Stage 상세

#### MS-20.01 full safety audit

- 목적: 전체 안전 정책을 점검한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-20.02 credential audit

- 목적: credential 노출/사용 시점을 점검한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-20.03 DB/file tracking audit

- 목적: DB/data/.env Git 추적을 점검한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-20.04 full test suite

- 목적: full test suite를 실행한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-20.05 local runbook

- 목적: local 실행 runbook을 작성한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-20.06 troubleshooting guide

- 목적: 문제 해결 문서를 작성한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

#### MS-20.07 final release checkpoint

- 목적: final local MVP checkpoint를 작성한다.
- 산출물: contract/code/test/report 중 해당 stage 범위에 맞는 최소 산출물
- 검증: no credential, no real order, no raw secret, deterministic/local-only 원칙 확인

### 20.11 검증 기준

- `python -m compileall -q src tests app` PASS
- `python -m unittest discover -s tests` PASS
- `python -m pytest` PASS
- `python scripts/dev_check.py` PASS
- `ruff check src tests app` PASS
- `git diff --check` PASS
- stage별 forbidden pattern scan PASS
- DB/data/.env Git 미추적 확인

### 20.12 완료 기준

- 모든 하위 Micro Stage 완료
- AppTest/server smoke가 필요한 경우 완료
- final checkpoint report 작성
- 안전 정책 및 미지원 범위 명시
- main fast-forward merge 완료

### 20.13 필요한 credential 여부

- OpenAI API KEY: 새 key 불필요
- Toss API KEY / SECRET KEY: 새 key 불필요
- accountSeq: 불필요

### 20.14 DB write 허용 여부

- audit 외 불필요

### 20.15 Toss API 사용 여부

- 불사용 또는 preflight 문서화만

### 20.16 OpenAI/LLM 사용 여부

- 불사용

### 20.17 주문/계좌/자산/잔고/체결 사용 여부

- 실제 주문 가능 여부: 금지
- 주문/계좌/자산/잔고/체결 API는 MVP 범위에서 금지

### 20.18 실패 시 중단 조건

- credential 또는 token 원문 출력
- accountSeq 도입
- 실제 주문/계좌 endpoint 도입
- 실주문 버튼 추가
- raw response/raw DB row 출력
- DB 파일 Git 추적
- 승인 없는 API/LLM 호출

### 20.19 다음 단계로 넘어가기 위한 조건

- stage final checkpoint 완료
- working tree clean
- origin/main fast-forward 반영
- 다음 stage preflight 작성 가능 상태

---

## 17. 단계별 credential 필요 시점

| Stage | OpenAI API KEY | Toss API KEY / SECRET KEY | accountSeq | DB write | 실제 주문 | 비고 |
|---|---|---|---|---|---|---|
| MS-09 | 불필요 | 불필요 | 불필요 | 원칙 불허 | 없음 | Candidate / Watchlist Foundation |
| MS-10 | 불필요 | 불필요 | 불필요 | 불허 | 없음 | Feature & Data Quality Model |
| MS-11 | 불필요 | 불필요 | 불필요 | 불허 | 없음 | Deterministic Scoring Model |
| MS-12 | 불필요 | 불필요 | 불필요 | 불허 | 없음 | Recommendation List UI |
| MS-13 | 불필요 | 불필요 | 불필요 | 불허 | 없음 | Toss Read-only API Preflight |
| MS-14 | 불필요 | MS-14.02부터 필요 가능 | 불필요 | 원칙 불허 | 없음 | Toss Read-only Market Data Integration |
| MS-15 | 불필요 | 필요 가능 | 불필요 | local snapshot 한정 허용 | 없음 | Local Snapshot Refresh Pipeline |
| MS-16 | 불필요 | 불필요 | 불필요 | paper ledger 한정 허용 | 금지 | Paper Trading Engine |
| MS-17 | 불필요 | 불필요 | 불필요 | backtest result 한정 가능 | 금지 | Backtest & Performance Review |
| MS-18 | MS-18.06부터 필요 가능 | 불필요 | 불필요 | 원칙 불허 | 금지 | Optional LLM / AI Reasoning Layer |
| MS-19 | 조건부 | 조건부 | 불필요 | dashboard 자체는 read-only | 금지 | Integrated Strategy Dashboard |
| MS-20 | 새 key 불필요 | 새 key 불필요 | 불필요 | audit 외 불필요 | 금지 | Final Local MVP Release |


핵심 결론:

```text
MS-09~MS-13: OpenAI/Toss credential 불필요
MS-14.02 이후: Toss read-only token issue smoke에서 Toss API KEY / SECRET KEY 필요 가능
MS-18.06 이후: OpenAI live smoke에서 OpenAI API KEY 필요 가능
accountSeq: local MVP 범위에서 계속 불필요
실제 주문: local MVP 범위에서 계속 금지
```

---

## 18. 단계별 DB write 허용 시점

- MS-09~MS-14: 원칙적으로 DB write 불허
- MS-15: local snapshot refresh에 한정해 허용
- MS-16: paper ledger에 한정해 허용
- MS-17: backtest result에 한정해 조건부 허용
- MS-18: LLM output cache는 별도 preflight 없이는 불허
- MS-19: dashboard 자체는 read-only
- MS-20: audit/report 중심

---

## 19. 단계별 금지 정책 요약

항상 금지:

- 실제 매수/매도/보유 지시
- 실주문 버튼
- 실제 주문 API
- 실제 계좌/자산/잔고/체결 API
- accountSeq
- raw Access Token 출력
- raw Authorization Bearer 출력
- raw credential 출력
- raw API response 전문 저장
- raw DB row 전문 출력
- `.env.local` 내용 출력
- DB 파일 Git 추적
- `data/` 디렉터리 Git 추적

---

## 20. 권장 진행 순서

```text
MS-09 → MS-10 → MS-11 → MS-12 → MS-13 → MS-14 → MS-15 → MS-16 → MS-17 → MS-18 → MS-19 → MS-20
```

바로 다음 실행 후보:

```text
MS-09.01 candidate input contract preflight
```

---

## 21. Known Risks

### Recommendation wording risk

UI 또는 LLM이 실제 추천처럼 보이는 문구를 만들 수 있다. forbidden recommendation language validation과 observation-only disclaimer를 유지한다.

### Credential leak risk

Toss key/secret, OpenAI key, Access Token, Authorization Bearer가 로그나 report에 남을 수 있다. 필요 시점 전 credential 요청을 금지하고 staged diff scan을 수행한다.

### DB tracking risk

`data/` 또는 SQLite DB가 Git에 추적될 수 있다. `git ls-files -- data`, `git check-ignore -v data/local/ai_stock.sqlite3`를 반복 확인한다.

### Real order boundary risk

paper trading과 real order가 혼동될 수 있다. simulated/local-only 문구를 강제하고 accountSeq 및 real order endpoint를 금지한다.

### LLM hallucination risk

LLM이 과도한 확신이나 투자 지시를 생성할 수 있다. LLM은 설명 보조로만 제한하고 sanitizer/validation을 둔다.

---

## 22. 운영 원칙

- Local-only first
- Read-only before write
- Credential last
- No real trading in MVP
- Paper trading is simulated only
- Dashboard must not be an execution surface
- Every risky expansion needs preflight

---

## 23. Stage Naming Convention

브랜치명 예시:

```text
codex/pm/MS-09.01-candidate-input-contract-preflight
codex/ai/MS-10.02-price-summary-feature
codex/ui/MS-12.02-candidate-table-ui
codex/api/MS-14.03-market-data-readonly-smoke
codex/storage/MS-15.03-idempotent-local-db-write
codex/trading/MS-16.04-simulated-order-model
```

커밋 메시지 예시:

```text
docs(project): MS-09.00 add next roadmap MS09-MS20
feat(ai): MS-09.01 add candidate input contract preflight
feat(ai): MS-10.02 add price summary feature
feat(ui): MS-12.02 add candidate table UI
feat(api): MS-14.03 add market data read-only smoke
feat(storage): MS-15.03 add idempotent local snapshot write
feat(trading): MS-16.04 add simulated order model
```

---

## 24. Commit / Push / Merge 정책

기본 흐름:

```text
1. main 최신 확인
2. 새 stage branch 생성
3. 구현/문서화
4. 검증
5. 사용자에게 보고
6. 사용자 승인 후 commit
7. 사용자 승인 후 push
8. 사용자 승인 후 main fast-forward merge
```

금지:

- 승인 없는 commit
- 승인 없는 push
- 승인 없는 merge
- merge commit
- force push
- reset --hard
- credential commit
- DB file commit
- `.env.local` commit

병합 방식:

```text
git merge --ff-only <stage-branch>
```

---

## 25. 최종 결론

MS-09~MS-20은 `ai_stock` 프로젝트를 local-only MVP로 완성하기 위한 장기 계획이다.

가장 중요한 진행 방향은 다음이다.

```text
후보군 → feature → deterministic scoring → list UI → Toss read-only → local refresh → paper trading → backtest → optional LLM → integrated dashboard → final release
```

다음 즉시 실행 후보는 다음이다.

```text
MS-09.01 candidate input contract preflight
```

이 단계까지는 OpenAI API KEY, Toss API KEY, Toss SECRET KEY, accountSeq가 모두 불필요하다.
