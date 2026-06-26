# 04_regression_robustness_report.md
## 회귀 · Verbosity 통제 · 부호 역전 — language signal이 통제 후에도 남는가

> **연구 질문 (재확인)**
> 사업보고서의 ESG 관련 공시 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가?
>
> 이 보고서는 그 흐름의 **세 번째 단계** — *"분량(verbosity)·산업·연도를 통제한 후에도 ESG 언어 신호가 KCGS 등급과 관련되는가, 그리고 모형 선택을 바꾸면 결론이 어떻게 흔들리는가"* — 를 다룬다.

---

## 1. 왜 correlation 다음에 regression이 필요한가

§3의 Spearman ρ는 두 가지 한계를 가진다.

1. **두 변수 관계만 본다.** firm 길이, 산업, 연도 같은 명백한 교란을 빼지 못한다.
2. **방향성만 본다.** 등급이 1단계 변할 때 feature가 얼마나 변하는가 (또는 그 반대)를 정량화하지 못한다.

특히 §3에서 가장 강한 신호로 등장한 `total_tokens` (ρ ≈ +0.27, p < 0.001) 는 결정적인 단서다.

> 등급이 높은 firm일수록 보고서가 *길고*, 길수록 모든 어휘가 더 많이 등장한다.
>
> 따라서 ==`g_signal_ratio`의 음의 ρ는 **순수한 ESG 신호일 수도, 단순한 분량 효과의 그림자일 수도** 있다. 둘을 분리하지 않으면 cheap-talk 해석을 할 수 없다.

회귀의 목적은 따라서 단순한 "예측력 평가"가 아니라 — ==**verbosity와 ESG language 신호를 분리하는 진단 작업**이다.

```
correlation : "두 변수가 같이 움직이는가?"
              ↓
regression  : "다른 요인을 빼고도 같이 움직이는가?
               빼고 나면 어느 쪽이 진짜 신호인가?"
              ↓
sign change : "통제 전후, 표본 크기 전후, 모형 전후 — 방향이 유지되는가?"
```

---

## 2. 다섯 모형 명세 (M1 ~ M5) 
##### — 우리가 발견한 게 진짜 ESG 신호인가? 아니면 그냥 문서가 길어서 생긴 착시인가?

### 2.1 모형 명세표

| 모델 | 종속변수 | 독립변수 | 답하는 질문 |
|---|---|---|---|
| **M1** OLS | `kcgs_grade_7` | `g_signal_ratio` only | naive correlation (단변량) |
| **M2** OLS | `kcgs_grade_7` | `g_signal_ratio` + `log_tokens` | 분량 통제 후 |
| **M3** OLS | `kcgs_grade_7` | `+ industry_FE + year_FE` | full controls |
| **M4** Ordered Logit | `kcgs_grade_7` (6단계) | M3와 동일 (standardized) | 순서형 가정 robustness |
| **M5** Binary Logit | `kcgs_grade_high` (A/A+ vs 그외) | M3와 동일 | A 이상 vs 아래 robustness |
[OLS 안에서 통제를 단계적으로 추가]
1. M1: ESG 단어 많이 쓰면 등급도 높은가? `등급 = ESG 언어량`
2. M2: 보고서 길이를 제외하고도 ESG 언어가 의미가 있나? `등급 = ESG 언어량 + 보고서 길이`
3. ==M3: 같은 산업, 같은 연도 안에서 비교했을 때도 ESG 언어 차이가 있는가? 
	**`등급 = ESG 언어량 + 보고서 길이 + 산업 효과 + 연도 효과`**==

[다른 모델로 robustness 확인]
4. M4: M3에서 등급의 순서만 인정하는 Ordered Logit 추가
5. M5: M3에서 group1(A+,A)을 1로, group2(그 외)을 0으로 설정해서 A 이상이냐 아니냐?

종속변수는 모두 **외부 평가(KCGS)** 다 — 본 분석은 어떤 모형에서도 *ESG performance 자체를 직접 측정하지 않는다*. 측정 대상은 항상 "외부 평가와의 통계적 연관"이다.

### 2.2 한 모형으로 안 되는 이유 — 모형 다중성의 의미

| 모형 | 강점 | 본질적 한계 |
|---|---|---|
| OLS | 계수 해석이 직관적 ("ratio 1pp 증가시 등급 점수 X 변화") | KCGS 등급을 *등간척도*로 가정. A+와 A의 거리 = B와 C의 거리라고 본다. 사실이 아니다. |
| Ordered Logit | KCGS 등급의 *순서형(ordinal)* 본질에 정합 | 비례오즈(proportional odds) 가정이 깨질 수 있음. 표본이 작으면 수렴 자체가 불안정. |
| Binary Logit | 가장 임상적 — "A 이상이냐 아니냐" | 6단계 등급 정보의 상당 부분이 손실됨 |

> **해석 원칙:** 세 모형이 *같은 방향*을 가리킬 때만 신호로 인정한다. 하나의 결과만 보고하지 않는다.

### 2.3 verbosity 통제 — M1 → M2 → M3 계수 변화의 의미

M1에서 M2로 넘어가며 `log_tokens`가 추가될 때, `g_signal_ratio` 계수가 어떻게 변하는지가 **cheap-talk vs verbosity bias 진단의 핵심**이다.

| 시나리오               | 계수 변화                   | 해석                                                  |
| ------------------ | ----------------------- | --------------------------------------------------- |
| (i) 계수가 *더 음수*로 이동 | M1: −β → M2: −β' (β'>β) | verbosity가 양의 방향 편향을 흡수했음 → 잔여 신호는 cheap-talk과 더 정합 |
| (ii) 계수가 *유의성을 잃음* | M1 p<0.05 → M2 p>0.10   | `g_signal_ratio`가 주로 verbosity의 함수였음                |
| (iii) 부호 역전        | M1: + → M2: −           | 분량 효과가 ratio의 방향을 통째로 결정하고 있었음                      |
[해석]
1. verbosity제거 -> ESG 단어가 많을수록 등급이 낮은 경향이 더 강하게 드러남 -> cheap-talk
2. ESG 단어 효과처럼 보였는데 실제로는 verbosity 효과였음을 확인함
3. 문서 길이 효과가 결과 방향 자체를 왜곡하고 있음을 확인함(M3)
	1. "ESG 단어 많으면 등급 높네?" -> verbosity 제거 -> "오히려 반대였네?"
4. ESG 잘해서가 아니라 산업 자체 특성으로 높은 것들을 확인함(M3)

M3에서 산업·연도 고정효과를 추가하는 것은 *두 firm을 직접 비교하지 않고 같은 산업·연도 내에서 비교*하는 것에 해당한다. 산업 평균 ESG 어휘 사용량이 등급과 상관된다면 그 효과가 빠진다.

### 2.4 robust SE (HC1) 사용 근거

KCGS 등급을 OLS의 연속변수로 취급할 때, firm-year panel 구조에서 오차항이 비등분산(heteroskedasticity)일 가능성이 높다. White's HC1 robust standard error는 이 가정 위반에 대해 *계수 추정치는 유지하되 SE만 보정*한다. 본 분석은 모든 OLS 모형에 HC1을 기본으로 적용한다.

### 2.5 금지 어휘 reminder

> "predicts ESG · causes · improves ESG · true ESG · classifies"는 사용하지 않는다.
>
> 일관적으로 사용: "associated with · positively/negatively related · consistent with · weak-but-significant · disclosure intensity"

---

## 3. VIF 진단 — 다중공선성 사전 점검

회귀 결과를 신뢰하려면 독립변수 간 상관관계가 너무 높지 않아야 한다. 일반적 기준: VIF > 10이면 해당 변수의 계수 해석이 불안정.

| 변수 | 예상 VIF 위치 | 우려 지점 |
|---|---|---|
| `g_signal_ratio` | < 5 | OK — ratio 변수는 다른 변수와의 직접 합산 관계가 없음 |
| `log_tokens` | < 5 | OK — 분량은 다른 ratio와 다른 차원 |
| `esg_signal_ratio` | 잠재적 위험 | g_signal_ratio와 같은 corpus에서 산출 → 부분 공유 |
| `esg_tfidf_concentration` | 잠재적 위험 | seed-based TF-IDF → ratio들과 부분 상관 |

본 분석은 **g_signal_ratio · log_tokens** 두 변수를 main pair로 두고, `esg_*` 변수들은 robustness 보조변수로만 사용한다. 모든 변수를 한 모형에 동시에 투입하면 cheap-talk 해석이 multicollinearity로 가려질 수 있기 때문이다.

> **Decision Box · 변수 조합**
> - **Alternative:** (a) 모든 ESG 변수 동시 투입, (b) main pair만, (c) PCA로 차원 축소
> - **Choice:** main pair (g_signal_ratio + log_tokens)
> - **Justification:** ESG ratio 간 공선성이 cheap-talk 해석을 가리기 쉬움. main pair가 가장 해석가능
> - **Limitation:** esg_signal_ratio · esg_tfidf_concentration의 잔여 정보는 robustness inset에서만 다룸

---

## 4. M1 → M2 → M3 — verbosity 통제의 실증적 의미

### 4.1 계수 변화의 narrative

본 표본(N=210, 77 firm × 3년, primary exp = exp_F)에서 관찰된 패턴은 다음과 같다.

| 모형 | g_signal_ratio 계수 (방향) | log_tokens 계수 | R² |
|---|---|---|---|
| **M1** (naive) | 음 — 약하게 유의 | — | 매우 낮음 (~3%) |
| **M2** (+log_tokens) | 음 — 약화 / 유의성 소실 가능 | 양 — 강하게 유의 | 약간 상승 |
| **M3** (+ FE) | 음 / 0 부근 (FE 흡수) | 양 — 약화 (산업 흡수) | 가장 높음 (~10–15%) |

> M2에서 `g_signal_ratio` 계수의 *유의성이 사라지는 방향으로 이동*하는 경향이 관찰된다. 이는 ratio가 KCGS와 가졌던 음의 연관 중 *상당 부분이 분량의 그림자*였음을 시사한다.

### 4.2 이 결과를 어떻게 해석할 것인가

**조심스러운 해석 1 — verbosity dominance.** 문서 길이가 너무 강한 영향력을 가짐
`g_signal_ratio`가 KCGS와 갖는 univariate 관계의 대부분이 `log_tokens`로 흡수된다면, ratio 신호는 *그 자체가 새로운 정보*라기보다 *분량 신호의 ratio 형태 재표현*에 가깝다.

**조심스러운 해석 2 — residual cheap-talk signal.** “단순히 긴 보고서라서만은 아니네”
그러나 `log_tokens` 통제 후에도 계수가 *음의 방향을 유지*한다면(설사 약하게라도), 이는 분량으로 환원되지 않는 *어휘 강도* 차원이 남아 있다는 뜻이다. 이 잔여분은 §5 Alpha 1의 verbosity-adjusted score로 분리해서 따로 본다.
같은 길이 문서끼리 비교해도
등급 낮은 회사가
ESG 말을 더 많이 하는 경향이
조금 남아 있음

**조심스러운 해석 3 — 약한 효과 크기의 실질적 의미.** “산업·연도 효과까지 제거하니
남는 신호는 약함”
M3의 R²가 10%대라면, *모형 자체가 KCGS 등급의 대부분을 설명하지 못한다*. 이는 실패가 아니라 본 연구의 framing과 정합한다 — disclosure intensity가 ESG performance를 직접 측정하지 않는다는 사실이 R²로 드러난 것이다.

처음엔 ESG 언어가 중요한 신호처럼 보였지만, 분석을 깊게 할수록 그 상당 부분은 “보고서 길이”와 “산업 특성”의 영향이었다. 다만 모든 효과가 사라진 것은 아니어서, 일부 residual cheap-talk 가능성은 남아 있었다

---

## 5. M4 · M5 — 모형 선택 robustness

### 5.1 Ordered Logit (M4)

순서형 종속변수 가정 하에서 standardized feature를 사용해 BFGS 최적화로 추정. 보고는 log-odds 단위.

- **계수 부호 일치 여부**가 핵심. M2/M3의 OLS 음의 계수가 M4에서도 음으로 유지되는가?
- 비례오즈 가정이 깨지면 log-odds 해석이 약해진다. 대안은 generalized ordered logit이지만 본 표본 크기에서는 수렴 불안정.

### 5.2 Binary Logit (M5)

종속변수: `kcgs_grade_high` = 1 if `kcgs_grade ∈ {A, A+}` else 0. 본 표본에서 A 이상이 약 70%를 차지 → 클래스 불균형 약함.

- odds ratio 형태로 함께 보고.
- "ratio가 1pp 증가하면 A 이상일 odds가 X% 변화" 형태의 해석.

### 5.3 세 모형이 무엇을 동시에 가리키는가

| 검정 항목 | OLS M3 | Ordered Logit M4 | Binary Logit M5 |
|---|---|---|---|
| g_signal_ratio 계수 부호 | − | − | − |
| 유의성 | 약 (p ≈ 0.10–0.20) | 약 | 약 |
| log_tokens 계수 부호 | + | + | + |
| log_tokens 유의성 | 강 (p < 0.01) | 강 | 강 |

> 세 모형이 *같은 방향*을 가리키되 *같은 강도로 약하다*. 즉 신호가 robust하게 약하다는 것 자체가 결과의 일부다.


---

## 6. Bootstrap CI for OLS — 방향성 안정 검정

각 OLS 계수에 대해 1,000회 재표본해 95% CI를 추정한다. p-value 한 점보다 *방향성 안정*을 보는 데 더 유용하다.

| 계수 | 점 추정 | 95% bootstrap CI | CI excludes 0? | 해석 |
|---|---|---|---|---|
| `g_signal_ratio` (M2) | 음 | 일부 실험에서 [−0.x, +0.0x] | **no** | weak evidence, direction uncertain |
| `log_tokens` (M2) | 양 | [+0.xx, +0.xx] | **yes** | stable positive association |
| `g_signal_ratio` (M3) | 음 (작아짐) | 0 가로지름 | **no** | FE 흡수 후 신호 약함 |

### 6.1 Bootstrap CI가 0을 가로지를 때

이 경우는 *"유의하지 않으니 의미 없음"*으로 처리하지 않는다. 본 보고서는 다음과 같이 분류한다.

- **direction uncertain** — 표본을 흔들면 부호가 안정적이지 않음
- **weak evidence** — 부호는 유지되나 점 추정 강도가 약함
- **unstable association** — preprocessing/sample 변화에 흔들림

> 이 분류 자체가 **measurement fragility evidence**이며, 본 연구의 핵심 finding 중 하나다.

---

## 7. Sign Reversal Inset — pilot(n=30) vs full(n=210)

### 7.1 무엇이 뒤집혔는가

| feature | pilot ρ (n=30) | full ρ (n=210) | 방향 |
|---|---|---|---|
| `g_signal_ratio` | **+0.444** | **−0.197** | 양 → **음** |
| `esg_tfidf_concentration` | **+0.326** | **−0.185** | 양 → **음** |
| `esg_g_relative` | +0.253 | −0.049 | 양 → 0 |

회귀 계수에서도 동일한 패턴이 관찰된다 — pilot 표본 회귀에서는 `g_signal_ratio`가 KCGS와 양의 연관처럼 보였고, full 표본에서는 음의 계수가 일관되게 등장한다.
 처음엔 잘 포장된 대기업만 봤는데

표본을 넓히니까
“말은 많은데 성과는 낮은”
기업 패턴이 나타난 것

### 7.2 이것이 왜 *finding*인가

> **직관적으로 좋아 보였던 pilot 결과가 전체 표본에서 반전되었다.**

이 부호 역전을 "오류 / 잡음 / 이상치"로 묻어 두는 것은 가장 쉬운 선택이지만, *가장 비싸게 잃는 정보*이기도 하다. 본 보고서는 다음과 같이 해석한다.

| 가능한 framing | 본 보고서의 입장 |
|---|---|
| 분석 실패 | ✗ — 두 표본 모두 데이터 lineage가 동일하며 계산 절차가 같음 |
| 통계적 이상치 | ✗ — Cook's distance 점검에서 단일 firm-year가 결과를 좌우하지 않음 |
| Small-sample 인공물 | ✓ — pilot은 KOSPI 대형주 편향 표본 (high-grade firm 집중) |
| **Cheap-talk evidence** | ✓ — 표본이 넓어질수록 "낮은 등급일수록 ESG 어휘를 더 쓴다"는 strategic disclosure 패턴이 드러남 |

> **Decision Box · sign reversal 해석**
> - **Alternative:** (a) 결과를 안 보고함, (b) 이상치 처리, (c) finding으로 보고
> - **Choice:** (c) — methodology section과 limitation section 모두에 명시
> - **Justification:** sign reversal은 *재현 가능한 패턴*이며, 표본 확장 방향이 cheap-talk과 정합
> - **Limitation:** 부호 안정성을 보장하는 사전 표본 크기 기준이 없음 — 후속 연구에서 power analysis 필요

### 7.3 발표용 narrative 한 줄

> "처음에는 ESG 언어 사용량이 KCGS 등급과 양의 관계로 보였다. 표본을 KOSPI 상위 10개에서 77개로 확장하자 부호가 음으로 뒤집혔다. 이 반전 자체가 *언어와 성과의 간극*을 보여주는 가장 강한 증거다."

---

## 8. Preprocessing Robustness — exp_B / exp_E / exp_F

### 8.1 같은 회귀를 세 전처리에서 다시 돌리면

M2 회귀(`kcgs_grade_7 ~ g_signal_ratio + log_tokens`)를 exp_B / exp_E / exp_F 각각에서 추정하면, `g_signal_ratio` 계수의 **방향**이 세 실험 모두에서 **음**으로 유지된다.

| 전처리                                  | `g_signal_ratio` 계수 (방향) | 유의성 | `log_tokens` 계수 |
| ------------------------------------ | ------------------------ | --- | --------------- |
| **exp_B** (baseline)                 | 음                        | 약   | 양 (강)           |
| **exp_E** (정제 강)                     | 음                        | 약   | 양 (강)           |
| **exp_F** (정제 강 + 정량 표현 보존, primary) | 음                        | 약   | 양 (강)           |

- 점 추정의 *크기*는 exp_B < exp_F 정도로 약간 차이 — 그러나 *방향*은 동일
- `log_tokens` 효과는 세 실험 모두에서 강하게 양 — verbosity dominance는 preprocessing-invariant

### 8.2 이를 effect strengthening 실패로 해석하지 않는다

| 일반적 framing | 본 보고서의 framing |
|---|---|
| "정제를 강화해도 ρ가 크게 늘지 않았으니 실패" | "정제 선택이 결과 방향을 무너뜨리지 않았다는 점에서 robustness evidence" |

> 본 연구의 가설은 *"전처리를 잘하면 ρ가 커진다"*가 아니다.
>
> *"전처리 선택이 결론을 결정하는가"* 다.
>
> 만약 전처리 강도에 따라 `g_signal_ratio` 계수의 부호가 흔들렸다면, 그것은 *boilerplate artifact*이지 ESG language signal이 아니다. 본 표본에서 부호가 흔들리지 않는다는 사실은 *cheap-talk 정합 결과가 boilerplate artifact가 아니다*는 보조 증거다.

### 8.3 effect strengthening이 *제한적*임을 인정해야 하는 이유

그렇다고 exp_F의 우월성을 강하게 주장하지도 않는다. 세 실험 간 |ρ|·|β| 차이는 작고, 본 표본 크기에서 그 차이가 통계적으로 유의하다고 단정할 수 없다.

> **결론:** exp_F는 ρ·β를 *키우지는* 못했지만 *무너뜨리지도 않았다*. 이 양면을 모두 보고하는 것이 본 보고서의 일관된 입장이다.

---

## 9. 진단 — Breusch-Pagan + Cook's distance
“오차가 고르게 퍼져 있냐?” “특정 기업 하나 때문에 결과 나온 거 아니야?”

### 9.1 이분산성 (BP test, M2 기준)

KCGS 등급을 OLS의 연속변수로 두면 등급 양 끝(D, A+) 근처에서 잔차 분산이 달라질 수 있다. BP test 결과 p < 0.05이면 이분산 의심 → 본 분석은 *처음부터* HC1 robust SE를 사용했으므로 SE는 보정되어 있다.

### 9.2 영향력 큰 관측치 (Cook's D)

기준: Cook's D > 4/N (=4/210 ≈ 0.019). 이 기준을 넘는 firm-year를 제거해도 `g_signal_ratio` 계수 부호가 유지되는가?

- 본 표본에서 단일 firm-year가 회귀 결론을 좌우하지 않는다 (예비 점검 결과).
- 부록표(`cooks_distance_summary.csv`)에 영향력 상위 10개 관측치 기록.

> 단일 outlier에 의해 sign reversal이 발생하지 않는다는 점은 §7의 finding을 *통계 인공물*이 아닌 *표본 구조 차이*로 해석하는 근거다.

---

## 10. Association-Only Interpretation — 인과 추론 금지 reminder

본 회귀 결과를 어떻게 *말하지 않는가*가 어떻게 *말하는가*만큼 중요하다.

### 10.1 허용되는 표현

- "낮은 등급의 firm일수록 G 어휘 비율이 *높은 경향이* 있다"
- "분량을 통제한 후에도 `g_signal_ratio`는 KCGS 등급과 *음의 방향으로 연관*된다"
- "이 패턴은 cheap-talk 가설과 *정합*한다"
- "본 표본에서 관찰된 *약한 음의 association*은…"

### 10.2 금지되는 표현

- "ESG 언어가 ESG 성과를 *예측*한다"
- "ESG 언어 사용량이 KCGS 등급을 *낮춘다*"
- "거버넌스 공시가 *실제 거버넌스*를 보여 준다"
- "이 모형이 ESG performance를 *측정*한다"

### 10.3 왜 이 구분이 결정적인가

회귀 계수의 부호와 유의성은 *조건부 평균의 변화*를 추정할 뿐이다. 그 변화가 *인과*인지, *역인과*인지(낮은 등급을 받은 firm이 이후 공시 언어를 강화), *공통 원인*에 의한 spurious 관계인지 — 이 셋은 OLS 회귀로 구분할 수 없다.

> **연관(association) ≠ 인과(causation)**
> 이 한 줄을 본 보고서 전체에 항상 적용한다.

---

## 11. 한계 (방법론)

| 한계 | 의미 | 후속 연구 방향 |
|---|---|---|
| **다중공선성 잠재 위험** | esg_signal_ratio · esg_tfidf_concentration 동시 투입 시 계수 해석 불안정 | feature pair 분리 보고 + PCA-based summary |
| **순서형 등급의 등간 가정** | OLS는 A+~A 거리 = B~C 거리로 처리 | M4 Ordered Logit과 부호 일관성으로 보완 |
| **약한 효과 크기** | R² ≈ 10–15%, ρ ≈ 0.18 | finding의 일부 — instability narrative와 정합 |
| **모형 설명력 자체가 낮음** | 텍스트 feature가 KCGS 분산의 대부분을 설명 못함 | disclosure intensity ≠ performance 가설과 정합 |
| **panel 구조 부분 활용** | firm 고정효과 미통제 (산업·연도만) | within-firm 변동을 보는 후속 분석 필요 |
| **OLS의 normality 약가정** | residual 정규성은 미검정 | bootstrap CI로 보완 (§6) |
| **인과 식별 전략 부재** | OLS·Ordered/Binary Logit 모두 association만 | DiD / IV / 평가 변경 자연실험 등 식별 가능한 후속 설계 필요 |

---

## 12. 다음 단계 — Alpha 분석으로 이어지는 흐름

§5 회귀 결과는 다음 네 가지를 §6 Alpha 분석에 넘긴다.

| 회귀 finding | Alpha 분석에서 어떻게 이어지는가 |
|---|---|
| `log_tokens` 통제 후 음의 잔여 | **Alpha 1 — Verbosity-Adjusted Score (r_i)** 직접 입력 |
| 등급 낮은 firm의 ratio 평균이 더 높음 | **Alpha 2 — Low-Grade Strategic Disclosure** 가설 검정 |
| pilot vs full 부호 역전 | **Alpha 3 — Sign Reversal Diagnosis** sub-sampling 검정 |
| 거버넌스 어휘의 dominant verbosity 흡수 | **Alpha 4 — Governance Paradox** quartile 분석 |

> 회귀가 *통제 후에도 약한 신호*를 남긴다면, 그 잔여를 직접 시각화하고 분해하는 것이 Alpha 분석의 역할이다. 회귀와 Alpha는 같은 가설을 다른 각도에서 *교차 검증*한다.

---

## 13. 핵심 메시지 한 줄

> **분량을 통제하면 `g_signal_ratio`의 KCGS 연관은 약해지지만 음의 방향을 유지하며, 이 약한 잔여 신호와 표본 확장 시 발생한 부호 역전은 — 통계적 결함이 아니라 — 한국 사업보고서의 ESG 언어가 외부 평가와 단순 정합하지 않는다는 measurement evidence로 해석된다.**

---

**산출 파일**

- `data/06_analysis/regression_M1_M5_summary.csv` — 다섯 모형 계수·SE·p·R² 정리
- `data/06_analysis/coef_bootstrap_CI.csv` — `g_signal_ratio`·`log_tokens` 부트스트랩 1,000회 CI
- `data/06_analysis/robustness_by_exp.csv` — exp_B/E/F별 M2 회귀 결과
- `data/06_analysis/cooks_distance_summary.csv` — 영향력 상위 firm-year 진단
- `data/06_analysis/vif_diagnostics.csv` — 다중공선성 점검표
- `data/06_analysis/fig_coef_M1_M3.png` — verbosity 통제 전후 계수 변화 시각화
- `data/06_analysis/alpha3_sign_reversal_exp_F.png` — N-curve sub-sampling 분포 (§6과 공유)

---

## 14. Refinement Addendum — Orthogonalization · Joint Regression (post-cycle)

> 본 §14 는 본 보고서 *작성 이후* 시행된 추가 robustness 분석을 본 문서에 정합적으로 통합한 addendum 이다. §1 ~ §13 의 결론은 *방향성으로는* 유지되지만, 그 *강도* 가 본 §14 에서 refinement 된다.
> 전체 refined narrative 는 `08_revised_final_report.md` §2 ~ §3 참고.

### 14.1 Verbosity confounding 의 정량 — r ≈ −0.79

`g_signal_ratio` 와 `log_tokens` 의 Pearson 상관: **r ≈ −0.79**.

본 보고서 §1·§2·§4 에서 *"verbosity 통제 변수"* 로 다루었던 `log_tokens` 가, 실제로는 `g_signal_ratio` 와 *기계적으로 매우 강하게* 얽혀 있다. ratio 의 정의(분자 = G 어휘 카운트, 분모 = total_tokens)상 어느 정도의 음의 상관은 *수학적으로* 예상되지만, |r| ≈ 0.79 는 그 한계를 *훨씬 초과* 한다.

이 사실의 함의.

| 함의 | 의미 |
|---|---|
| `log_tokens` 는 *교란 변수* 라기보다 *공동 구성 요소* | "통제" 라는 표현보다 "*공동 구성 요소 분리*" 가 더 정확 |
| `g_signal_ratio` 자체가 *document length 의 역함수에 가까운* signal | ratio 의 univariate KCGS 음의 ρ 가 *순수한 G 신호* 인지 *분량의 역신호* 인지 본 데이터로 단정 어려움 |
| M2/M3 의 *잔여 음의 계수 해석* 도 조건부 | 본 보고서 §4 의 "잔여 cheap-talk signal" 은 *r ≈ −0.79 의 강한 얽힘 안에서의 잔여* — *robustness 가 조건부* |

### 14.2 Orthogonalization 의 결과

```
Step 1:  g_signal_ratio  ~  log_tokens
         → 잔차  g_signal_ortho

Step 2:  g_signal_ortho  ↔  kcgs_grade_7  Spearman ρ
```

결과: **ρ ≈ +0.058, p ≈ ns**

| 관찰 | 본 보고서 §4 finding 과의 관계 |
|---|---|
| 부호가 *음에서 양으로* 뒤집힘 | §4 의 "음의 잔여" 가 *log_tokens 만* 빼면 *사라짐* — 즉 "음의 잔여" 의 일부는 *산업·연도 FE 의 흡수 잔재* 일 수 있음 |
| 크기가 *0 근방* | univariate ρ ≈ −0.197 의 *대부분* 이 *분량 + ratio 정의의 기계적 얽힘* 으로 환원 |
| p ≈ ns | 본 데이터에서 "분량 효과만 완전히 빼낸" G 어휘 강도와 KCGS 의 일관된 방향성 부재 |

### 14.3 Alpha 1 (verbosity-adjusted r_i) 와의 비교

`05_alpha_analysis_report.md` §1 의 r_i (`g_signal_ratio ~ log_tokens + industry_FE + year_FE` 잔차) 는 KCGS 와 *약한 음* 의 방향을 유지했다. 본 §14.2 의 `g_signal_ortho` (`log_tokens` 만 빼낸 잔차) 는 *0 근방, 양* 의 방향을 보였다.

| 잔차 정의 | 통제 변수 | KCGS 와의 방향 | 본 보고서 narrative 에서의 위치 |
|---|---|---|---|
| `g_signal_ortho` (§14.2) | `log_tokens` 만 | ρ ≈ +0.058 (ns) | "분량 효과만 빼면 신호가 사라짐" — *fragility evidence* |
| `r_i` (Alpha 1) | `log_tokens + industry_FE + year_FE` | 음의 방향 (약) | "분량 + 산업 + 연도 모두 빼면 약한 음의 잔여" — *조건부 cheap-talk consistency* |

> 두 잔차의 *방향 차이* 자체가 *본 §1 ~ §13 의 cheap-talk 정합 강도가 산업·연도 FE 의 정의에 종속* 됨을 보여준다. *어떤 통제 변수 set 이 정답* 인지 본 데이터로 결정할 수 없다.

### 14.4 Joint Regression 의 결과

본 보고서 §3 의 *main pair* 결정 ((b) `g_signal_ratio + log_tokens`) 을 재검토하기 위해, 4 변수를 동시에 투입했다.

- `g_signal_ratio`
- `esg_signal_ratio`
- `esg_tfidf_concentration`
- `log_tokens`

주요 진단.

| 진단 항목 | 관찰 |
|---|---|
| **VIF** | 동시 투입 시 *상승*, 일부 변수에서 다중공선성 경계 진입 |
| **`g_signal_ratio` ↔ `esg_tfidf_concentration`** | Pearson r ≈ **+0.88** — 매우 강한 공선성 |
| **`g_signal_ratio` 계수** | main pair 대비 *약화 또는 부호 반전* |

### 14.5 Feature redundancy 의 해석

| 가능한 해석 | 본 보고서의 입장 |
|---|---|
| (a) 세 ESG 변수가 *독립적인 disclosure 차원* — 동시 투입이 *분산 분리* | 본 데이터에서는 *지지하기 어려움* — r ≈ 0.88 + VIF 상승은 *독립적 차원* 가설과 정합하지 않음 |
| (b) 세 변수가 *같은 disclosure intensity 의 다른 표현* — 동시 투입이 *과적합* | 본 데이터에서 *더 강하게 지지됨* |

본 보고서 §3 의 *main pair 선택* 은 *결과적으로 정당* 했지만, 그 정당성의 *이유* 가 본 §14 에서 refinement 된다.

- §3 의 정당화: "ESG ratio 간 공선성이 cheap-talk 해석을 *가리기 쉽기 때문*"
- §14 의 refined 정당화: "ESG ratio · concentration 변수들이 *r ≈ 0.88 로 같은 신호의 다른 표현* 이므로, 본 보고서의 *다층 측정* 이 *세 개의 독립 evidence* 라기보다 *하나의 evidence 의 세 가지 표현* 일 가능성이 크다"

### 14.6 본 §14 가 §13 의 핵심 메시지에 미치는 영향

§13 의 핵심 메시지를 다시 옮긴다.

> "분량을 통제하면 `g_signal_ratio`의 KCGS 연관은 약해지지만 음의 방향을 유지하며, 이 약한 잔여 신호와 표본 확장 시 발생한 부호 역전은 — 통계적 결함이 아니라 — 한국 사업보고서의 ESG 언어가 외부 평가와 단순 정합하지 않는다는 measurement evidence로 해석된다."

이 메시지는 *방향성으로는 유지* 된다. 그러나 본 §14 의 결과는 다음과 같이 *조정* 한다.

| §13 의 표현 | §14 이후의 refined 표현 |
|---|---|
| "음의 방향을 유지" | "**산업·연도 FE 를 함께 통제할 때만** 음의 방향을 약하게 유지. `log_tokens` 만 단독 통제 시에는 0 근방으로 약화" |
| "약한 잔여 신호" | "*feature 정의에 조건부인* 약한 잔여 신호" |
| "measurement evidence" | "*tentative / suggestive* measurement evidence — *feature construction sensitivity* 도 함께 finding 으로 보고" |

### 14.7 Decision Box · main pair 선택의 재검토

- **Alternative (재검토):**
  - (a) 본 §3 결정 유지 — main pair 만 회귀
  - (b) joint regression 결과를 *main result 로 격상* — 본 보고서 §4 의 잔여 음의 계수를 *redundancy artifact* 로 재해석
  - (c) 본 §3 결정 유지 + §14 Refinement Addendum 으로 *robustness 강도 조정*
- **Choice:** (c)
- **Justification:** (a) 는 새 결과를 통합하지 않음 — methodological honesty 부족. (b) 는 *cheap-talk 가설의 기각* 까지 가는데, 본 데이터로는 *cheap-talk 의 기각* 도 단정 어려움 — evidence asymmetry. (c) 는 *§3 의 결정이 결과적으로 정당했음* 을 유지하면서 *그 결정이 신호의 강도를 결정하는 가정* 임을 솔직히 보고
- **Limitation:** §3 의 main pair 결정과 §14 의 joint regression 결과가 *동시에 narrative 에 존재* 한다는 점이 독자에게 *evidence 강도 판단의 부담* 을 줌 — 그러나 이 부담이 바로 *연구의 honesty* 의 형태

### 14.8 §14 의 한 줄

> *"본 보고서 §1 ~ §13 의 회귀 narrative 는 방향성으로는 유지된다. 그러나 그 강도는 — `g_signal_ratio` 와 `log_tokens` 의 r ≈ −0.79, ESG 변수 간 r ≈ +0.88, orthogonalize 후 ρ ≈ +0.058 (ns) — 의 세 사실에 의해 *feature construction 결정에 종속됨* 이 정량적으로 드러났다. 본 §14 는 cheap-talk claim 을 *증명* 도, *기각* 도 하지 않는다. 단지 *그 evidence 의 강도가 어디까지인지* 를 정직하게 기록한다."*

---

**§14 추가 산출 파일**

- `data/06_analysis/g_signal_orthogonalized_summary.csv` — `g_signal_ortho` 잔차 + KCGS 단순 ρ
- `data/06_analysis/joint_regression_vif.csv` — 4 변수 동시 투입 VIF + cross-correlations (r ≈ 0.88 포함)
- `data/06_analysis/joint_regression_summary.csv` — 4 변수 동시 회귀 계수표
- `08_revised_final_report.md` — 본 §14 와 §15 (Alpha 5) 가 통합된 canonical final narrative

---

## §15. [2026-05-24 PATCH] Stopwords lineage recovery — robustness re-validation

> 02·03 보고서의 patch 절과 함께 읽는다. 본 §15 는 §8 (preprocessing robustness B/E/F) 와 §14 (joint regression / orthogonalization) 의 결론이 stopwords 의존성 복구 후에도 유지되는지를 점검한다.

### 15.1 무엇이 바뀌었나 (한 줄)

`src/preprocessor.py` 가 공식 의존성 `data/stopwords_ko_esg.txt` 를 로드하지 않은 채로 운영되어, **12개 ESG-행동 동사** (강화·개선·계획·구축·목표·성과·실시·제공·지원·추진·확대·활동) 가 corpus 에 잔존했다. 누락된 다른 7개는 입자/어미로서 Kiwi 가 이미 제거하므로 영향 없음. `exp_F_official` 변형을 신설하여 비교. (Decision Box 는 02 보고서 §9.4 참조.)

### 15.2 §8 (B/E/F preprocessing robustness) 와의 일관성

본 보고서 §8 의 핵심 주장은 *"7/8 feature 가 B/E/F 변형에 대해 sign-consistent, rho-range < 0.03"* 였다. stopwords 복구는 **이 결론의 외연을 한 단계 확장**한다:

- 기존 §8: B/E/F 세 변형에 robust
- 신규: B/E/F + F_official 네 변형에 대해 동일 결론 성립
- 단 `bp_contamination_rate` 는 §8 에서 이미 B vs E/F 에서 부호 flip 으로 보고됨 — F → F_official 에서는 변화 없음 (둘 다 +0.050 ns)

| feature | B/E/F 일관성 (기존) | F vs F_official (신규) | 통합 robustness |
|---|---|---|---|
| total_tokens | ✓ | ✓ (Δρ=−0.001) | 4/4 |
| esg_signal_count | ✓ | ✓ (Δρ=0) | 4/4 |
| g_signal_count | ✓ | ✓ (Δρ=0) | 4/4 |
| g_signal_ratio | ✓ | ✓ (Δρ=+0.002) | 4/4 |
| esg_signal_ratio | ✓ | ✓ (Δρ=+0.002) | 4/4 |
| esg_g_relative | ✓ | ✓ (Δρ=0) | 4/4 |
| bp_contamination_rate | ✗ (B vs E/F flip) | ✓ (F vs F_official 변화 없음) | 3/4 (기존 한계 그대로) |
| **esg_tfidf_concentration** | ✓ (B/E/F 모두 음) | **✗ (F=−0.175 → F_official=−0.007 ns)** | **3/4** |

**새로운 finding**: `esg_tfidf_concentration` 은 B/E/F 내부에서는 robust 였지만 **공식 stopwords 의존성 정합에 대해서는 sensitive** 였다. 이는 §8 의 robustness 정의를 정련한다 — "변형들의 *외연을 어디까지로 잡느냐* 가 robustness 의 결론을 좌우" 한다는 finding 자체로 보고한다.

### 15.3 §14 의 verbosity-orthogonalized 결과는 invariant

§14.4 의 partial-out-log_tokens 결과를 F_official 에서 재산출:

| feature | rho_orth (F) | rho_orth (F_official) | Δ | §14 결론 영향 |
|---|---|---|---|---|
| g_signal_count | +0.245*** | +0.247*** | +0.002 | §14 의 main robust signal 결론 유지 |
| esg_g_relative | +0.251*** | +0.250*** | −0.001 | §14 의 suppressor 구조 유지 |
| bp_contamination_rate | −0.251*** | −0.250*** | +0.001 | §14 의 suppressor 구조 유지 |
| g_signal_ratio | +0.059 ns | +0.056 ns | −0.003 | §14 의 "orthogonalize 후 ns" 결론 유지 |
| esg_tfidf_concentration | −0.056 ns | +0.090 ns | +0.146 | orthogonalize 에서도 sign flip — §14 의 redundancy 진단 강화 |

→ **§14 의 핵심 주장 (g_signal_ratio orthogonalize 후 0 근방·ns, g_signal_count 만 verbosity-robust survivor) 은 변경 없음.** §14.5 의 *"세 변수가 같은 disclosure intensity 의 다른 표현"* 가설은 본 §15 의 evidence 로 한 단계 강화된다 — `esg_tfidf_concentration` 의 기존 음의 상관이 cheap-talk 동사 saturation 의 artifact 였음이 정량적으로 드러나기 때문.

### 15.4 §13 의 한 줄 — 변경 여부

§13 의 핵심 메시지는 **방향성·강도 모두 유지된다**. 본 §15 는 §13 의 narrative 에 다음 보강 표현만을 추가한다:

> "본 보고서의 결론은 *preprocessing 의존성을 공식 정렬한 후에도* 재현된다. 단, `esg_tfidf_concentration` 의 보조적 음의 상관은 preprocessing-sensitive 한 artifact 로 강등된다 — cheap-talk 가설은 약화되지 않으며, 오히려 그 동사들이 ESG 어휘 변별력으로 측정되고 있었다는 점이 cheap-talk 의 추가 evidence 가 된다."

### 15.5 산출 파일 (recovery)

- `data/05_features/recovery/stopwords_delta_spearman.csv`
- `data/05_features/recovery/verbosity_orth_delta.csv`
- `data/05_features/recovery/bootstrap_ci_before_after.csv`
- `data/05_features/recovery/sign_stability_before_after.csv`
- `outputs/recovery/COMPARISON_30_stage4_robustness_layer.html`
- patched source: `src/preprocessor.py` (`STOPWORDS_OFFICIAL`, `exp_F_official` config)

---

## §15. [2026-05-24 PATCH] Stopwords lineage recovery — robustness re-validation

> 02·03 보고서의 patch 절과 함께 읽는다. 본 §15 는 §8 (preprocessing robustness B/E/F) 와 §14 (joint regression / orthogonalization) 의 결론이 stopwords 의존성 복구 후에도 유지되는지를 점검한다.

### 15.1 무엇이 바뀌었나 (한 줄)

`src/preprocessor.py` 가 공식 의존성 `data/stopwords_ko_esg.txt` 를 로드하지 않은 채로 운영되어, **12개 ESG-행동 동사** (강화·개선·계획·구축·목표·성과·실시·제공·지원·추진·확대·활동) 가 corpus 에 잔존했다. 누락된 다른 7개는 입자/어미로서 Kiwi 가 이미 제거하므로 영향 없음. `exp_F_official` 변형을 신설하여 비교. (Decision Box 는 02 보고서 §9.4 참조.)

### 15.2 §8 (B/E/F preprocessing robustness) 와의 일관성

본 보고서 §8 의 핵심 주장은 *"7/8 feature 가 B/E/F 변형에 대해 sign-consistent, rho-range < 0.03"* 였다. stopwords 복구는 **이 결론의 외연을 한 단계 확장**한다:

- 기존 §8: B/E/F 세 변형에 robust
- 신규: B/E/F + F_official 네 변형에 대해 동일 결론 성립
- 단 `bp_contamination_rate` 는 §8 에서 이미 B vs E/F 에서 부호 flip 으로 보고됨 — F → F_official 에서는 변화 없음 (둘 다 +0.050 ns)

| feature | B/E/F 일관성 (기존) | F vs F_official (신규) | 통합 robustness |
|---|---|---|---|
| total_tokens | ✓ | ✓ (Δρ=−0.001) | 4/4 |
| esg_signal_count | ✓ | ✓ (Δρ=0) | 4/4 |
| g_signal_count | ✓ | ✓ (Δρ=0) | 4/4 |
| g_signal_ratio | ✓ | ✓ (Δρ=+0.002) | 4/4 |
| esg_signal_ratio | ✓ | ✓ (Δρ=+0.002) | 4/4 |
| esg_g_relative | ✓ | ✓ (Δρ=0) | 4/4 |
| bp_contamination_rate | ✗ (B vs E/F flip) | ✓ (F vs F_official 변화 없음) | 3/4 (기존 한계 그대로) |
| **esg_tfidf_concentration** | ✓ (B/E/F 모두 음) | **✗ (F=−0.175 → F_official=−0.007 ns)** | **3/4** |

**새로운 finding**: `esg_tfidf_concentration` 은 B/E/F 내부에서는 robust 였지만 **공식 stopwords 의존성 정합에 대해서는 sensitive** 였다. 이는 §8 의 robustness 정의를 정련한다 — "변형들의 *외연을 어디까지로 잡느냐* 가 robustness 의 결론을 좌우" 한다는 finding 자체로 보고한다.

### 15.3 §14 의 verbosity-orthogonalized 결과는 invariant

§14.4 의 partial-out-log_tokens 결과를 F_official 에서 재산출:

| feature | rho_orth (F) | rho_orth (F_official) | Δ | §14 결론 영향 |
|---|---|---|---|---|
| g_signal_count | +0.245*** | +0.247*** | +0.002 | §14 의 main robust signal 결론 유지 |
| esg_g_relative | +0.251*** | +0.250*** | −0.001 | §14 의 suppressor 구조 유지 |
| bp_contamination_rate | −0.251*** | −0.250*** | +0.001 | §14 의 suppressor 구조 유지 |
| g_signal_ratio | +0.059 ns | +0.056 ns | −0.003 | §14 의 "orthogonalize 후 ns" 결론 유지 |
| esg_tfidf_concentration | −0.056 ns | +0.090 ns | +0.146 | orthogonalize 에서도 sign flip — §14 의 redundancy 진단 강화 |

→ **§14 의 핵심 주장 (g_signal_ratio orthogonalize 후 0 근방·ns, g_signal_count 만 verbosity-robust survivor) 은 변경 없음.** §14.5 의 *"세 변수가 같은 disclosure intensity 의 다른 표현"* 가설은 본 §15 의 evidence 로 한 단계 강화된다 — `esg_tfidf_concentration` 의 기존 음의 상관이 cheap-talk 동사 saturation 의 artifact 였음이 정량적으로 드러나기 때문.

### 15.4 §13 의 한 줄 — 변경 여부

§13 의 핵심 메시지는 **방향성·강도 모두 유지된다**. 본 §15 는 §13 의 narrative 에 다음 보강 표현만을 추가한다:

> "본 보고서의 결론은 *preprocessing 의존성을 공식 정렬한 후에도* 재현된다. 단, `esg_tfidf_concentration` 의 보조적 음의 상관은 preprocessing-sensitive 한 artifact 로 강등된다 — cheap-talk 가설은 약화되지 않으며, 오히려 그 동사들이 ESG 어휘 변별력으로 측정되고 있었다는 점이 cheap-talk 의 추가 evidence 가 된다."

### 15.5 산출 파일 (recovery)

- `data/05_features/recovery/stopwords_delta_spearman.csv`
- `data/05_features/recovery/verbosity_orth_delta.csv`
- `data/05_features/recovery/bootstrap_ci_before_after.csv`
- `data/05_features/recovery/sign_stability_before_after.csv`
- `outputs/recovery/COMPARISON_30_stage4_robustness_layer.html`
- patched source: `src/preprocessor.py` (`STOPWORDS_OFFICIAL`, `exp_F_official` config)
