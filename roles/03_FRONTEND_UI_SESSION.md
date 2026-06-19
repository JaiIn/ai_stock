# Session F — Frontend/UI 역할 지침

## 1. 책임

- Streamlit UI 구현
- 화면 구조, 탭, 페이지, 컴포넌트 작성
- 사용자 입력 폼 작성
- 서비스 호출 결과 표시
- 로컬 실행 UX 개선

## 2. 수정 가능 영역

```text
app/
app/pages/
app/ui_components/
tests/ui/
```

## 3. 수정 금지 영역

```text
src/ai_stock/toss_api/
src/ai_stock/repositories/
src/ai_stock/recommendation/
src/ai_stock/paper_trading/
src/ai_stock/risk/
```

## 4. 핵심 규칙

- UI는 service layer만 호출한다.
- UI에서 Toss API를 직접 호출하지 않는다.
- UI에서 SQLite에 직접 접근하지 않는다.
- UI에서 추천 점수 계산을 직접 하지 않는다.
- UI에서 모의체결 로직을 직접 하지 않는다.
- UI에서 실주문 버튼을 만들지 않는다.

## 5. v0.1 UI 페이지 후보

```text
01_dashboard.py
02_watchlist.py
03_recommendations.py
04_market_data.py
05_paper_trading.py
06_account_snapshot.py
07_logs_and_reports.py
08_settings.py
```

## 6. 서비스가 아직 없을 때

백엔드 서비스가 아직 구현되지 않았다면 직접 구현하지 말고 다음 중 하나를 선택한다.

1. mock adapter를 UI 내부가 아닌 `app/mock_view_models.py`에 둔다.
2. 필요한 service interface를 handoff 문서로 Backend 세션에 요청한다.

## 7. 완료 기준

- UI smoke check 완료
- backend logic 직접 구현 없음
- 외부 host 바인딩 없음
- 변경 화면 스크린샷 또는 설명 리포트 작성

## 8. 종료 문구

```text
현재 Frontend/UI Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
