# Session C — Data/DB 역할 지침

## 1. 책임

- SQLite schema 설계
- SQLAlchemy model 구현
- Repository 구현
- DB 초기화 스크립트
- DB 관련 테스트

## 2. 수정 가능 영역

```text
src/ai_stock/repositories/
src/ai_stock/domain/entities.py
src/ai_stock/domain/db_models.py
scripts/init_db.py
tests/unit/test_repository*.py
tests/integration/test_db*.py
```

## 3. 수정 금지 영역

```text
app/
src/ai_stock/toss_api/
src/ai_stock/recommendation/
src/ai_stock/paper_trading/
```

## 4. 중단 조건

- 기존 DB 삭제 필요
- schema 변경으로 데이터 손실 가능
- migration 도입 필요
- PostgreSQL 등 외부 DB 도입 제안

## 5. 완료 기준

- SQLite 로컬 DB 생성 확인
- repository unit test 통과
- 데이터 손실 가능성 없음
- schema 변경 내용 문서화

## 6. 종료 문구

```text
현재 Data/DB Micro Stage가 종료되었습니다. 다음 명령을 기다립니다.
```
