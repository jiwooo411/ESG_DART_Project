# 07_appendix_team_and_insight.md
## Appendix — Team Collaboration · Strengths · Limitations · Insight

> 이 부록은 두 부분으로 구성된다.
>
> - **Appendix A** — 팀 협업의 *evolution narrative* (hierarchy 또는 hero narrative 없음)
> - **Appendix B** — 본 파이프라인의 *Strengths · Limitations · Insight*
>
> 두 appendix 모두 "누가 더 잘했는가" 가 아니라 *"어떤 실험이 어떤 evidence 를 강화했는가"* 를 기록한다.

---

# Appendix A · Team Collaboration Narrative

## A.0 이 appendix 의 framing

본 프로젝트는 단일 분석자의 결과물이 아니다. 팀원들의 *서로 다른 실험과 강점* 이 통합 cycle 을 거쳐 최종 narrative 로 합쳐졌다.

그러나 본 부록은 한 가지 *서술 원칙* 을 따른다.

> **누가 무엇을 했는가** 가 아니라 **어떤 실험이 어떤 evidence 를 강화했는가** 를 기록한다.

이 원칙은 두 가지 이유에서 나왔다.

1. 본 연구의 핵심 framing — *"instability 가 finding 이다"* — 는 *재현 가능한 패턴* 위에 서 있다. 한 사람의 실험이 단독으로 그 패턴을 만들지 않는다.
2. *robustness evidence* 는 본디 *다층 실험의 산물* 이다. 한 라인의 실험은 다른 라인의 실험에 의해 *재현* 되어야 의미가 있다.

따라서 이 appendix 는 *기여 등급 매기기* 가 아니라 *evidence flow tracking* 이다.

---

## A.1 기여 매핑 — 어떤 실험이 어떤 evidence 를 강화했는가

| 영역 | 활용된 강점 | 통합 파이프라인 기여 |
|---|---|---|
| **Tokenizer robustness 실험** | Kiwi vs Okt 8 지표 비교 분석 | §2 의 *tokenizer instability* evidence 제공. 단일 tokenizer 선택의 한계를 정량화 |
| **Preprocessing eval (exp_B / E / F)** | 정제 강도 trade-off 분석 | §2.6 *preprocessing sensitivity* inset 의 직접 입력. canonical = exp_F 결정의 근거 |
| **Top-N 토큰 직접 읽기** | BP / ESG / G-signal 분류 | §2 의 ESG specificity 검증 평가표 정합 ("직접 읽고 판단") |
| **fastText dictionary 확장** | manual_v1 (7 단어) 후보 검토 | §3.5 의 expanded dictionary 절차 frame 과 honest gap statement |
| **Seed dictionary validation** | seed 별 corpus 등장 빈도 + 개별 ρ | §3.5.3 희소도 진단의 cross-reference |
| **Sample definition sensitivity** | N=30 → N=210 N-curve 분석 | §5.6 + §6 Alpha 3 sign reversal 의 직접 evidence |
| **Regression robustness 실험** | sign reversal 발견 | §6 Alpha 3 cheap-talk narrative 강화 |

---

## A.2 협업 evolution — 단순 → 복합으로 가는 과정

본 프로젝트가 *단순 카운트 → ratio → TF-IDF → fastText 확장 → robustness 다층화* 로 발전한 것은 한 사람의 결정이 아니다. 다음과 같은 *교차 영향* 이 있었다.

### A.2.1 첫 cycle — 단순 빈도 측정의 한계 인지

- 한 라인이 ESG seed token 의 단순 빈도 (count) 를 계산해 KCGS 와 비교
- 결과: 양의 ρ 가 *대형 firm 편향* 표본에서 나왔으나 안정성을 확신할 수 없었음
- 이 결과를 *그대로 채택하지 않은* 것이 후속 cycle 을 가능하게 했다

### A.2.2 두 번째 cycle — ratio 로의 이동, verbosity 문제 발견

- 다른 라인이 firm 길이 차이를 통제하기 위해 ratio (g_signal_ratio · esg_signal_ratio) 를 도입
- 그러나 ratio 도 *분량 효과를 완전히 제거하지 못한다* 는 점이 회귀 분석에서 드러남
- 이 발견이 §4 verbosity 통제 + §6 Alpha 1 verbosity-adjusted score 의 출발점이 됨

### A.2.3 세 번째 cycle — preprocessing 실험 다층화

- 또 다른 라인이 boilerplate 정제 강도에 따라 결과가 어떻게 변하는지 실험 (exp_B → exp_E → exp_F)
- 이 라인이 *없었다면* "preprocessing sensitivity" inset 자체가 존재할 수 없었음
- *instability 가 한 분석의 우연이 아니라 재현 가능한 패턴* 임을 보일 수 있었음

### A.2.4 네 번째 cycle — dictionary 확장 시도

- 또 다른 라인이 fastText 로 seed dictionary 를 확장 (manual_v1, 7 단어)
- *Final pipeline 의 N=210 에는 정식 통합되지 못함* — 이 사실 자체가 §3.5 의 *honest gap statement* 가 됨
- "확장 시도가 있었으나 한계가 있었다" 는 기록이 후속 연구의 출발점

### A.2.5 다섯 번째 cycle — sample definition sensitivity, sign reversal 발견

- 한 라인이 N=30 → N=210 으로 표본을 확장하는 N-curve 분석을 실행
- *sign reversal 의 발견* 이 이 cycle 에서 일어남
- 이 발견이 §6 Alpha 3 의 *cheap-talk evidence narrative* 로 통합됨

---

## A.3 교차 영향의 narrative — *evidence 가 어떻게 보강되었는가*

> **하나의 결과는 다른 라인의 실험에 의해 보강될 때만 *robust* 하다.**

이 원칙이 본 프로젝트의 협업 구조를 규정했다.

| 한 라인의 결과 | 다른 라인이 어떻게 보강했는가 |
|---|---|
| ratio 변수 도입 (verbosity 문제 인지) | preprocessing 라인이 같은 ratio 가 exp_B / E / F 에서 어떻게 변하는지 비교 → ratio 자체의 stability 확인 |
| preprocessing 실험 (exp_F 우월성 시사) | tokenizer 라인이 *Kiwi 자체가 가정* 임을 보임 → exp_F 우월성을 *조건부* 로 한정 |
| sign reversal 발견 (N=30 → 210) | sub-sampling 라인이 *그 부호 반전이 통계 인공물이 아님을 1,000회 재현* 으로 보임 → finding 으로 격상 |
| fastText 확장 시도 | seed validation 라인이 *seed 가 corpus 에서 얼마나 희소한지* 를 정량화 → 확장의 *필요성과 한계* 동시에 기록 |

---

## A.4 협업의 *최종 결과*

본 통합 파이프라인은 *각 실험에서 살아남은 evidence* 를 한 narrative 로 정리한 결과물이다.

- 어떤 실험은 final 파이프라인의 main path 가 되었다 (exp_F · ratio · TF-IDF)
- 어떤 실험은 robustness inset 의 cross-reference 가 되었다 (Okt 비교 · sub-sampling)
- 어떤 실험은 *honest gap statement* 로 기록되었다 (fastText 확장 미통합)

> **세 가지 모두 narrative 에서 동등하게 필요하다.** main path 가 *결과* 이고 robustness inset 이 *그 결과의 조건부 한정* 이며 honest gap 이 *그 결과의 future work* 이다.

---

## A.5 협업 원칙 (이후 cycle 을 위한 기록)

| 원칙 | 의미 |
|---|---|
| hierarchy 금지 | 한 라인의 실험이 다른 라인의 실험보다 *더 중요* 하다고 사전 정렬하지 않음 |
| hero narrative 금지 | 한 사람의 결정이 결과를 만들었다고 서술하지 않음 |
| evidence flow tracking | 각 실험이 *어떤 evidence layer 를 강화* 했는지를 기록 |
| honest gap | 통합되지 못한 실험도 *기록 자체* 가 가치 |
| robustness as collaboration | robustness 는 *한 분석자의 일* 이 아니라 *다층 실험의 산물* |

---

---

# Appendix B · Strengths · Limitations · Insight

## B.0 이 appendix 의 framing

본 부록은 *통합 파이프라인이 어떤 연구 색깔을 가지는지* 를 기록하는 메타-documentation 이다.
자기 PR 이 아니라, *왜 이 pipeline 이 이런 구조로 발전했는지* 를 설명한다.

세 부분으로 구성된다.

- **B.1 Strengths** — 본 파이프라인이 가진 5가지 강점
- **B.2 Limitations** — 본 파이프라인이 가진 6가지 한계
- **B.3 Insight** — 이 연구에서 *반드시 기록되어야 하는* 4가지 insight

---

## B.1 Strengths

### B.1.1 Robustness comparison 을 main result 옆에 배치

| 강점 | 어디서 드러나는가 |
|---|---|
| Robustness inset 적극 노출 | §2.6, §4.5, §5.6 — 모든 main result 옆에 robustness inset 배치 |
| Preprocessing sensitivity 를 결과 일부로 통합 | §2 본문에서 exp_B / E / F 비교를 main figure 로 노출 |
| Sample sensitivity 를 결과 일부로 통합 | §5.6 N-curve + §6 Alpha 3 sub-sampling 분포 |

> *Robustness 를 footnote 가 아니라 main figure 옆에 둔다는 결정* 이 본 파이프라인을 다른 ESG NLP 연구와 차별화한다.

### B.1.2 Data lineage transparency

| 강점 | 어디서 드러나는가 |
|---|---|
| 5-key identifier 원칙 | §1 — stock_code / corp_code / rcept_no / fiscal_year / esg_year |
| Salvage log 보존 | 각 firm-year 의 INCLUDE / EXCLUDE_NO_RCEPT / EXCLUDE_KCGS_NA 단일 truth |
| company_name merge 금지 | 표기 변동 위험을 *시스템적으로* 차단 |
| Failed collection 행 보존 | 0 으로 채우지 않음 — 누락 사유를 명시적으로 로그 |

> *재현 가능성 (reproducibility)* 이 *결과 강도* 보다 우선한다는 원칙.

### B.1.3 Preprocessing documentation

| 강점 | 어디서 드러나는가 |
|---|---|
| G_SIGNAL_PROTECT 정책 | 13 단어가 불용어와 겹치지 않도록 명시적 검증 |
| 사용자 사전 등록 + 단위 테스트 | 재생에너지·감사위원회·탄소중립이 단일 토큰으로 보존되는지 검증 |
| Sentence-level boilerplate 필터 | 토큰 단위가 아닌 *문장 패턴* 으로 의무공시 제거 — 동의어 잡음 회피 |
| exp_B / E / F 비교 매트릭스 | 정제 강도의 trade-off 를 *표로* 노출 |

> *각 전처리 결정* 이 *각각의 정당화* 를 갖는 것 — 결정 box framework 의 일관 적용.

### B.1.4 Cheap-talk framing 의 일관 적용

| 강점 | 어디서 드러나는가 |
|---|---|
| disclosure intensity ≠ ESG performance | 모든 보고서·모든 figure caption 에서 일관 적용 |
| association ≠ causation | OLS · Ordered Logit · Binary Logit 모두 *"associated with"* 어휘만 사용 |
| weak signal 도 finding 으로 인정 | ρ ≈ 0.18 을 "유의하지만 약함" 으로 명시 보고 |
| Verbosity dominance 를 핵심 변수로 취급 | §4 M1 → M2 계수 변화 + §6 Alpha 1 verbosity-adjusted score |

> *어휘 선택* 자체가 *해석 강도* 의 일관성을 보장한다.

### B.1.5 Sign reversal 을 finding 으로 격상

| 강점 | 어디서 드러나는가 |
|---|---|
| Pilot 결과를 *숨기지 않음* | §3 + §4 + §6 모두에서 pilot ρ 표 명시 |
| Sub-sampling 1,000회 재현 | Alpha 3 — 양의 ρ 발생 빈도 정량화 |
| "잡음 / 오류" 어휘 금지 | "small-sample fragility · sampling sensitivity · measurement instability" 로 framing |
| Decision Box 로 해석 결정 명시 | sign reversal 을 어떻게 다룰지 *결정 자체를 기록* |

> 다른 연구에서는 "표본을 늘렸더니 결과가 바뀌었다" 가 *fooltnote 또는 무시* 로 처리된다.
> 본 파이프라인에서는 *그것이 가장 중요한 finding 중 하나* 다.

---

## B.2 Limitations

### B.2.1 표본 한계

| 한계 | 의미 |
|---|---|
| **N = 77 firms × 3 years = 210 firm-years** | KOSPI 중심, KOSDAQ·KONEX·비상장 미포함 |
| **D · C 군 표본 부족** | 평균이 단일 firm-year 에 흔들림 — Alpha 2 단조 패턴의 약한 부분 |
| **FY 2021–2023 만 다룸** | 코로나 회복기·ESG 의무공시 도입 초기 — 시기 편향 |

### B.2.2 외부 anchor 한계

| 한계 | 의미 |
|---|---|
| **KCGS 평가 방법 비공개** | 등급이 어떤 기준을 반영하는지 알 수 없음 — anchor 자체의 measurement error |
| **G 단독 등급 미사용** | Alpha 4 "거버넌스 paradox" 가 *G 어휘 vs 종합 ESG 등급* 으로만 검정됨 |
| **단일 anchor** | MSCI · Sustinvest 등과의 cross-validation 미수행 |

### B.2.3 통계적 식별 한계

| 한계 | 의미 |
|---|---|
| **인과 추론 불가** | OLS · Ordered Logit · Binary Logit 모두 association 만 |
| **firm 고정효과 미통제** | 산업·연도 FE 만 — within-firm 변동 정보 미활용 |
| **multiple testing 우려** | 4개 alpha 동시 검정 — 사전 등록 (pre-registration) 부재 |
| **약한 효과 크기** | ρ ≈ 0.10–0.20, R² ≈ 10–15% — instability narrative 의 *전제* 이기도 |

### B.2.4 Dictionary 확장 미통합

| 한계 | 의미 |
|---|---|
| **manual_v1 (7 단어) 이 main path 에 미반영** | N = 29 subset 에서만 계산됨. final N = 210 에 fully 통합되지 못함 |
| **θ 정량 비교 미수행** | fastText 모델이 final 코드베이스에 부재 — θ ∈ {0.5, 0.6, 0.7} 비교 표 부재 |
| **Seed 30 sparsity 미해결** | 일부 seed 의 corpus 등장 빈도가 0 — 표본에서 사용되지 않는 ESG 차원 존재 |

### B.2.5 Preprocessing 의존성

| 한계 | 의미 |
|---|---|
| **exp_F 를 canonical 로 두지만 그 자체가 가정** | preprocessing 선택이 결과의 *조건부 가정* 으로 들어감 |
| **Tokenizer 비교가 부분 외부 노트북에 의존** | Kiwi vs Okt 비교는 본 파이프라인 *바깥* 노트북에 있음 (cross-reference) |
| **사용자 사전 자체가 결정** | 어떤 단어를 단일 토큰으로 보호할지가 *분석자 결정* |

### B.2.6 본 연구의 *circular* 한 측면

> "instability 를 finding 으로 본다" 는 framing 은 *어떤 결과* 도 *finding 으로 해석할 위험* 이 있다.

본 파이프라인은 이 위험을 다음과 같이 통제했다.

- 모든 instability 를 *재현 가능한 robustness 실험* 으로 보임 (한 번의 우연이 아니라 다층 패턴)
- 4개 alpha 를 *모두 보고* (selection bias 회피)
- Honest gap statement 로 *통합되지 못한 실험* 도 명시

그러나 이 통제가 완전하지 않다. 후속 연구에서는 *pre-registration* 으로 framing 자체의 사전 합의가 필요하다.

---

## B.3 Insight — 반드시 기록되어야 하는 4가지

### B.3.1 Instability 자체가 finding 이다

ESG 텍스트 분석의 일반적 framing 은 *"신호를 더 잘 잡는 측정"* 을 만드는 것이다.
본 파이프라인은 *반대로* 접근한다.

> 같은 corpus 에서 분석자의 선택을 한 단계만 바꿨을 때 결과가 흔들린다면, *그 흔들림 자체* 가 *공시 언어가 외부 평가와 단순 정합하지 않는다* 는 사실을 가리킨다.

이는 측정 도구의 결함이 아니라 *측정 대상의 본질적 특성* 이다. ESG disclosure 는 strategic communication 행위이며, 그 *언어의 외연·정밀도·통제* 에 모두 가정이 들어간다.

> *"우리는 ESG 를 측정하지 않았다. 우리는 ESG 를 측정하기 어렵다는 사실을 측정했다."*

### B.3.2 Verbosity dominance 가 cheap-talk 의 첫 번째 layer 다

`g_signal_ratio` 가 KCGS 등급과 가진 univariate 음의 연관 중 *상당 부분이 분량 (`log_tokens`) 으로 흡수* 된다. 이는 다음 두 가지 의미를 동시에 갖는다.

1. **단순 카운트나 단순 TF-IDF 로는 cheap-talk 의 한 layer 가 드러나지 않는다.** 분량을 통제하기 전에는 신호가 *분량 효과의 그림자* 와 구별되지 않는다.
2. **분량을 통제한 후에도 음의 잔여 신호가 남는다.** 즉 cheap-talk 의 layer 가 *완전히 verbosity 로 환원되지 않는다*.

이 두 사실의 결합이 본 연구의 *가장 정직한 evidence* 다.

> *"분량을 빼면 신호가 사라지는가? 일부는 사라지고 일부는 남는다. 그 잔여가 cheap-talk 가설과 정합한다."*

### B.3.3 Sign reversal 은 통계 인공물이 아니다

`g_signal_ratio` 와 KCGS 등급의 ρ 가 *pilot (N=30) 에서 양, full (N=210) 에서 음* 으로 뒤집힌 것은 다음을 의미한다.

| 가능한 해석 | 본 보고서의 입장 |
|---|---|
| 통계적 잡음 | ✗ — sub-sampling 1,000회 재현에서 분포 중심이 음 |
| 단일 outlier 영향 | ✗ — Cook's distance 진단에서 단일 firm-year 가 결정짓지 않음 |
| Small-sample 인공물 | ✓ — pilot 의 대형주 편향이 양의 ρ 를 우연히 만들었음 |
| **Cheap-talk evidence** | ✓ — 표본이 넓어지면서 "낮은 등급일수록 ESG 어휘를 더 쓴다" 가 드러남 |

> *"sign reversal 은 cheap-talk 가설을 *증명* 하지 않는다. *정합한다*까지가 본 연구의 주장이다.*"

### B.3.4a (Refinement note) Verbosity dominance 의 한 단계 더 — *공동 구성 요소 분리*

> 본 note 는 §B.3.2 의 *refinement* 다. §B.3.2 의 결론 ("verbosity dominance 가 cheap-talk 의 첫 번째 layer") 은 *방향성으로는 유지* 되지만, 한 단계 더 정확한 framing 이 가능하다.

`g_signal_ratio` 와 `log_tokens` 의 Pearson 상관: **r ≈ −0.79**.

이 사실은 다음을 시사한다.

| 기존 framing (§B.3.2) | refined framing |
|---|---|
| `log_tokens` 는 *교란 변수* — 통제하면 잔여가 *순수 G 신호* | `log_tokens` 는 *공동 구성 요소* — `g_signal_ratio` 자체가 *분량의 역함수에 가까움*. 따라서 "통제" 는 *공동 구성 요소 분리* |
| verbosity 통제 후 음의 잔여 신호가 *cheap-talk evidence* | verbosity 통제 후 잔여 신호가 *어떤 통제 set* 에 조건부 — `log_tokens` 만 빼면 ρ ≈ +0.058 (ns), `log_tokens + 산업·연도 FE` 빼면 약한 음 |

즉 §B.3.2 의 evidence 는 *유지되되 강도가 조정* 된다.

> *"verbosity dominance 는 cheap-talk 의 첫 번째 layer 이지만, *그 layer 의 두께가 얼마인지* 는 통제 변수 set 의 정의에 종속된다."*

### B.3.5 (New insight) Feature redundancy 가 measurement narrative 의 새 layer 다

`g_signal_ratio` · `esg_signal_ratio` · `esg_tfidf_concentration` 동시 투입 시:
- **`g_signal_ratio` ↔ `esg_tfidf_concentration` r ≈ +0.88**
- VIF 상승
- `g_signal_ratio` 계수가 main pair 대비 약화/반전

이는 다음을 시사한다.

| 가능한 해석 | 본 연구의 입장 |
|---|---|
| 세 변수가 *독립적인 disclosure 차원* | 본 데이터에서 *지지 어려움* — r ≈ 0.88 + VIF 상승이 *독립* 가설과 충돌 |
| 세 변수가 *같은 disclosure intensity 의 다른 표현* | 본 데이터에서 *더 강하게 지지* |

이 결과의 함의가 본 연구의 *연구 색깔* 에 미치는 영향:

1. 본 연구의 *다층 측정* (count → ratio → TF-IDF → concentration) 이 *서로 보강하는 4 개의 독립 evidence* 라기보다 *하나의 evidence 의 4 가지 표현* 일 수 있다.
2. 따라서 4 alpha cheap-talk evidence matrix 의 *정합* 은 *세 독립 차원의 정합* 이 아니라 *하나의 신호의 세 가지 표현이 모두 같은 방향을 가리킴* — *evidence 강도가 단순 누적되지 않음*.
3. 본 연구의 *robustness 색깔* 은 *유지* 되되, "독립 다층 측정" 이라는 표현은 *"같은 disclosure intensity 의 다양한 정규화"* 로 refinement 되어야 한다.

> *"우리는 ESG disclosure 를 *세 번 다르게* 측정했다. 그 세 측정이 r ≈ 0.88 로 강하게 일치한다는 사실은 *세 측정이 robust 하다* 는 의미 이전에 *세 측정이 사실상 같은 것을 측정한다* 는 의미였다."*

이는 *measurement reliability* 의 한 형태이지만 *measurement validity* 의 *추가 evidence* 가 *아니다*. 본 연구의 evidence 강도를 *합산* 할 때 이 구분이 결정적이다.

### B.3.6 (New insight) Year-specific E-G asymmetry — *suggestive* 새 차원

2024 cross-section 에서 관찰된 **E disclosure (+) vs G rhetoric (−)** directional asymmetry (E bootstrap CI = [−0.003, +0.454]) 는 본 연구의 새 차원이다.

이 발견의 위치:

| 차원 | 본 연구의 narrative 에서 |
|---|---|
| *증거 강도* | suggestive (CI 0 살짝 포함, 단년도) — *증명 부재* |
| *narrative 기여* | "ESG 가 *하나의 차원* 이 아닐 가능성" — cheap-talk 가설의 *차원별 강도 비대칭* 가설 제기 |
| *후속 연구로의 연결* | 다년도 panel 에서의 재현 검증 + E/S/G 단독 anchor 와의 cross-validation |

본 발견이 *연구로서의 가치를 잃지 않는다* — 단지 *그 가치가 어디까지인지* 가 *재현 검증* 에 종속된다.

> *"단일 ESG 점수로 합치는 측정 자체에 *집계 편향* 가능성이 있을 수 있다. 본 연구는 그 가능성을 *제기* 한다 — *증명하지 않는다*."*

### B.3.4 Dictionary 확장의 한계 자체가 measurement narrative 다

본 파이프라인은 manual_v1 (7 단어) 의 fastText 확장 결과를 *final pipeline 의 N=210 에 정식 통합하지 못했다*. 이 honest gap 자체가 본 연구의 framing 과 정합한다.

> *"seed 30 이 corpus 의 ESG 어휘를 충분히 포착했는가? — 우리는 그 질문에 *완전히 답하지 못했다*. 그리고 그 답하지 못함이 ESG 어휘의 *정의 자체* 가 가진 fragility 를 다시 한 번 보여 준다."*

이는 *"우리가 안 한 것"* 의 기록이 *"우리가 한 것"* 의 기록만큼 중요하다는 본 연구의 일관된 입장이다.

---

## B.4 연구 철학 / Methodological Style

| 원칙 | 의미 |
|---|---|
| **Best model competition 보다 measurement interpretation 중심** | 어느 모형이 가장 높은 R² 를 갖는지가 아니라, 같은 신호가 모형 간에 어떻게 흔들리는지에 집중 |
| **Instability 를 제거 대상이 아니라 분석 대상으로 취급** | sign reversal · preprocessing variance 를 *닦아내지 않고* 보고서에 포함 |
| **Robustness 를 contribution 으로 활용** | exp_B / E / F · tokenizer 비교 · N-curve 분석을 main result 옆에 robustness inset 으로 배치 |
| **Reproducibility + transparency 중시** | 5-key identifier · salvage log · decision box · honest gap statement |
| **약한 결과를 약한 그대로 보고** | ρ ≈ 0.18 을 "유의하지만 weak" 으로 명시 — 과주장 회피 |
| **Association-only 어휘 유지** | "causes / predicts / improves / true ESG" 어휘 사용 금지 — 모든 보고서에서 일관 적용 |
| **Cheap-talk evidence matrix** | 4개 alpha 를 *모두 보고* — selection bias 회피 |

---

## B.5 마무리 — 본 연구의 자기 평가 한 줄

> **본 연구는 *ESG 신호를 잘 잡는 측정* 을 만드는 데 실패했다. 그러나 그 실패가 *cheap-talk 가설을 검증할 수 있는 measurement evidence* 로 격상될 수 있었던 이유는, 우리가 instability 를 *닦아내지 않고 분석 대상으로 보존* 했기 때문이다.**

이 한 줄이 본 파이프라인의 *연구 색깔* 이자 *후속 연구가 출발할 수 있는 지점* 이다.

### B.5.1 Refinement cycle 이후의 자기 평가 한 줄 (added)

> **본 연구는 cheap-talk 을 *증명하지 않았다*. 본 연구는 ESG disclosure language 신호의 *fragility 와 verbosity sensitivity 와 feature redundancy* 를 정량적으로 드러내면서, *E vs G 차원의 directional asymmetry* 라는 — *suggestive 수준의* — 흥미로운 패턴을 후속 연구를 위해 *남겼다*. 이 refinement 가 본 연구를 단순 상관분석에서 *robustness-aware ESG disclosure methodology study* 로 진화시킨 지점이다.**

> **canonical final narrative:** `08_revised_final_report.md`

---

**산출 파일 (appendix 직접 참조)**

- `data/06_analysis/cheap_talk_evidence_matrix.csv` — 4 alpha 통합 표
- `data/06_analysis/robustness_by_exp.csv` — preprocessing robustness
- `data/06_analysis/alpha3_subsample_summary.csv` — sub-sampling 진단치
- `data/04_preprocessed/seed_corpus_freq.csv` — seed sparsity 진단
- `data/00_meta/salvage_log.csv` — firm-year 단일 truth 로그
- `ESG_DART_Integrated_Pipeline.ipynb` — 통합 파이프라인 (본 부록의 cross-reference)
