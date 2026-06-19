# 16. Future Roadmap

## v0.1 — 현재 목표

- read-only API 연동
- AI 추천 설명
- 모의투자
- Streamlit UI
- 테스트/로그/리포트
- 실주문 차단

## v0.2 — 고급 모의투자

- 전략별 백테스트
- 종목군 비교
- 리밸런싱 시뮬레이션
- 포트폴리오 VaR/변동성
- 거래 비용 모델 개선
- CSV export

## v0.3 — 운영 안정화

- FastAPI backend 분리
- 스케줄러 추가
- 알림 기능
- DB migration
- Docker packaging
- CI workflow

## v0.4 — 실주문 준비 단계

실주문은 아직 활성화하지 않고 다음을 준비한다.

- 주문 preview
- 주문 검증 checklist
- 수동 승인 workflow
- kill switch
- duplicate order guard
- 일일 주문 제한
- 실주문 dry-run 리포트

## v1.0 — 실주문 가능 여부 검토

다음 조건이 충족될 때만 검토한다.

- 약관/규정 검토 완료
- paper trading 성과와 리스크 검증 완료
- 장애 대응 절차 수립
- 수동 승인 UX 완성
- 소액 테스트 계획 수립
- 사용자가 명시적으로 책임을 인지
