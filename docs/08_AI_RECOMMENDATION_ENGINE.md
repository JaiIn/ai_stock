# 08. AI 추천 엔진 설계

## 1. 핵심 원칙

AI는 매매 명령자가 아니라 **설명 생성기와 보조 분석기**다. 최종 등급과 점수는 deterministic rule-based scoring이 만든다.

## 2. 입력 데이터

```json
{
  "symbol": "005930",
  "name": "삼성전자",
  "marketCountry": "KR",
  "currency": "KRW",
  "lastPrice": "72000",
  "indicators": {
    "return_1d": "0.012",
    "ma5_gap": "0.018",
    "ma20_gap": "0.042",
    "volatility_20d": "0.021",
    "volume_change": "1.34"
  },
  "warnings": [],
  "position": {
    "quantity": "0",
    "averagePurchasePrice": null
  }
}
```

## 3. Rule-based score

예시:

```text
score = 50
+ trend_score       # -20 ~ +20
+ momentum_score    # -15 ~ +15
+ volume_score      # -10 ~ +10
- volatility_penalty # 0 ~ 20
- warning_penalty    # 0 ~ 50
- concentration_penalty # 0 ~ 15
```

## 4. 등급 산출

| 조건 | 등급 |
|---|---|
| warning severe | `BLOCKED` |
| score >= 75 and risk <= 40 | `BUY_CANDIDATE` |
| current holding and score >= 55 | `HOLD` |
| current holding and score < 45 | `REDUCE` |
| otherwise | `WATCH` |

## 5. Warning penalty

| Warning | 정책 |
|---|---|
| `LIQUIDATION_TRADING` | `BLOCKED` |
| `INVESTMENT_RISK` | `BLOCKED` |
| `INVESTMENT_WARNING` | 강한 감점 또는 BLOCKED |
| `OVERHEATED` | 감점 |
| `VI_STATIC`, `VI_DYNAMIC` | 단기 리스크 감점 |
| `STOCK_WARRANTS` | 감점/주의 |

## 6. LLM Prompt 원칙

### system message

```text
너는 개인 투자자의 모의투자 분석 보조자다.
확정 수익, 원금 보장, 단정적 매수 지시를 하지 않는다.
제공된 수치와 규칙 기반 점수만 근거로 설명한다.
실제 주문을 권유하지 않는다.
```

### user message

```text
아래 JSON 데이터를 기반으로 추천 등급의 이유를 한국어로 설명해라.
반드시 다음 형식을 지켜라.
1. 요약
2. 긍정 요인
3. 위험 요인
4. 모의투자에서 확인할 점
5. 면책 문구
```

## 7. AI 출력 Guardrail

금지 표현:

- 반드시 오른다
- 무조건 매수
- 수익 보장
- 안전한 종목
- 손실 없음
- 지금 사라
- 몰빵

검출 시:

- AI 응답 폐기
- fallback 템플릿 사용
- `logs/ai.log`에 guardrail violation 기록

## 8. Fallback Explanation

LLM API가 실패하면 다음 템플릿을 사용한다.

```text
{symbol}은 현재 규칙 기반 점수 {score}점으로 {rating} 등급입니다.
주요 긍정 요인은 {positive_reasons}입니다.
주요 위험 요인은 {risk_reasons}입니다.
이 결과는 모의투자 검증용 분석이며 실제 투자 판단은 사용자가 별도로 해야 합니다.
```
