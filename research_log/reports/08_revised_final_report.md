# 08_revised_final_report.md
## Revised Final Narrative — From Cheap-Talk Claim to Fragility-Aware Refinement

> **본 revised 문서의 위치**
> 본 문서는 `06_final_takeaway_report.md` (first-draft) 를 *대체* 하지 않는다. 06 은 *cheap-talk narrative 가 어떻게 처음 정리되었는지* 를 보여주는 historical record 로 보존된다.
> 본 문서 08 은 그 narrative 가 *추가 robustness 분석 — orthogonalization · joint regression · year-specific cross-section — 이후 어떻게 refinement 되었는지* 를 정리한 **canonical final narrative** 이다.

> **연구 질문 (재확인)**
> 한국 사업보고서의 ESG 관련 공시 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가? 그리고 그 연관은 *어떤 측정 가정* 위에서 성립하는가?

> **본 revised 문서가 *답하지 않는* 질문**
> 어느 firm 이 cheap-talk 을 하는가? ESG 언어가 ESG 성과를 *예측* 하는가? ESG 성과에 *영향을 주는가*? — 본 데이터·설계로 답할 수 없다.

---

## 0. 왜 이 refinement 가 필요했는가

`06_final_takeaway_report.md` 는 네 layer 의 instability (preprocessing · tokenizer · verbosity · sign reversal) 와 4 alpha 의 cheap-talk 정합을 main narrative 로 정리했다. 그 시점의 framing 은 다음과 같았다.

> *"4개 alpha 가 모두 cheap-talk 가설과 정합하는 방향을 가리킨다."*

이 framing 자체는 *어휘적으로* 이미 조심스러웠다 — "정합한다" 까지만 주장하고 "증명" 하지 않았다. 그러나 *evidence 의 강도* 에 대해서는 한 단계 더 검증이 필요했다.

이 refinement cycle 에서 추가된 분석은 세 가지다.

| 추가 분석 | 무엇을 검증했는가 |
|---|---|
| **Orthogonalization** | `g_signal_ratio` 의 음의 연관이 verbosity (`log_tokens`) 와 *기계적으로 얽혀* 있던 것은 아닌가 |
| **Joint regression** | `g_signal_ratio` · `esg_signal_ratio` · `esg_tfidf_concentration` · `log_tokens` 를 동시에 투입했을 때 신호가 *서로를 잡아먹는가* |
| **Year-specific cross-section** | 단년도 (2024) 단면에서 E disclosure 와 G rhetoric 이 *같은 방향* 으로 움직이는가, 아니면 *비대칭* 인가 |

세 분석 모두 main narrative 의 단순 보강이 아니라 *narrative 자체의 강도* 를 재검토하는 도구다. 결과적으로 cheap-talk framing 은 *유지되되 강도가 낮춰진다*.

---

## 1. 핵심 refinement 요약 (한 페이지)

| 차원 | 06 first-draft 의 framing | 08 revised 의 refined framing |
|---|---|---|
| **Full-sample G negative relation** | 표본 확장 후 안정적 음의 연관 — cheap-talk 가설과 정합 | 음의 방향 유지 — 그러나 *feature 구성 결정에 매우 민감*. orthogonalize 후 신호가 0 부근으로 약화 |
| **Verbosity 의 역할** | univariate 음의 연관 중 *상당 부분* 이 분량으로 흡수 | `g_signal_ratio ↔ log_tokens` r ≈ **−0.79** — ratio 자체가 *분량의 역함수처럼* 작동. verbosity 는 *통제 변수* 가 아니라 *공동 구성 요소* |
| **Joint regression** | main pair (`g_signal_ratio + log_tokens`) 로 단순화 | 4 변수 동시 투입 시 `g_signal ↔ tfidf` r ≈ **+0.88**, VIF 상승, g 부호 약화/반전 — "같은 disclosure intensity 를 다른 척도로 측정한 것" 가능성 |
| **Pilot vs full sign reversal** | small-sample artifact + cheap-talk evidence | pilot 의 양의 ρ 는 *large-cap · verbosity structure 편향* 의 산물 가능성. full sample 의 음의 ρ 는 *feature construction artifact 가능성* 도 포함 |
| **E vs G** | 통합 ESG 신호로 다룸 | 2024 cross-section 에서 **E disclosure ↔ KCGS positive · G rhetoric ↔ KCGS negative** 의 *directional asymmetry* 관측. 단 E 의 bootstrap CI = **[−0.003, +0.454]** — 0 을 살짝 포함, *tentative* 수준 |
| **Cheap-talk claim** | "4개 alpha 가 cheap-talk 가설과 정합" | "*Confirmed cheap-talk* 이 아니라 *methodologically fragile but suggestive evidence*" |
| **연구의 색깔** | ESG language measurement instability study | **Robustness-aware ESG disclosure methodology study** |

> **한 문장 요약:**
> 본 refinement 는 cheap-talk 을 *강화하지 않는다*. 본 refinement 는 cheap-talk 가설의 *증거 강도가 feature construction sensitivity 에 종속됨* 을 정직하게 드러낸다. 그러나 같은 데이터 안에서 **2024 단면의 E(+) vs G(−) directional asymmetry** 라는 — 단순 verbosity 로 환원되지 않는 — 패턴이 발견되었다는 점에서 *연구로서의 가치를 잃지 않는다*.

---

## 2. Refinement 1 — Verbosity Confounding 의 실증적 의미

### 2.1 무엇이 새로 드러났는가

`g_signal_ratio` 와 `log_tokens` 의 Pearson 상관은 **r ≈ −0.79**.

즉 `g_signal_ratio` 는 *짧은 보고서에서 높고, 긴 보고서에서 낮다*. 이는 ratio 의 정의상 *수학적으로 어느 정도 예상되는* 패턴이지만, 그 크기가 |r| ≈ 0.79 라는 것은 — 본 표본에서 `g_signal_ratio` 가 *G disclosure intensity 의 척도* 라기보다 *document length 의 역함수처럼* 작동하고 있었음을 시사한다.

### 2.2 왜 이것이 narrative 의 refinement 인가

`06_final_takeaway_report.md` §4 (Layer 3) 는 이 현상을 *"verbosity dominance"* 로 framing 했다. 그 framing 은 다음과 같았다.

> *"`g_signal_ratio` 가 KCGS 와 가진 univariate 음의 연관 중 상당 부분이 분량으로 흡수된다."*

이 표현은 *옳다*. 그러나 한 단계 더 강한 표현이 가능하다.

> *"`g_signal_ratio` 자체가 verbosity 의 역함수에 가깝게 구성되어 있다. 따라서 `log_tokens` 통제는 *교란 변수 제거* 가 아니라 *공동 구성 요소 분리* 다."*

이 구분은 academic 하게 중요하다. *교란 변수* 라면 통제 후 잔여가 *순수한 G signal* 이지만, *공동 구성 요소* 라면 통제 후 잔여는 *ratio 의 정의 안에 남은 잔재* 일 수 있다.

### 2.3 Orthogonalization 결과

이 우려를 직접 검정하기 위해 다음 절차를 시행했다.

```
Step 1:  g_signal_ratio  ~  log_tokens
         → 잔차  g_signal_ortho  =  log_tokens 와 *직교화* 된 G 어휘 강도

Step 2:  g_signal_ortho  ↔  kcgs_grade_7  Spearman ρ
```

결과: **ρ ≈ +0.058, p ≈ ns (비유의)**

이 결과의 의미.

| 관찰 | 해석 |
|---|---|
| ρ 의 *방향* 이 음에서 양으로 뒤집힘 | `g_signal_ratio` 의 음의 ρ 는 *순수한 G 신호* 라기보다 *verbosity 와의 기계적 얽힘* 의 산물일 수 있음 |
| ρ 의 *크기* 가 0 근방 | orthogonalize 후에는 G 어휘 강도와 KCGS 사이의 *robust 한* 단순 연관이 사라짐 |
| 통계적 유의성 부재 | 본 표본에서 "분량을 완전히 빼낸" G 어휘 강도가 KCGS 와 일관된 방향을 갖지 않음 |

### 2.4 Alpha 1 결과와의 관계 — 모순이 아니라 *층위의 차이*

`05_alpha_analysis_report.md` §1 의 verbosity-adjusted score (r_i) 는 *G 어휘 강도에서 분량 · 산업 · 연도 효과를 모두 빼낸* 잔차였고, KCGS 와 음의 방향을 *약하게* 유지했다.

본 §2.3 의 `g_signal_ortho` 는 *분량만* 빼낸 잔차다. 따라서 둘은 *다른 변수* 이고 다른 결과를 줄 수 있다.

| 잔차 정의 | 통제 변수 | KCGS 와의 방향 | 본 narrative 에서의 위치 |
|---|---|---|---|
| `g_signal_ortho` | `log_tokens` 만 | ρ ≈ +0.058 (ns) | "분량 효과만 빼면 신호가 사라짐" — *fragility evidence* |
| `r_i` (Alpha 1) | `log_tokens + industry_FE + year_FE` | 음의 방향 (약) | "분량 · 산업 · 연도 모두 빼면 약한 음의 잔여" — *cheap-talk consistency, weak* |

두 결과의 **공존**이 본 refinement 의 honest 한 그림이다. 어느 한 잔차가 *정답* 이 아니다.

> **Decision Box · 어느 잔차를 main 으로 보고할 것인가**
> - **Alternative:** (a) `g_signal_ortho` (verbosity 만 직교화), (b) `r_i` (verbosity + 산업·연도), (c) 둘 다 보고
> - **Choice:** (c) 둘 다 보고
> - **Justification:** 두 잔차는 *다른 가정* 위에 서 있음. (a) 는 보수적(가장 단순), (b) 는 통제 풍부. 어느 한쪽만 보고하면 selection bias
> - **Limitation:** 두 결과 방향이 다르다는 사실 자체가 *cheap-talk 결론의 fragility* — 본 refinement 의 핵심 메시지

### 2.5 한 줄 정리

> *"분량을 빼면 G 어휘 강도와 KCGS 의 단순 연관은 사라진다. 분량 + 산업 + 연도 를 빼면 약한 음의 잔여가 남는다. 어느 쪽이 *진짜 신호* 인지 본 데이터로는 결정할 수 없다."*

---

## 3. Refinement 2 — Joint Regression 과 Feature Collinearity

### 3.1 검정 설계

본 cycle 에서는 다음 변수를 *동시에* 회귀에 투입했다.

- `g_signal_ratio`
- `esg_signal_ratio`
- `esg_tfidf_concentration`
- `log_tokens`

### 3.2 결과의 핵심

| 진단 | 관찰 |
|---|---|
| **VIF** | 동시 투입 시 *상승* — 일부 변수에서 다중공선성 경계 진입 |
| **`g_signal_ratio` ↔ `esg_tfidf_concentration`** | Pearson r ≈ **+0.88** — 매우 강한 공선성 |
| **`g_signal_ratio` 계수** | main pair 대비 *약화 또는 부호 반전* |

### 3.3 무엇이 새로 드러나는가

`04_regression_robustness_report.md` §3 의 VIF 진단에서는 *main pair (g_signal_ratio + log_tokens)* 를 사용하고 ESG ratio · concentration 은 *robustness 보조* 로만 다루었다. 그 결정은 *해석가능성* 측면에서 정당했다.

그러나 *그 결정을 뒤집어* 4 변수를 동시에 투입해 보면, 다음과 같은 그림이 나타난다.

| 가능한 해석 | 무엇을 시사하는가 |
|---|---|
| (a) `g_signal_ratio`, `esg_signal_ratio`, `esg_tfidf_concentration` 이 *서로 다른 disclosure 차원* 을 측정한다 | 동시 투입은 *해석가능* — 각 계수가 *순수 한 차원의 효과* |
| (b) 세 변수가 *같은 disclosure intensity 를 다른 척도로* 측정한다 | 동시 투입은 *과적합* — 같은 신호를 세 번 측정해 서로 분산을 잡아먹음 |

r ≈ +0.88 + VIF 상승 + 계수 부호 약화/반전 의 **세 신호가 동시에 관찰** 된다는 점은 *(b) 해석을 더 지지* 한다.

즉:

> 본 corpus 에서 `g_signal_ratio` · `esg_signal_ratio` · `esg_tfidf_concentration` 는 *세 개의 독립적 disclosure 차원* 이라기보다 *하나의 disclosure intensity 를 다른 정규화 · 다른 가중치로* 측정한 척도일 가능성이 크다.

### 3.4 이것이 cheap-talk narrative 에 갖는 함의

만약 세 변수가 *같은 disclosure intensity 의 다른 표현* 이라면, "G 어휘 강도가 KCGS 와 음으로 관련된다" 는 주장의 *robustness* 가 다음 두 가지 의미에서 약해진다.

1. 부호와 강도가 *어느 척도를 선택하느냐* 에 따라 흔들린다 (joint 투입 시 부호 약화/반전)
2. 같은 신호를 *세 번 측정해 정합하는 것* 은 *세 개의 독립 evidence* 가 아니라 *하나의 evidence 의 세 가지 표현*

### 3.5 그러나 — 이것이 cheap-talk 가설을 *기각* 하지는 않는다

세 변수가 *같은 disclosure intensity 를 다른 척도로 측정* 한다는 사실 자체는 *공시 언어가 KCGS 와 어떻게 연관되는지* 의 질문에는 직접 답하지 않는다. 단지 *우리가 그 연관의 강도를 과대 평가하지 않도록* 경고한다.

> **Decision Box · joint regression 의 narrative 위치**
> - **Alternative:** (a) 본 결과를 *cheap-talk 기각 evidence* 로 해석, (b) feature redundancy evidence 로 해석, (c) 양쪽 모두 가능 — open
> - **Choice:** (b) + (c) — feature redundancy 가 1차 해석, cheap-talk 가설은 *판단 보류*
> - **Justification:** r ≈ 0.88 자체가 *변수 간 정보 중복* 의 직접 증거. cheap-talk 가설은 *직교적 dimension* 위에서 검정되어야 — 본 데이터로는 직교화 후 신호가 약함
> - **Limitation:** "feature redundancy" 자체가 *측정 도구의 문제* — 더 직교적인 feature set 을 설계하는 것이 future work

---

## 4. Refinement 3 — 2024 Cross-Section 의 E-G Asymmetry

### 4.1 새로운 관찰

3년 panel 전체가 아닌 *2024 단면* 만 본 결과:

| 차원 | KCGS 와의 관계 (Spearman ρ 방향) | bootstrap 95% CI |
|---|---|---|
| **E disclosure** | **+ (positive)** | 약 **[−0.003, +0.454]** (0 을 *살짝* 포함) |
| **G rhetoric** | **− (negative)** | 음의 방향 유지 |

### 4.2 이 패턴의 잠재적 의미

만약 이 directional asymmetry 가 *반복 관찰* 된다면, 다음을 시사할 수 있다.

| 해석 | 내용 |
|---|---|
| **E disclosure 가 substantive 일 가능성** | 환경 공시는 *측정가능한 정량 지표 (탄소 배출 · 재생에너지 비중)* 와 연동되기 쉬워 *공시량이 실제 성과를 부분적으로 반영* 가능 |
| **G rhetoric 이 ritualistic 일 가능성** | 거버넌스 공시는 *법적 양식에 의해 강제* 되어 *공시량이 실제 거버넌스 수준과 분리* — `06_final_takeaway` §4 Alpha 4 의 "거버넌스 paradox" 와 연장선 |
| **ESG 가 *하나의 차원* 이 아닐 가능성** | E · S · G 가 *서로 다른 disclosure incentive* 를 가진 *다른 자산 클래스* 일 수 있음 |

### 4.3 그러나 — 이 결과는 *tentative* 다

다음 한계가 동시에 있다.

| 한계 | 의미 |
|---|---|
| **단년도 (2024) 결과** | 패널 전체가 아닌 한 시점의 cross-section. 다음 해 (2025+) 에 재현되지 않을 수 있음 |
| **E bootstrap CI 가 0 을 살짝 포함 [−0.003, +0.454]** | 통계적 유의성 *경계* — "proof" 가 아니라 "suggestive" |
| **E disclosure feature 의 정의 자체가 본 cycle 의 결정** | seed dictionary · ratio 정의에 따라 결과가 흔들릴 수 있음 |
| **표본 구성** | 2024 단면 표본이 *어떤 firm 으로* 구성되었는지가 결과의 일부 — `06_final_takeaway` 의 sign reversal 교훈이 여기에도 적용 |

### 4.4 그럼에도 narrative 에 남겨야 하는 이유

이 directional asymmetry 는 *본 연구의 가장 흥미로운* 발견 중 하나다. 이유:

1. 그동안 본 연구의 narrative 는 "ESG 신호 전체" 를 한 덩어리로 다뤘다. 만약 E 와 G 가 *다른 방향* 으로 움직인다면, 단일 ESG 점수로 합치는 측정 자체에 *집계 편향* 가능성이 있다.
2. 이 패턴은 *cheap-talk 가설을 부분적으로 refine* 한다. cheap-talk 은 *모든* ESG 차원에서 균일하게 나타나지 않을 수 있으며, *법적 양식이 강한 영역 (G)* 에서 더 강하게 나타날 수 있다.
3. *Robustness-aware* 연구 철학과 정합 — 한 가지 척도가 작동하지 않을 때 *척도를 쪼개어 어디에서 신호가 살아남는지* 를 보는 것이 본 연구의 일관된 입장.

> **Decision Box · 2024 E-G asymmetry 를 어떻게 보고할 것인가**
> - **Alternative:** (a) main finding 으로 격상, (b) appendix 로 강등, (c) "suggestive cross-section finding" 으로 narrative 의 한 구성요소로 포함
> - **Choice:** (c)
> - **Justification:** (a) 는 bootstrap CI 가 0 을 살짝 포함하는 evidence 강도와 정합하지 않음. (b) 는 본 연구의 *연구 색깔 (robustness-aware methodology)* 과 정합하는 결과를 *숨기는* 결정이 됨. (c) 는 정직한 중간
> - **Limitation:** "tentative finding" 으로 보고하는 경우 후속 연구에서 *재현 검증* 이 필수

### 4.5 한 줄 정리

> *"2024 단면에서 E 공시는 KCGS 와 약한 양, G rhetoric 은 음의 방향을 보였다. 이는 *증명* 이 아니라 *suggestive directional asymmetry* 이며, ESG 가 단일 차원이 아닐 가능성을 *제기* 한다."*

---

## 5. 통합 refinement — Cheap-Talk Claim 의 강도 조정

`06_final_takeaway` 의 4 alpha cheap-talk evidence matrix 는 다음과 같았다.

| Alpha | 결과 | cheap-talk 정합 |
|---|---|---|
| 1 | verbosity-adj 음의 잔여 | 부분 정합 (weak) |
| 2 | 저등급 firm 의 G 어휘 과다 사용 (약 단조) | 부분 정합 |
| 3 | sign reversal sub-sampling 재현 | 정합 (재해석) |
| 4 | governance quartile paradox | 정합 (weak-medium) |

본 refinement 이후의 *조정된 evidence matrix* 는 다음과 같다.

### 5.1 Refined Evidence Matrix

| Alpha | 결과 | refinement 이후 강도 | refinement 이유 |
|---|---|---|---|
| **1** | verbosity-adj 음의 잔여 | **weak (조건부)** | `g_signal_ortho` (verbosity 만 직교화) 잔차는 *0 근방, ns*. r_i (verbosity + FE) 만 약한 음 — 잔차 정의에 *조건부* |
| **2** | 저등급 firm 의 G 어휘 과다 사용 | **weak (D·C 군 표본 부족, 그대로)** | 본 cycle 에서는 변동 없음 |
| **3** | sign reversal sub-sampling 재현 | **weak-medium (이중 해석)** | 표본 확장의 *방향* 이 cheap-talk 정합인 동시에 *large-cap → small-cap verbosity structure shift* 의 산물일 수 있음 |
| **4** | governance quartile paradox | **weak (verbosity 공선성에 종속)** | quartile 정의가 `g_signal_ratio` 에 의존 — 본 ratio 자체의 verbosity 종속성이 quartile 분류에 전이 |
| **5 (new)** | 2024 E(+) vs G(−) asymmetry | **suggestive (CI 0 살짝 포함)** | 새로 드러난 차원. *재현 검증 필요* |

### 5.2 통합 메시지의 refinement

| 06 first-draft 의 통합 메시지 | 08 revised 의 통합 메시지 |
|---|---|
| "4개 alpha 가 모두 cheap-talk 가설과 정합하는 방향을 가리킨다" | "5개 alpha 가 *부분적으로* cheap-talk 가설과 정합하는 방향을 보이지만, 각 alpha 의 evidence 강도가 *feature construction 결정에 종속* 됨. 한 patterns 인 *2024 E-G directional asymmetry* 가 새로 관찰됨" |
| "Cheap-talk 가설과 정합" | "Methodologically fragile but suggestive evidence consistent with disclosure-performance gap hypothesis" |
| "instability 가 finding 이다" | "instability + feature construction sensitivity + directional asymmetry 가 finding 이다" |

### 5.3 본 연구가 *주장하는 것* 의 refinement

> **본 연구가 *주장하는 것*:**
>
> 1. 본 표본의 한국 사업보고서에서 ESG 공시 언어와 KCGS 등급 사이의 단순 연관은 *방향과 강도가 측정 결정에 매우 민감* 하다.
> 2. `g_signal_ratio` 의 KCGS 와의 음의 univariate 연관은 *상당 부분이 `log_tokens` 와의 강한 기계적 얽힘 (r ≈ −0.79) 으로 설명* 된다.
> 3. ESG 관련 ratio · concentration · TF-IDF 변수들이 *서로 r ≈ 0.88 의 강한 공선성* 을 보이므로, 본 데이터의 disclosure intensity 신호는 *세 개의 독립 차원* 이라기보다 *하나의 차원의 세 가지 표현* 일 가능성이 크다.
> 4. 그럼에도 2024 cross-section 에서 *E disclosure (+) vs G rhetoric (−)* 의 directional asymmetry 가 관찰되었으며, 이는 cheap-talk 가설이 *법적 양식이 강한 영역 (G)* 에서 더 강하게 나타날 가능성과 정합한다 — *suggestive 수준* 에서.

> **본 연구가 *주장하지 않는 것*:**
>
> 1. 어느 firm 이 *실제로* cheap-talk 을 하고 있다.
> 2. ESG 언어가 ESG 성과를 예측하거나 향상시킨다.
> 3. cheap-talk 가설을 *증명* 한다.
> 4. 본 표본의 결과를 KOSDAQ · 다른 anchor · 다른 시기로 일반화한다.

---

## 6. 본 연구의 *연구 색깔* refinement

| 차원 | 06 의 framing | 08 의 refined framing |
|---|---|---|
| 연구 종류 | ESG language measurement instability study | **Robustness-aware ESG disclosure methodology study** |
| 핵심 contribution | instability 자체가 finding | instability + feature construction sensitivity + directional asymmetry 가 finding |
| 일반적 ESG NLP 와의 차이 | 더 좋은 ESG predictor 가 아니라 measurement fragility 정량화 | predictor 가 아니라 *measurement fragility 의 reproducible 구조* 를 정량화 + *언어와 성과의 간극의 차원별 비대칭성* 을 제기 |
| 어휘 강도 | "weak / unstable / preprocessing-sensitive" | "weak / unstable / preprocessing-sensitive / feature-construction-sensitive / tentative / suggestive" |
| 발표 가능 한 줄 | "ESG 공시 언어 측정 자체가 분석자의 선택에 흔들린다" | "ESG 공시 언어 측정은 *feature construction 결정* 까지 포함해 분석자의 선택에 흔들리며, 그 흔들림 안에서도 *E vs G 차원의 비대칭성* 같은 substantive 발견이 가능하다" |

---

## 7. 새로 추가된 한계 (Refinement-specific)

기존 `06_final_takeaway` §6 의 한계 표는 그대로 유지된다. 본 §7 은 *refinement cycle 에서 새로 드러난* 한계를 추가한다.

| 새 한계 | 의미 |
|---|---|
| **Feature construction sensitivity** | `g_signal_ratio` 가 `log_tokens` 와 r ≈ −0.79 로 얽혀 있어 *ratio 자체의 정의가 결과의 일부* — 잔차 정의 (verbosity-only vs verbosity + FE) 에 따라 결론 방향이 변동 |
| **Feature redundancy** | `g_signal_ratio` · `esg_signal_ratio` · `esg_tfidf_concentration` 간 r ≈ +0.88 — *세 변수가 같은 disclosure intensity 의 다른 표현* 일 가능성. 본 연구의 "다층 측정" 이 *세 개의 독립 evidence* 라기보다 *하나의 evidence 의 세 가지 표현* 일 수 있음 |
| **Year-specific finding 의 재현 부재** | 2024 E-G asymmetry 가 *단년도* 결과 — 다음 cycle 의 panel 재검증이 필수 |
| **E disclosure feature 의 별도 검증 부재** | 본 cycle 에서 E disclosure 를 *G rhetoric 과 동일한 ratio 구조* 로 측정 — E 만의 독립적 feature engineering 부재 |
| **Bootstrap CI 경계 결과의 해석 합의 부재** | E ↔ KCGS 의 CI = [−0.003, +0.454] — "0 을 살짝 포함" 결과의 보고 표준이 학계에 통일되어 있지 않음. 본 연구는 *suggestive* 어휘로 보고 |
| **Cheap-talk evidence 의 fragility 자체가 finding 인지 selection bias 인지의 경계** | 본 연구는 *모든 결과를 보고* 하는 입장이지만, "fragility 를 finding 으로 본다" 는 framing 자체가 *어떤 결과도 finding 으로 해석할 위험* 을 갖는다 — `07_appendix` B.2.6 의 *circular* 한 측면 |

---

## 8. 발표용 narrative (refined)

### 8.1 시작 (problem statement, 변경 없음)

> "ESG 공시 언어를 어떻게 측정해야 *맞게* 측정한 것인가?"
>
> 우리는 이 질문에 *유일한 정답이 없다* 는 것을 보였다.

### 8.2 중간 — refined version

- 같은 corpus 에서 *preprocessing · tokenizer · 표본 크기* 의 선택이 결론을 흔든다 (4 layer instability)
- 한 단계 더 들어가 보면 — *ratio 변수의 정의 자체* 가 `log_tokens` 와 r ≈ −0.79 로 얽혀 있다 (verbosity confounding)
- ESG 관련 ratio · concentration · TF-IDF 변수들이 r ≈ +0.88 로 강하게 공선 (feature redundancy)
- Orthogonalize 후에는 G 어휘 강도와 KCGS 의 단순 연관이 0 근방으로 약화 (ρ ≈ +0.058, ns)
- 그럼에도 *2024 cross-section 에서 E(+) vs G(−) directional asymmetry* 가 관찰됨 — *suggestive 수준*

### 8.3 끝 — refined version

> 본 표본의 한국 사업보고서에서, ESG 공시 언어와 외부 평가의 연관은 *측정 결정에 매우 민감* 하다. 단순 연관의 방향과 강도는 *분량 효과 · feature 정의 · 표본 크기* 에 따라 흔들리며, 통합 ESG 신호 안에서도 *E 와 G 가 다른 방향* 을 보일 수 있다.
>
> 따라서 본 연구의 evidence 는 *cheap-talk 을 증명* 하지 않는다. 대신 *언어와 성과의 간극이 존재할 수 있다는 가설과 정합* 하면서도, *그 정합의 강도가 어떻게 측정하느냐에 종속* 됨을 정량적으로 기록한다.

### 8.4 끝의 끝 — *주장하지 않는 것* (변경 없음)

- 어느 firm 이 cheap-talk 을 하는지 *말할 수 없다*
- ESG 언어를 *예측 신호로 쓸 수 있다고 권하지 않는다*
- 본 finding 이 KOSDAQ · 다른 anchor · 다른 시기에서도 *유효할지* 알 수 없다

---

## 9. Future work — refinement-specific

| 방향 | 무엇을 검증하는가 |
|---|---|
| **Directly orthogonal feature engineering** | TF-IDF 정규화 · 분량 통제 · 차원 축소 (PCA) 를 결합해 *서로 직교한* disclosure intensity 차원 set 을 설계. 본 연구의 r ≈ 0.88 공선성 문제 해결 |
| **E / S / G 차원의 독립적 feature** | 본 연구의 E · G 가 *같은 ratio 구조* 위에서 측정됨. 차원별로 *다른 정규화 · 다른 seed expansion · 다른 sparsity 처리* 를 적용한 독립 feature engineering |
| **Year-specific cross-section panel** | 2024 E-G asymmetry 를 *다년도 cross-section* 으로 재검증. *어느 해에 어느 방향* 으로 비대칭이 나타나는지 시계열 변동 분석 |
| **Anchor 다양화 + E/S/G 단독 등급** | KCGS 의 *통합 등급* 이 아니라 *E 단독 · G 단독 등급* 과의 연관 검증. MSCI · Sustinvest 등 다중 anchor 정합성 |
| **Verbosity-orthogonal ESG feature** | 분량과 *기계적으로* 얽히지 않는 ESG feature 의 직접 설계 — 예: passage-level semantic similarity (KoBERT) 기반 disclosure intensity |
| **Pre-registration with refined framing** | "instability + feature construction sensitivity + directional asymmetry" 의 사전 등록 — *어떤 결과가 cheap-talk 정합인지* 를 *결과 보기 전에* 결정 |
| **Cheap-talk 의 차원별 강도 비교** | 본 연구의 *suggestive* E-G asymmetry 가 후속 cycle 에서 안정적이라면, 이를 *cheap-talk 의 G-specific 가설* 로 정식화 — 법적 양식 강도 · ritualistic disclosure 정도와의 상관 |

---

## 10. Decision Box · 본 refinement narrative 의 framing 선택

- **Alternative:**
  - (a) cheap-talk 결론을 *유지* 하고 새 결과를 *robustness inset* 으로만 추가
  - (b) cheap-talk 결론을 *기각* 하고 "feature construction sensitivity" 결론만 남김
  - (c) cheap-talk 가설을 *suggestive 수준으로 강도 조정* 하고 E-G asymmetry 를 *새 차원의 evidence* 로 추가
- **Choice:** (c)
- **Justification:**
  - (a) 는 새 결과를 *narrative 본문* 에 통합하지 않아 — 06 의 framing 을 *기계적으로* 방어. *연구 honesty* 와 정합하지 않음
  - (b) 는 cheap-talk 가설 자체를 *너무 강하게 기각* — 본 데이터로는 cheap-talk 의 기각도 *증명* 할 수 없음. evidence asymmetry 가 발생
  - (c) 는 *evidence 의 강도가 정확히 어디까지인지* 를 솔직하게 보여줌 + 새 차원의 흥미로운 발견을 *over-claim 없이* 보고
- **Limitation:** (c) 는 *방어적* 으로 비칠 위험 — 그러나 association-only 데이터 + feature redundancy + small sample 조합에서는 *과주장* 보다 *조심스러운 정합 주장* 이 더 정직

---

## 11. 핵심 메시지 한 줄 (refined)

> **본 연구의 refined finding 은 "ESG 공시 언어 → KCGS 등급" 의 강한 신호가 아니다. 또한 그 신호의 단순 fragility 만도 아니다. *언어와 성과의 간극을 시사하는 음의 방향* 이 — `log_tokens` 와의 r ≈ −0.79 의 기계적 얽힘과 ESG 변수 간 r ≈ +0.88 의 공선성 안에서 — *부분적으로 살아남지만 그 강도는 feature construction 결정에 종속* 된다는 사실이다. 그리고 그 안에서 *2024 단면의 E disclosure (+) vs G rhetoric (−) directional asymmetry* 가 — *suggestive 수준에서* — ESG 의 차원별 disclosure-performance gap 가설을 새롭게 제기한다. 본 연구는 *cheap-talk 을 증명* 하지 않는다. 본 연구는 *cheap-talk 가설이 어디까지 살아남고 어디에서 흔들리는지* 를 *재현 가능한 robustness 구조* 안에서 정직하게 기록한다.**

---

## 12. 본 refinement 의 결론

이 cycle 은 *cheap-talk claim 의 강화* 가 아니라 *evidence 강도의 정직한 재조정* 이었다. 결과적으로 본 연구는 다음으로 진화했다.

- *ESG predictor* 연구 → *measurement instability* 연구 → **robustness-aware methodology** 연구
- *cheap-talk 정합* → **tentative / suggestive cheap-talk consistency**
- *4 alpha multi-angle* → **5 alpha (E-G asymmetry 포함) + 2 refinement layer (orthogonalization · joint regression)**
- *통합 ESG 신호 단일 차원* → **E vs G directional asymmetry 의 차원별 분리**

이 진화 자체가 본 연구의 *연구 색깔* 이다. *어느 결과가 살아남는가* 보다 *어떤 결과가 어떤 조건에서 어떤 강도로 살아남는가* 를 정량적으로 기록하는 것 — 이것이 본 refinement 의 자기 정의다.

---

**산출 파일 (refinement-specific)**

- `data/06_analysis/g_signal_orthogonalized_summary.csv` — `g_signal_ortho` 잔차 + KCGS 단순 ρ
- `data/06_analysis/joint_regression_vif.csv` — 4 변수 동시 투입 VIF + cross-correlations
- `data/06_analysis/joint_regression_summary.csv` — 4 변수 동시 회귀 계수표
- `data/06_analysis/cross_section_2024_e_vs_g.csv` — 2024 단면 E vs G ρ + bootstrap CI
- `data/06_analysis/refined_evidence_matrix.csv` — Alpha 1~5 통합 (refinement 후)
- `ESG_DART_Integrated_Pipeline.ipynb` — refinement 분석 코드 cell 포함

---

**관련 historical 문서**

- `06_final_takeaway_report.md` — first-draft narrative (cheap-talk framing 진화의 출발점, 보존)
- `04_regression_robustness_report.md` — §14 Refinement Addendum 으로 직접 연결
- `05_alpha_analysis_report.md` — §10 Alpha 5 (E-G asymmetry) 로 직접 연결
- `07_appendix_team_and_insight.md` — Insight B.3.5 (verbosity confounding) 로 직접 연결

---

## §13. [2026-05-24 PATCH] Refinement 4 — Stopwords lineage recovery

> 02·03·04 보고서의 patch 절을 통합한 narrative-level summary. §5 (cheap-talk strength refinement) 와 §11 (refined message) 에 대한 영향을 한 절에 정리한다.

### 13.1 발견

`src/preprocessor.py` 가 공식 의존성 `data/stopwords_ko_esg.txt` 를 로드하지 않은 채로 운영되었음 (Notice/03_minimal_analysis_example.md L56 에 명시되어 있던 의존성). 33개 공식 토큰 중 14개만 inline set 과 겹쳤다. 누락된 19개 중 12개 — **강화·개선·계획·구축·목표·성과·실시·제공·지원·추진·확대·활동** — 가 corpus 에 실제로 등장 (나머지 7개는 입자/어미로서 Kiwi 가 형태소 단계에서 제거하므로 corpus 영향 0).

이 12개는 cheap-talk 가설이 *지목* 하는 ESG-행동 어휘 그 자체. 즉 lineage gap 의 *내용물* 이 cheap-talk theory 의 *대상* 이라는 우연한 정합.

### 13.2 영향 (matched-sample N=210, exp_F vs exp_F_official)

| narrative element | 본 보고서 §1-§12 결론 | stopwords 복구 후 |
|---|---|---|
| `g_signal_count` = main robust signal | rho_orth ≈ +0.245*** | rho_orth ≈ +0.247*** ✓ 유지 |
| `g_signal_ratio` orthogonalize 후 ns | rho_orth ≈ +0.059 ns | rho_orth ≈ +0.056 ns ✓ 유지 |
| suppressor (esg_g_relative ↔ bp_contamination) | ±0.250*** | ±0.250*** ✓ 유지 |
| §5 의 "joint regression: ESG 변수 r ≈ 0.88" redundancy 가설 | 본 §15.3 (04 보고서) 에서 강화 |  |
| `esg_tfidf_concentration` 의 보조적 음의 상관 | ρ = −0.175** | ρ = −0.007 ns ⚠ **artifact 로 강등** |

→ **본 §1-§12 의 refined cheap-talk narrative 는 stopwords 복구 후에도 방향성·강도 모두 유지된다**. 단 한 가지 변화: 보조 feature `esg_tfidf_concentration` 의 이전 음의 상관이 cheap-talk 동사 saturation 의 verbosity-mediated artifact 였음이 드러남.

### 13.3 narrative 강화 (약화 아님)

이 patch 는 cheap-talk claim 을 **강화** 한다. 이유:

1. Lineage bug 의 *내용물* 자체가 cheap-talk theory 가 지목하는 어휘였다 — 우연이라기보다 ESG-strategic-communication 의 lexicon 이 한국어 disclosure 에서 12개 동사로 수렴함의 증거.
2. 보조 feature 가 *그 동사들에 mediate 되어 음의 상관을 보였다* 는 사실은 — **measurement 가 cheap-talk artifact 를 포착하고 있었다** 는 의미. cheap-talk 가설의 통계적 흔적이 의도하지 않은 곳에서 발견된 것.
3. 본 보고서 §13 (refined one-liner) 의 *"본 데이터에서 ESG 언어와 KCGS 등급의 정합은 *조건적·약하다·feature-construction 종속적*"* 진술과 정확히 일치 — feature construction 의 한 단계 (stopwords) 가 보조 feature 의 부호를 결정한다는 본 patch 의 finding 은 그 진술의 *직접적 예시*.

### 13.4 instability-as-finding 의 확장

§7 (refinement-specific 한계) 에 다음 항목을 추가한다:

> "**Preprocessing dependency lineage limitation.** 본 연구의 inline-hardcoded stopwords set 은 공식 문서가 명시한 dependency 와 14/33 토큰만 겹쳤다. 이 lineage gap 은 한 보조 feature 의 결과에 binary 영향을 미쳤다. ESG disclosure 연구가 *robustness layer* 와 *공식 의존성 audit trail* 을 동시에 갖춰야 reproducibility 가 보장됨을 보여주는 *methodological lesson learned*."

### 13.5 §11 의 refined one-liner — 변경 여부

§11 의 한 줄을 다시 옮긴다:

> *"본 연구는 한국 사업보고서의 ESG 언어가 외부 ESG 평가와 단순 정합하지 않을 수 있다는 가설을 — 표본·전처리·feature 정의·모형 선택의 **각 단계가 신호의 방향과 강도를 결정하는** condition-dependent evidence 로 — 정직하게 측정·보고하고, 그 instability 자체를 cheap-talk 와 robustness layer 가설의 보조 증거로 해석한다."*

**변경 없음.** 본 §13 (patch) 는 이 한 줄을 그대로 두고, 그 한 줄의 *"전처리"* 가 *공식 stopwords 의존성 정합 수준* 까지 포함됨을 추가 evidence 로 명시한다.

### 13.6 산출 파일

- `data/04_preprocessed/recovery/tokenized_exp_F_official.csv` + `stopwords_recovery_diagnostics.json`
- `data/05_features/recovery/features_exp_F_official.csv` / `merged_exp_F_official.parquet`
- `data/05_features/recovery/stopwords_delta_spearman.csv` / `feature_means_delta.csv` / `verbosity_orth_delta.csv` / `bootstrap_ci_before_after.csv` / `sign_stability_before_after.csv`
- `outputs/recovery/COMPARISON_30_stage4_robustness_layer.html` — full visual dashboard
- patched source: `src/preprocessor.py` — `STOPWORDS_OFFICIAL`, `STOPWORDS_EXTENDED_PLUS_OFFICIAL`, `load_official_stopwords()`, `get_stopword_set()`, `exp_F_official` config
- 02·03·04 보고서의 patch 절: §9 / §11 / §15

---

## §13. [2026-05-24 PATCH] Refinement 4 — Stopwords lineage recovery

> 02·03·04 보고서의 patch 절을 통합한 narrative-level summary. §5 (cheap-talk strength refinement) 와 §11 (refined message) 에 대한 영향을 한 절에 정리한다.

### 13.1 발견

`src/preprocessor.py` 가 공식 의존성 `data/stopwords_ko_esg.txt` 를 로드하지 않은 채로 운영되었음 (Notice/03_minimal_analysis_example.md L56 에 명시되어 있던 의존성). 33개 공식 토큰 중 14개만 inline set 과 겹쳤다. 누락된 19개 중 12개 — **강화·개선·계획·구축·목표·성과·실시·제공·지원·추진·확대·활동** — 가 corpus 에 실제로 등장 (나머지 7개는 입자/어미로서 Kiwi 가 형태소 단계에서 제거하므로 corpus 영향 0).

이 12개는 cheap-talk 가설이 *지목* 하는 ESG-행동 어휘 그 자체. 즉 lineage gap 의 *내용물* 이 cheap-talk theory 의 *대상* 이라는 우연한 정합.

### 13.2 영향 (matched-sample N=210, exp_F vs exp_F_official)

| narrative element | 본 보고서 §1-§12 결론 | stopwords 복구 후 |
|---|---|---|
| `g_signal_count` = main robust signal | rho_orth ≈ +0.245*** | rho_orth ≈ +0.247*** ✓ 유지 |
| `g_signal_ratio` orthogonalize 후 ns | rho_orth ≈ +0.059 ns | rho_orth ≈ +0.056 ns ✓ 유지 |
| suppressor (esg_g_relative ↔ bp_contamination) | ±0.250*** | ±0.250*** ✓ 유지 |
| §5 의 "joint regression: ESG 변수 r ≈ 0.88" redundancy 가설 | 본 §15.3 (04 보고서) 에서 강화 |  |
| `esg_tfidf_concentration` 의 보조적 음의 상관 | ρ = −0.175** | ρ = −0.007 ns ⚠ **artifact 로 강등** |

→ **본 §1-§12 의 refined cheap-talk narrative 는 stopwords 복구 후에도 방향성·강도 모두 유지된다**. 단 한 가지 변화: 보조 feature `esg_tfidf_concentration` 의 이전 음의 상관이 cheap-talk 동사 saturation 의 verbosity-mediated artifact 였음이 드러남.

### 13.3 narrative 강화 (약화 아님)

이 patch 는 cheap-talk claim 을 **강화** 한다. 이유:

1. Lineage bug 의 *내용물* 자체가 cheap-talk theory 가 지목하는 어휘였다 — 우연이라기보다 ESG-strategic-communication 의 lexicon 이 한국어 disclosure 에서 12개 동사로 수렴함의 증거.
2. 보조 feature 가 *그 동사들에 mediate 되어 음의 상관을 보였다* 는 사실은 — **measurement 가 cheap-talk artifact 를 포착하고 있었다** 는 의미. cheap-talk 가설의 통계적 흔적이 의도하지 않은 곳에서 발견된 것.
3. 본 보고서 §11 (refined one-liner) 의 *"feature-construction 종속적"* 진술과 정확히 일치 — feature construction 의 한 단계 (stopwords) 가 보조 feature 의 부호를 결정한다는 본 patch 의 finding 은 그 진술의 *직접적 예시*.

### 13.4 instability-as-finding 의 확장

§7 (refinement-specific 한계) 에 다음 항목을 추가한다:

> "**Preprocessing dependency lineage limitation.** 본 연구의 inline-hardcoded stopwords set 은 공식 문서가 명시한 dependency 와 14/33 토큰만 겹쳤다. 이 lineage gap 은 한 보조 feature 의 결과에 binary 영향을 미쳤다. ESG disclosure 연구가 *robustness layer* 와 *공식 의존성 audit trail* 을 동시에 갖춰야 reproducibility 가 보장됨을 보여주는 *methodological lesson learned*."

### 13.5 §11 의 refined one-liner — 변경 여부

§11 의 한 줄을 다시 옮긴다:

> *"본 연구는 한국 사업보고서의 ESG 언어가 외부 ESG 평가와 단순 정합하지 않을 수 있다는 가설을 — 표본·전처리·feature 정의·모형 선택의 **각 단계가 신호의 방향과 강도를 결정하는** condition-dependent evidence 로 — 정직하게 측정·보고하고, 그 instability 자체를 cheap-talk 와 robustness layer 가설의 보조 증거로 해석한다."*

**변경 없음.** 본 §13 (patch) 는 이 한 줄을 그대로 두고, 그 한 줄의 *"전처리"* 가 *공식 stopwords 의존성 정합 수준* 까지 포함됨을 추가 evidence 로 명시한다.

### 13.6 산출 파일

- `data/04_preprocessed/recovery/tokenized_exp_F_official.csv` + `stopwords_recovery_diagnostics.json`
- `data/05_features/recovery/features_exp_F_official.csv` / `merged_exp_F_official.parquet`
- `data/05_features/recovery/stopwords_delta_spearman.csv` / `feature_means_delta.csv` / `verbosity_orth_delta.csv` / `bootstrap_ci_before_after.csv` / `sign_stability_before_after.csv`
- `outputs/recovery/COMPARISON_30_stage4_robustness_layer.html` — full visual dashboard
- patched source: `src/preprocessor.py` — `STOPWORDS_OFFICIAL`, `STOPWORDS_EXTENDED_PLUS_OFFICIAL`, `load_official_stopwords()`, `get_stopword_set()`, `exp_F_official` config
- 02·03·04 보고서의 patch 절: §9 / §11 / §15
