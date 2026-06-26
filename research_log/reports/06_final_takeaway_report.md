# 06_final_takeaway_report.md
## Final Takeaway — Language–Performance Wedge, Instability as Finding *(first-draft narrative)*

> **⚠ 본 문서의 위치 (2026 refinement cycle 이후 추가됨)**
>
> 본 문서는 본 연구의 **first-draft final narrative** 이다. 이후 추가 robustness 분석 — *orthogonalization · joint regression · 2024 cross-section E-G asymmetry* — 가 시행되었고, 그 결과 cheap-talk framing 의 *evidence 강도* 가 refinement 되었다.
>
> 본 문서는 narrative refinement 의 *evolution* 을 보여주는 historical record 로 *그대로 보존* 된다. **canonical final narrative 는 `08_revised_final_report.md`** 에 있다.
>
> 두 문서의 관계:
> - 06 (본 문서) = cheap-talk 가설과의 "정합" 을 main framing 으로 정리한 시점
> - 08 = "정합" 의 강도가 *feature construction 결정에 종속* 됨을 정직하게 재조정한 refined narrative
>
> 본 문서의 §1 ~ §10 은 변경 없이 보존된다. 단, 다음 두 문장은 06 → 08 narrative 진화에서 *refinement 대상* 임을 미리 밝힌다.
> - "4개 alpha 가 모두 cheap-talk 가설과 정합하는 방향을 가리킨다" (§4)
> - "verbosity 통제 후에도 약한 음의 잔여가 남는다" (§2.3)
>
> 두 문장 모두 본 문서 시점에서는 *valid finding* 이었고, 08 에서는 *조건부 finding* 으로 강도가 조정된다.

---

> **본 연구가 답한 질문**
> 한국 사업보고서의 ESG 관련 공시 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가? 그리고 그 연관은 *어떤 측정 가정* 위에서 성립하는가?
>
> **본 연구가 *답하지 않은* 질문**
> ESG 언어가 ESG 성과를 *예측*하는가? 어느 firm이 *실제로* cheap-talk을 하는가? — 이 두 질문은 본 연구의 데이터·방법으로 답할 수 없다.

---

## 1. 본 연구의 framing — 다시 한 번

본 파이프라인은 일반적인 ESG NLP 연구와 다음 한 줄에서 갈라진다.

> *더 좋은 ESG predictor* 를 만드는 연구가 아니다.
>
> *ESG disclosure language measurement 자체가 preprocessing · verbosity · dictionary choice 에 매우 민감*하다는 점, 그리고 *그 instability 자체가 cheap-talk 가능성을 empirical 하게 드러낸다*는 점 — 이 두 사실을 보이는 연구다.

이 framing 은 본 보고서 전체에서 한 번도 흔들리지 않는다. 모든 결과는 다음 세 어휘 안에서 해석된다.

| 허용 | 금지 |
|---|---|
| associated with · related to · consistent with | causes · predicts · improves |
| disclosure intensity | true ESG · ESG performance measurement |
| weak / unstable / preprocessing-sensitive | classifies · scores ESG |

---

## 2. 핵심 발견 — 네 layer의 instability

본 통합 파이프라인은 같은 corpus 위에서 네 가지 다른 layer 에서 ESG disclosure language signal 의 *불안정성* 을 정량적으로 드러낸다.

### 2.1 Layer 1 — Preprocessing sensitivity

같은 corpus 에서 토큰화 옵션 (exp_B / exp_E / exp_F) 만 바꿔도 feature 분포·ρ 부호가 변동한다. 본 표본에서 그 변동의 폭은 |Δρ| ≤ 0.05 정도로 제한되지만, *어떤 feature 는 0 을 가로지를 수 있다*.

> *"전처리 강도를 한 단계 바꾸면 어떤 신호는 사라지고 어떤 신호는 유지된다."*

### 2.2 Layer 2 — Tokenizer instability

Kiwi 와 Okt 같은 다른 한국어 형태소 분석기를 교체하면 ESG-relevant vocabulary 의 일부가 *분리되거나 결합* 되어 다른 token 으로 등장한다. 본 파이프라인은 Kiwi 와 사용자 사전을 canonical 로 두지만, 그 선택 자체가 결과의 한 *가정* 이다.

> *"분석자가 분석기를 바꾸면 같은 문장에서 다른 ESG 토큰이 나온다."*

### 2.3 Layer 3 — Verbosity dominance

`g_signal_ratio` 가 KCGS 등급과 가진 univariate 음의 연관 중 *상당 부분이 분량 (log_tokens)으로 흡수* 된다. 동시에 `log_tokens` 자체는 KCGS 와 가장 강한 (양의) ρ 를 갖는다.

> *"높은 등급 firm 일수록 보고서가 더 길다. 그리고 그 길이가 ratio 신호의 상당 부분을 설명한다."*

### 2.4 Layer 4 — Sign reversal (N=30 → N=210)

소표본 (N ≈ 30) 에서 양의 ρ로 보였던 신호가 N=210 으로 확장하면 *음으로 뒤집힌다*. sub-sampling 1,000회 재현 결과, 작은 표본에서 양의 ρ 가 *우연히 발생할 확률이 무시할 수 없는 수준* 이다.

> *"직관적으로 좋아 보였던 pilot 결과가 표본을 늘리자 반대 방향으로 갔다."*

### 2.5 네 layer 의 의미

이 네 layer 는 *우연히 한 분석에서 한 번* 관찰된 것이 아니다. **동일 corpus 위에서 robustness 실험으로 재현 가능한 패턴** 이다. 그리고 네 layer 가 *서로 보강* 한다 — preprocessing 을 다르게 해도, tokenizer 를 다르게 해도, 표본을 다르게 잡아도, 분량을 통제해도 — *어떤 결정이든 결과의 일부를 흔든다*.

---

## 3. Instability 가 왜 *finding* 인가

> 같은 데이터, 같은 질문에서도 분석자의 선택이 결론을 흔든다.

본 보고서는 이 흔들림을 *분석 실패* 로 부르지 않는다. 다음과 같은 의미에서 *measurement evidence* 로 해석한다.

### 3.1 만약 ESG 언어가 ESG 성과를 직접 반영한다면

이 가설이 참이라면, 전처리 강도를 한 단계 바꾸거나 표본을 다르게 잡았을 때 ρ 부호가 흔들려서는 안 된다. *진짜 신호* 는 측정 가정에 부분적으로 강건해야 한다.

### 3.2 본 표본의 관찰

- ρ 의 *방향* 은 preprocessing 안에서는 어느 정도 유지되지만 — *표본 크기를 바꾸면 부호가 뒤집힌다*
- ρ 의 *크기* 는 약하다 (|ρ| ≈ 0.10 – 0.20)
- 분량을 통제하면 ratio 신호가 *상당 부분 사라진다*

### 3.3 이 흔들림이 *공시 언어의 본질* 을 드러내는 방식

ESG 공시는 *strategic communication* 행위다. 기업은:

1. KCGS 등급을 *알고 있고*,
2. 자신의 공시 문구를 *수정할 수 있는* 행위자이며,
3. 외부 평가에 *대응하는 incentive* 가 있다.

이 세 조건이 합쳐지면 ESG 어휘 사용은 *실질 성과의 결과* 가 아니라 *외부 평가에 대한 전략적 응답* 일 수 있다. 그리고 그 전략적 응답이 *분석자의 측정 결정에 종속* 된다는 것 — 이것이 본 연구의 가장 honest 한 finding 이다.

> *"측정 도구의 결함이 아니라, 측정 대상의 본질적 특성이다."*

---

## 4. Cheap-Talk implication — 4개 alpha 통합

본 연구의 4개 alpha 는 모두 *cheap-talk 가설과 정합하는* 방향을 가리킨다.

| Alpha | 결과 | cheap-talk 정합 |
|---|---|---|
| **1** | 분량 통제 후에도 음의 잔여 (verbosity-adjusted score r_i) | 분량이 *유일한 원인* 은 아님 |
| **2** | 저등급 firm 이 G 어휘를 더 많이 사용 (약 단조) | "성과가 낮을수록 언어로 보완" 패턴 |
| **3** | 소표본 양의 상관은 표본 bias 의 인공물 (sub-sampling 재현) | 표본 확장 시 cheap-talk 정합 방향 안정 |
| **4** | 거버넌스 어휘 최다 사용 firm 이 낮은 등급 영역에 몰림 | 의례적 공시 영역에서 cheap-talk 가장 강함 |

### 4.1 본 보고서가 *주장하지 않는 것*

- 어느 firm 이 *실제로* cheap-talk 을 했다고 말하지 않는다.
- ESG 언어 ↔ ESG 성과의 *인과 관계* 를 주장하지 않는다.
- 한 alpha 의 결과만으로 결론짓지 않는다.
- 본 표본 (KOSPI N=210) 의 결과를 KOSDAQ·다른 시장에 *일반화* 하지 않는다.

### 4.2 본 보고서가 *주장하는 것*

> *Cheap-talk 가설과 정합하는 패턴이 본 corpus 안에서 4개의 다른 측정 각도로 동시에 관찰된다.*

이 주장의 강도는 *증명 (proof)* 이 아니라 *정합 (consistency)* 이다.

---

## 5. 본 연구의 contribution — 다시 한 번

| 구분 | 일반적 ESG NLP 연구 | 본 연구 |
|---|---|---|
| 목적 | 더 좋은 ESG predictor | ESG language measurement 자체의 fragility 정량화 |
| 모형 평가 | R² · accuracy · F1 | 부호 안정성 · preprocessing robustness · 표본 sensitivity |
| sign reversal | 잡음 / 이상치로 처리 | empirical finding 으로 격상 |
| instability | 결함 (제거 대상) | 결과의 일부 (해석 대상) |
| disclosure framing | "ESG 신호 추출" | "ESG language ≠ ESG performance" |

> 본 연구의 contribution 은 *결과의 강도* 가 아니라 *결과의 honest 한 해석 방식* 에 있다.

---

## 6. 한계 (honest)

| 한계 | 의미 |
|---|---|
| **인과 추론 불가** | OLS · Ordered Logit · Binary Logit 모두 association 만 |
| **KCGS validity 한계** | 외부 평가의 방법론이 공개되지 않음 → KCGS 자체의 measurement error 가 잠재 noise |
| **표본 편향** | KOSPI 중심, N=210, FY 2021–2023 — 표본 외 일반화 어려움 |
| **D · C 군 표본 부족** | 등급 분포 좌측 tail 의 평균이 단일 firm-year 에 흔들림 |
| **Expanded dictionary 미통합** | manual_v1 (7 단어) 이 final 파이프라인의 N=210 에 정식 반영되지 않음 — *honest gap* |
| **θ 정량 비교 미수행** | fastText 확장 모델이 final 코드베이스에 없음 — *honest gap* |
| **Preprocessing 의존성** | 결과가 exp_B / exp_E / exp_F 간에 부분 변동 — 본 연구의 주제이기도 함 |
| **firm 고정효과 미통제** | 산업·연도 FE 만 — within-firm 변동 정보 미활용 |
| **multiple testing 우려** | 4개 alpha 를 동시에 본 후 selection bias 가 없도록 *모두 보고* — 그러나 사전 등록 (pre-registration) 부재 |

이 한계를 *숨기지 않는 것* 이 본 연구 framing 의 일관성이다. *Instability 를 finding 으로 본다면, 자신의 분석이 가진 fragility 도 동등하게 기록해야 한다.*

---

## 7. Future work

| 방향 | 무엇을 검증하는가 |
|---|---|
| **Expanded dictionary 정식 통합** | manual_v1 후속 cycle 에서 `features_expanded_exp_F.parquet` 생성. θ ∈ {0.5, 0.6, 0.7} 정량 비교 표 완성. §3·§5·§6 재검증 |
| **섹션별 cheap-talk 분리 분석** | II / IV / VI 별로 동일 회귀를 돌려 *거버넌스 cheap-talk 이 VI 섹션에 집중* 되는지 검증 |
| **시계열 within-firm 분석** | 동일 firm 의 연도별 disclosure 변화와 등급 변화의 시차 연관성 — Granger-style 진단 |
| **표본 확장 (KOSDAQ)** | KOSDAQ 포함 시 cheap-talk 패턴의 robustness 재검증 — 시장 segmentation 효과 분리 |
| **Anchor 다양화** | KCGS 외에 MSCI · Sustinvest · 한국기업지배구조원 G 등급 단독 — 다중 anchor 정합성 검증 |
| **Pre-registration** | 후속 표본에서 4개 alpha 를 *사전 등록* 후 재검증 → selection bias 최소화 |
| **Semantic similarity (KoBERT)** | seed-based TF-IDF 의 vocabulary 한계 보완 — passage 단위 ESG 의미 유사도 |
| **DiD / IV 식별 전략** | KCGS 평가 변경 사건 (firm-year level rating shock) 을 활용한 *준자연실험* 식별 |

---

## 8. 발표용 narrative — 한 페이지 요약

### 8.1 시작 (problem statement)

> "ESG 공시 언어를 어떻게 측정해야 *맞게* 측정한 것인가?"
>
> 우리는 이 질문에 *유일한 정답이 없다* 는 것을 보였다.

### 8.2 중간 (what we found)

- preprocessing 강도를 바꿔도 ρ 부호는 흔들리지 않지만 *크기는 변한다*
- tokenizer 를 바꾸면 ESG vocabulary 의 *외연이 달라진다*
- 분량 (log_tokens) 이 KCGS 와의 연관 중 *상당 부분을 흡수* 한다
- 표본을 30 → 210 으로 확장하면 ρ 부호가 *뒤집힌다*
- 4개 alpha 모두 *cheap-talk 가설과 정합* 하는 방향을 가리킨다

### 8.3 끝 (what we claim)

> 본 표본의 한국 사업보고서에서, ESG 공시 언어는 외부 평가와 *단순 정합하지 않는다*. 약한 음의 연관, 강한 분량 효과, 부호 역전, 4개 alpha 정합 — 이 다섯 가지는 모두 *언어와 성과의 간극* 이라는 한 가설과 일관된다.

### 8.4 끝의 끝 (what we don't claim)

- 어느 firm 이 cheap-talk 을 하는지 *말할 수 없다*
- ESG 언어를 *예측 신호로 쓸 수 있다고 권하지 않는다*
- 본 finding 이 KOSDAQ·다른 anchor 에서도 *유효할지* 알 수 없다

---

## 9. Decision Box · 전체 연구 framing 선택

- **Alternative:**
  - (a) "ESG predictor 만들기" 연구로 framing — accuracy·F1 보고 중심
  - (b) "ESG measurement instability" 연구로 framing — robustness·sensitivity 중심
  - (c) "cheap-talk 가설 검정" 연구로 framing — 4개 alpha 중심
- **Choice:** (b) + (c) 결합. instability 가 main framing, cheap-talk 이 sub-framing
- **Justification:** (a) 는 본 표본 (N=210) · feature set 의 약한 효과 크기로는 정직하게 주장하기 어려움. (b) 는 본 연구의 실험 설계 (3개 전처리, 5개 모형, 4개 alpha, sub-sampling) 와 정합. (c) 는 finding 의 해석 방향을 제공
- **Limitation:** (b) 와 (c) 의 결합이 *방어적* 으로 비칠 위험 — 그러나 association-only 데이터에서는 *과주장* 보다 *조심스러운 정합 주장* 이 더 정직

---

## 10. 핵심 메시지 한 줄

> **본 연구의 finding 은 "ESG 공시 언어 → KCGS 등급" 의 강한 신호가 아니라, *그 신호의 fragility* 와 *분량 효과가 그 신호를 상당 부분 설명한다* 는 사실이다. 이 fragility 와 verbosity dominance, 그리고 4개 alpha 의 cheap-talk 정합은 — 한국 사업보고서의 ESG 언어가 외부 평가와 단순 정합하지 않는, *strategic disclosure* 행태의 measurement evidence 로 해석된다. 이 결과는 ESG 공시 연구가 단순 빈도·예측 모형에서 멈출 수 없는 이유를 한 corpus 위에서 정량적으로 보여 준다.**

---

**산출 파일 (전체 파이프라인 통합)**

- `ESG_DART_Integrated_Pipeline.ipynb` — 통합 분석 노트북
- `data/06_analysis/regression_M1_M5_summary.csv` — 5 모형 통합 계수표
- `data/06_analysis/cheap_talk_evidence_matrix.csv` — 4 alpha 통합 표
- `data/06_analysis/robustness_by_exp.csv` — preprocessing robustness
- `data/06_analysis/alpha3_subsample_summary.csv` — sign reversal sub-sampling 진단
- `00_ingest_report.md` ~ `07_appendix_team_and_insight.md` — 통합 narrative 8 부
