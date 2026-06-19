# 24. 프론트엔드 프레임워크 검토 및 결정

작성일: 2026-06-19  
적용 범위: v0.1 로컬 전용 UI

---

## 1. 결론

v0.1 기본 프론트엔드는 **Streamlit**을 유지한다.

단, 다음 조건을 반드시 지킨다.

```text
Streamlit = UI 렌더링 전용
핵심 로직 = src/ai_stock/ 백엔드 패키지
```

즉, Streamlit을 쓰더라도 백엔드/프론트 역할은 분리한다.

---

## 2. 왜 Streamlit을 v0.1 기본으로 유지하는가

이 프로젝트는 다음 조건을 가진다.

- 배포하지 않음
- 로컬 PC에서만 실행
- 사용자는 빠른 개발과 바이브코딩을 원함
- 주식 데이터 표, 차트, 추천 결과, 로그, 설정 화면이 필요
- 복잡한 사용자 인증/권한/다중 사용자 기능이 없음
- 초반에는 UI 완성도보다 기능 검증이 중요

따라서 v0.1에서는 Streamlit이 가장 현실적이다.

장점:

- Python만으로 빠르게 UI 구현 가능
- 데이터프레임, 차트, 탭, 사이드바 구현이 쉬움
- 로컬 실행이 간단함
- Codex가 구현하기 쉬움
- 백엔드 서비스 호출용 UI shell로 적합

주의점:

- Streamlit의 rerun 모델 때문에 복잡한 상태 관리가 어려울 수 있음
- 프론트/백엔드 경계가 흐려지기 쉬움
- 파일 하나에 로직이 몰릴 위험이 있음
- 아주 복잡한 앱형 UI에는 한계가 있음

보완책:

- `app/streamlit_app.py`는 화면 조립만 담당
- 각 페이지는 service layer만 호출
- 모든 핵심 로직은 `src/ai_stock/`에 위치
- UI state는 최소화
- 화면별 adapter/view_model 계층 사용

---

## 3. 후보 비교

| 후보 | 장점 | 단점 | v0.1 판단 |
|---|---|---|---|
| Streamlit | 가장 빠름, 데이터 앱 적합, 로컬 실행 쉬움 | 복잡한 상태/레이아웃 한계 | 기본 채택 |
| NiceGUI | Python 기반 브라우저 UI, 이벤트형 앱에 적합 | Streamlit보다 학습/구조 설계 필요 | v0.2 대안 |
| Gradio | AI/ML 데모와 챗 UI에 강함 | 트레이딩 대시보드/복잡한 화면에는 덜 적합 | 보조/실험 후보 |
| Dash | Plotly 기반 분석 대시보드에 강함 | callback 구조가 초보자에게 부담 | 차트 중심이면 후보 |
| Panel | PyData 대시보드와 복잡한 분석 UI에 적합 | 생태계/학습 부담 | 데이터 분석 고도화 후보 |
| Reflex | Python full-stack 앱 구조 가능 | 프로젝트 복잡도 증가 | v0.2+ 검토 |
| React + FastAPI | 역할 분리 가장 명확 | 프론트 지식/빌드 복잡도 증가 | 지금은 과함 |

---

## 4. Streamlit을 사용할 때의 역할 분리 규칙

### 4.1 허용되는 Streamlit 코드

```python
import streamlit as st

from ai_stock.services.recommendation_service import RecommendationService
from ai_stock.services.paper_trading_service import PaperTradingService

st.title("AI 추천/모의투자")

if st.button("추천 실행"):
    result = recommendation_service.run_recommendation(...)
    st.dataframe(result.to_dataframe())
```

---

### 4.2 금지되는 Streamlit 코드

```python
# 금지: UI에서 직접 HTTP 호출
response = httpx.get("https://...toss...")

# 금지: UI에서 직접 SQL 실행
conn.execute("select * from paper_order")

# 금지: UI에서 추천 점수 직접 계산
score = price_momentum * 0.7 + volume_score * 0.3

# 금지: UI에서 실주문 safety gate 우회
create_order(...)
```

---

## 5. 권장 UI 구조

```text
app/
├── streamlit_app.py
├── pages/
│   ├── 01_dashboard.py
│   ├── 02_watchlist.py
│   ├── 03_recommendations.py
│   ├── 04_market_data.py
│   ├── 05_paper_trading.py
│   ├── 06_account_snapshot.py
│   ├── 07_logs_and_reports.py
│   └── 08_settings.py
└── ui_components/
    ├── tables.py
    ├── charts.py
    ├── forms.py
    ├── alerts.py
    └── layout.py
```

주의:

- `app/pages/*`는 service 호출만 한다.
- `app/ui_components/*`는 display/helper만 담당한다.
- business logic은 `src/ai_stock/`에 둔다.

---

## 6. 프론트엔드 변경 조건

다음 중 2개 이상이 발생하면 Streamlit 유지 여부를 재검토한다.

- 화면 상태가 복잡해져 session_state 관리가 어려움
- 실시간 차트/이벤트 업데이트가 많아짐
- UI/UX를 앱처럼 세밀하게 제어해야 함
- 백엔드와 프론트 프로세스 분리가 필수가 됨
- 멀티 페이지 간 상태 공유가 복잡해짐
- Streamlit rerun 때문에 성능/사용성이 크게 저하됨

---

## 7. 대안별 전환 기준

### 7.1 NiceGUI로 전환

추천 상황:

- 로컬 브라우저 앱을 유지하면서 UI 이벤트 제어를 더 잘하고 싶음
- Streamlit rerun 모델이 불편함
- Python 기반 개발을 유지하고 싶음

전환 난이도:

```text
중간
```

---

### 7.2 Dash로 전환

추천 상황:

- Plotly 차트 중심의 분석 대시보드가 핵심
- 사용자 입력보다 데이터 시각화가 더 중요

전환 난이도:

```text
중간
```

---

### 7.3 Gradio로 전환

추천 상황:

- AI 추천 대화형 인터페이스가 핵심
- 챗봇/설명 생성/모델 실험 화면이 중심

전환 난이도:

```text
낮음~중간
```

---

### 7.4 React + FastAPI로 전환

추천 상황:

- 프론트/백엔드 역할을 완전히 분리해야 함
- UI 품질과 상태 관리가 매우 중요
- 장기적으로 앱을 크게 키울 계획이 있음

전환 난이도:

```text
높음
```

v0.1에서는 권장하지 않는다.

---

## 8. 최종 결정

```text
v0.1 Frontend: Streamlit
v0.1 Backend: Python package service layer
v0.1 API Server: 없음
v0.1 DB: SQLite
v0.1 실행: localhost only
```

Codex는 이 결정을 임의로 바꾸지 않는다.

변경이 필요하면 `reports/decision-records/`에 ADR을 작성하고 사용자 승인을 기다린다.
