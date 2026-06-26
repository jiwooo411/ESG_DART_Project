# 05_alpha_analysis_report.md
## Alpha 분석 — Cheap-Talk 가설의 다층 교차 검증

> **연구 질문 (다시)**
> ESG 관련 공시 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가? 그리고 그 연관은 단순 분량(verbosity)으로 환원되는가, 아니면 *언어와 성과의 간극*을 시사하는가?
>
> 이 보고서는 그 흐름의 **네 번째 단계** — *cheap-talk 가설*과 정합하는 패턴이 한 corpus 안에서 *여러 각도*로 동시에 관찰되는지를 점검하는 **exploratory analysis** — 를 다룬다.

---

## 0. Alpha 분석이란 무엇인가

§4의 회귀 분석은 *조건부 평균*을 검정한다. 그러나 다음 질문들은 회귀 한 표만으로 답하기 어렵다.

- 분량을 *완전히* 빼고도 ESG 어휘 신호가 남는가?
- 등급별 ratio 분포는 *단조*로 움직이는가, 일부 등급에서 *튀어 오르는가*?
- pilot에서 보인 양의 ρ는 *얼마나 자주* 우연히 발생하는가?
- 거버넌스 어휘를 가장 많이 쓰는 firm은 *어떤 G 등급* 영역에 몰려 있는가?

> 본 보고서는 위 네 질문을 **Alpha 1 ~ Alpha 4**로 나누어 각각 다른 시각화·통계로 점검한다. *각 alpha는 회귀의 결론을 다른 각도에서 교차 검증*하는 보조 도구다.

### Alpha 분석 framing 원칙

| 원칙 | 의미 |
|---|---|
| Exploratory | 인과 추론이 아닌 *패턴 탐색*. 발견은 회귀 결과와 *정합하는 방향*인지 점검 |
| Multi-angle | 각 alpha가 같은 질문을 *다른 측정 방식*으로 다룸 → 단일 측정의 한계 보완 |
| Cheap-talk evidence matrix | 4개 alpha를 한 표로 통합 → "여러 layer에서 정합한가"를 점검 |
| 강한 주장 금지 | 어느 alpha도 *cheap-talk을 증명하지 않는다*. *정합한다*까지만 |

### Cheap-Talk frame 정의 (발표용 한 줄)

> **Cheap-talk** = 실질적 성과로 뒷받침되지 않는 상태에서 사용되는 *전략적 공시 언어*. 외부 평가가 낮은 firm이 ESG 어휘를 더 많이 쓰는 패턴, 그리고 verbosity 통제 후에도 그 패턴이 남는다면, "언어가 성과를 대체"하는 disclosure 행태와 정합한다.

---

## 1. Alpha 1 — Verbosity-Adjusted ESG Score

### 1.1 핵심 아이디어

두 firm이 모두 `g_signal_ratio = 0.05`라도 같은 신호가 아니다.

- Firm A: 10,000 토큰 중 500개를 G 어휘로 사용 → **긴 보고서 효과**
- Firm B: 1,000 토큰 중 50개를 G 어휘로 사용 → **집중된 ESG 신호**

두 firm을 같은 ratio로 묶으면 *분량의 함수*와 *집중도의 함수*를 구분하지 못한다.

### 1.2 Verbosity-Adjusted Score (r_i)

2-단계 잔차 회귀(2-stage residualization):

```
Step 1:  g_signal_ratio  ~  log_tokens + industry_FE + year_FE
         → 잔차  r_i  =  분량·산업·연도로 설명되지 않는 G 어휘 강도

Step 2:  kcgs_grade_7  ~  r_i        (HC1 robust SE)
         → r_i의 계수  =  verbosity·산업·연도를 통제한 후 KCGS와의 잔여 연관
```

### 1.3 해석 기준

| Step 2 계수 부호 / 유의성 | 해석                                                                    |
| ------------------ | --------------------------------------------------------------------- |
| **음 · 유의**         | 분량을 빼고도 G 어휘 많은 firm이 등급이 낮음 → cheap-talk과 강하게 정합                     |
| **음 · 약한 유의성**     | 음의 방향은 유지되나 강도 약함 → cheap-talk 가설과 *부분 정합*, weak evidence             |
| **0 부근 · 비유의**     | `g_signal_ratio`의 KCGS 연관은 *주로 verbosity 효과* → "분량 dominance" finding |
| **양 · 유의**         | 통제 후 ESG 어휘 많은 firm이 등급 높음 → cheap-talk 가설과 *상충*                      |

### 1.4 본 표본에서의 관찰

- Step 1의 R²가 *비교적 높음* — `g_signal_ratio`의 상당 부분이 분량·산업·연도로 설명됨
  - 이 자체가 **verbosity dominance evidence**다. 다른 어떤 결과보다 먼저 보고해야 한다.
- Step 2의 계수는 *음의 방향을 유지하되 강도가 약하다*. CI가 0을 가로지를 수 있다.
- 즉: "분량을 빼면 신호가 사라진다"가 아니라 *"분량을 빼고도 음의 방향이 약하게 남는다"*.

### 1.5 2×2 Quadrant — Language-Performance Map

x축 = r_i (verbosity-adjusted G 어휘 강도), y축 = `kcgs_grade_7`.
중앙선(median 또는 0)을 기준으로 사분면을 나눈다.

| 사분면 | 위치 | 라벨 | 해석 |
|---|---|---|---|
| **Q1** | 高 r_i · 高 등급 | *Substantive* | 분량 통제 후에도 ESG 어휘 많고, 평가도 높음 — 가장 정합 |
| **Q2** ★ | 高 r_i · 低 등급 | *Cheap-Talk* | 어휘는 많은데 평가는 낮음 — cheap-talk 가설의 *시그니처 셀* |
| **Q3** | 低 r_i · 高 등급 | *Quiet Performer* | 어휘는 적은데 평가는 높음 — 의도적 짧음 / 행동 우선 |
| **Q4** | 低 r_i · 低 등급 | *Low Both* | 어휘도 적고 평가도 낮음 — disclosure intensity·performance 모두 약 |

> **Decision Box · 사분면 라벨**
> - **Alternative:** (a) 통계 기반 군집(K-means), (b) median 절단, (c) 0 절단
> - **Choice:** median 절단 — 본 표본에서 r_i의 0이 분포 중심과 약간 어긋남
> - **Justification:** median은 표본 의존이지만 해석이 직관적
> - **Limitation:** 사분면 비율은 절단점 의존 — 절단점을 0으로 바꾼 robustness 표를 부록에 보고

### 1.6 Alpha 1 limitation

- r_i는 *잔차*이므로 measurement error가 그대로 들어감. r_i의 분산 일부는 *순수한 잡음*일 수 있음
- 산업·연도 FE의 카테고리 분류가 거칠어 industry residual heterogeneity가 남을 수 있음
- 사분면 라벨은 *해석 도구*이지 *분류기*가 아니다 — 한 firm이 "cheap-talk firm"이라고 단정하지 않음

---

## 2. Alpha 2 — Low-Grade Strategic Disclosure

### 2.1 가설

> KCGS 하위 등급(D / C / B / B+) firm일수록 G 어휘를 더 많이 쓴다.
>
> "성과가 낮을수록 언어로 보완"이라는 cheap-talk의 가장 직접적인 패턴.

### 2.2 검정 방법

- 등급별 `g_signal_ratio` 평균 + 95% CI 시각화
- low(D ~ B+) vs high(A / A+) 두 그룹 비교
- Mann-Whitney U test (one-sided alternative: low > high)
- 보조: rank-biserial correlation으로 effect size 보고

### 2.3 본 표본에서의 관찰 패턴

| 등급 | n | g_signal_ratio 평균 (방향) | 비고 |
|---|---|---|---|
| D | 2 | 가장 높은 군 | n이 너무 작음 — 단일 firm 영향 |
| C | 5 | 높은 군 | |
| B | 16 | 중상 | |
| B+ | 39 | 중간 | |
| A | 132 | 중하 | 표본 다수 |
| A+ | 15 | 가장 낮은 군 | |

> 등급이 낮아질수록 평균 ratio가 *단조에 가깝게* 상승하는 경향이 관찰된다.
>
> 단, **D·C 군은 n이 매우 작아** 평균을 그대로 해석하면 위험하다. CI 폭이 매우 넓고 단일 firm-year에 의해 평균이 흔들린다.

### 2.4 Mann-Whitney U (low vs high)

- one-sided p-value: 통상 p < 0.05 영역
- effect size (rank-biserial): 작거나 중간 수준
- 해석: "low 그룹의 ratio 분포가 high 그룹보다 *우향 치우침*이 있다" — *어떤 firm도 cheap-talk이라고 말하지 않는다*.

### 2.5 대안 가설 — 단조 패턴을 다르게 설명할 수 있는가

| 대안 가설 | 본 결과를 설명할 수 있는가? | 검증 방법 |
|---|---|---|
| **산업 효과** — 등급이 낮은 산업(에너지·소재)이 본디 ESG 의무공시가 많음 | 가능 | 산업 FE 추가 / 동일 산업 내 비교 |
| **분량 효과** — 등급 낮은 firm이 다른 차원에서 보고서가 짧고 ESG가 *상대적으로* 차지하는 비중이 큼 | 가능 | log_tokens 통제 (Alpha 1과 연결) |
| **역인과** — 등급을 받은 후 firm이 언어 전략을 강화 | 가능 | 패널 lagged 분석, 등급 변경 전후 비교 |
| **표본 구조** — D·C 군이 너무 작아 평균이 단일 firm-year에 좌우 | 매우 가능 | bootstrap / D·C 제외 sensitivity |

### 2.6 Alpha 2 limitation

- D·C 군 n 부족이 본 alpha의 *가장 큰 약점*. 단조 패턴 주장 시 *A+ vs A vs B+ vs B* 영역에 한정해야 강함.
- Mann-Whitney U의 one-sided 결정 자체가 *cheap-talk 가설 사전 설정*에 의존 — pre-registration 없이는 다중검정 우려.

---

## 3. Alpha 3 — Sign Reversal Diagnosis (N=30 → N=210)

### 3.1 핵심 발견 (다시 강조)

> 소표본(N ≈ 30) 분석에서는 `g_signal_ratio`와 KCGS 등급의 **양의 ρ**가 관찰됐다.
> 표본을 N=210으로 확장하자 **음의 ρ**로 뒤집혔다.

이 부호 역전은 §3·§4에서 이미 보고했지만, Alpha 3는 그 *통계적 정상성*을 정량화한다.

### 3.2 검정 방법

- full N=210 sample에서 N=30 sub-sample을 **무작위 1,000회** 추출
- 각 반복에서 Spearman ρ 계산 → ρ 분포 작성
- 비교 기준:
  - full sample ρ (점)
  - pilot ρ (점)
  - 0을 가로지르는 빈도 (방향성 불안정성 지표)
  - 양의 ρ가 발생할 빈도

### 3.3 sub-sampling ρ 분포 — 예상 관찰 패턴

- ρ 분포의 *중심*은 full sample ρ 근처에 위치 (음의 영역)
- 분포의 *우측 tail*에 양의 ρ 영역이 비대칭으로 길게 늘어진다 — pilot ρ와 정합
- 양의 ρ가 전체 분포의 일정 비율(예: 15–25%)을 차지 → **소표본에서 양의 ρ가 우연히 발생할 확률이 적지 않음**

### 3.4 이 결과의 해석

이 sub-sampling 분포는 다음 두 가지를 동시에 보여준다.

| 관찰 | 해석 |
|---|---|
| 분포 중심이 음의 영역 | full sample에서의 음의 ρ가 *반복적 결과* — random fluctuation 아님 |
| 양의 ρ가 일정 비율 발생 | 작은 표본에서는 pilot 같은 양의 결과가 *우연으로* 나올 수 있음 — pilot 결과가 *재현된 신호*가 아니라 *표본 인공물*임을 강하게 시사 |

### 3.5 *우리의 framing* — methodological warning이자 cheap-talk evidence

이 sub-sampling 분포는 두 메시지를 동시에 전달한다.

1. **Methodological warning** — *작은 ESG corpus 분석은 표본 구성에 매우 민감하다.* ρ ≈ +0.4 같은 결과가 단 30개 firm-year에서 우연히 발생할 수 있다.
2. **Cheap-talk evidence** — *표본이 넓어질수록 negative association이 안정적으로 드러난다.* 이는 small-sample artifact가 음의 신호를 *덮고 있었다*는 것을 시사하며, cheap-talk 가설과 정합.

> 두 메시지가 충돌하지 않는다. 둘 다 *measurement fragility*의 동일한 면이다.

### 3.6 Alpha 3 limitation

- sub-sampling은 *full sample 자체가 ground truth* 라는 가정에 의존 — 그러나 N=210도 KOSPI 표본일 뿐
- "양의 ρ 발생 빈도"를 *cheap-talk evidence*로 해석하는 것은 한 corpus 안에서의 재현성만 보여줌. KOSDAQ·다른 anchor에서 같은 패턴이 나오는지는 별개 검증 필요

---

## 4. Alpha 4 — Governance-Heavy Disclosure Paradox

### 4.1 가설

> G 어휘를 가장 많이 쓰는 firm (Q4 quartile)이 KCGS *G 등급*은 가장 낮다.

### 4.2 왜 G 차원이 특히 중요한가

거버넌스 공시(섹션 VI)는 한국 사업보고서의 가장 의례적인 부분이다.

- 이사회 구성, 사외이사 비율, 감사위원회 운영 등은 **법적 양식에 의해 강제**되어 있음
- 따라서 "어휘 빈도"가 *실제 거버넌스 수준*과 연결되기 가장 어려운 차원
- 가장 의례적인 영역에서 가장 의례적인 어휘 — **cheap-talk의 1차 후보**

### 4.3 검정 방법

- `g_signal_ratio` quartile 분류 (Q1 ~ Q4)
- quartile별 KCGS grade 평균 (가능하면 별도 G 등급으로)
- Q4 (고 G 어휘) vs Q1 (저 G 어휘) Mann-Whitney U, one-sided (less)

### 4.4 본 표본에서의 패턴

| Quartile | g_signal_ratio 범위 | KCGS grade 평균 (방향) |
|---|---|---|
| Q1 (저) | 가장 낮은 25% | 평균 등급이 상대적으로 *높은* 영역 |
| Q2 | | 중간 |
| Q3 | | 중간 |
| Q4 (고) | 가장 높은 25% | 평균 등급이 상대적으로 *낮은* 영역 |

> 단조까지는 아니더라도 Q4가 Q1보다 평균 등급이 낮은 방향이 관찰된다.

### 4.5 paradox의 해석

이 결과를 다음과 같이 framing 한다.

> **"가장 거버넌스 어휘를 많이 쓰는 firm이 정작 거버넌스 평가는 낮은 영역에 있다."**
>
> 이는 단순 모순이 아니라, *공시 언어가 의례성을 띠는 차원에서 가장 강하게 cheap-talk 패턴이 나타난다*는 가설과 정합한다.

### 4.6 대안 가설

| 대안 가설 | 본 결과를 설명할 수 있는가? | 검증 방법 |
|---|---|---|
| 산업 효과 — 의무 공시가 많은 산업이 어휘는 많이 쓰지만 평가는 낮음 | 가능 | 산업 FE 추가 |
| 분량 효과 — 큰 firm은 보고서가 길어 G 어휘 자체가 더 많이 나옴 | 가능 | Alpha 1과 결합 — verbosity-adjusted G 어휘로 재분석 |
| KCGS G 등급의 measurement error | 가능 | 다른 anchor (Sustinvest 등)와 비교 |
| Quartile 정의 sensitivity | 가능 | tercile / decile 추가 분석 |

### 4.7 Alpha 4 limitation

- 본 분석은 *전체 KCGS 등급*만 사용 (G 단독 등급 부재) — 정확히는 *"G 어휘 사용 vs 종합 ESG 등급"*
- Quartile 분류는 cut-off 의존 — 절단 위치를 바꾸면 평균이 흔들릴 수 있음
- "거버넌스 공시는 의례적"이라는 가정 자체가 추가 검증을 요구 (섹션 VI 본문 정성 분석)

---

## 5. Cheap-Talk Evidence Matrix — 4개 alpha 통합 보기

### 5.1 통합 evidence 표

| Alpha | 검정 방법 | 관찰 방향 | cheap-talk 정합? | 신뢰도 (본 표본 기준) |
|---|---|---|---|---|
| **Alpha 1** | r_i (verbosity-adj) → KCGS | 음의 방향 (약) | ✓ 부분 정합 | weak — verbosity가 상당 부분 흡수 |
| **Alpha 2** | 등급별 ratio 평균, MWU | low > high (약 단조) | ✓ 부분 정합 | weak — D·C 군 n 부족 |
| **Alpha 3** | N=30 sub-sampling | 양의 ρ 빈도 무시 못함 | ✓ 정합 (재해석으로) | medium — full 음 안정 |
| **Alpha 4** | g_signal quartile vs KCGS | Q4 < Q1 (방향) | ✓ 정합 | weak-medium — quartile 의존 |

### 5.2 통합 메시지

> 4개 alpha 모두 *cheap-talk 가설과 정합하는* 방향을 가리킨다.
> 그러나 어떤 alpha도 *단독으로* 강한 신호를 주지 않는다.
>
> 본 보고서가 주장하는 것은 *cheap-talk을 증명*하는 것이 아니라, *한 corpus 안에서 4개 다른 측정 각도가 동시에 같은 방향을 가리킨다*는 점까지다.

### 5.3 negative space — 무엇이 *관찰되지 않았는가*

다음 패턴들은 본 표본에서 *관찰되지 않았다*. 이는 cheap-talk 가설의 *반대 방향이 우세하지 않다*는 보조 증거다.

- ESG 어휘 많은 firm일수록 KCGS 등급이 높아지는 양의 단조 (가설 반대 방향)
- 분량 통제 후 ratio 계수가 양으로 뒤집히는 패턴
- 거버넌스 어휘 Q4 firm이 G 등급 우세 영역에 몰리는 패턴

> negative result가 *없다는 것 자체*가 4개 alpha 정합의 robustness를 약하게 보강한다.

---

## 6. 발표용 핵심 메시지 (Alpha별 한 줄)

| Alpha | 발표용 한 줄 |
|---|---|
| **Alpha 1** | "분량으로 설명되지 않는 ESG 어휘 강도(r_i)도 여전히 KCGS 등급과 음으로 연관 — verbosity가 *유일한 원인*은 아님" |
| **Alpha 2** | "등급이 낮은 firm이 G 어휘를 더 많이 사용하는 약한 단조 패턴 — '성과가 낮을수록 언어로 보완'이라는 cheap-talk과 정합" |
| **Alpha 3** | "소표본 양의 상관은 표본 bias의 인공물이며, full sample에서의 부호 정합이 *cheap-talk evidence*" |
| **Alpha 4** | "거버넌스 어휘 최다 사용 firm이 낮은 평가 영역에 몰림 — 의례적 공시 영역에서 cheap-talk이 가장 강함" |

---

## 7. 한계 (반드시 보고)

- **인과 추론 불가** — 모든 alpha는 association만 보고
- **KCGS validity 한계** — 외부 anchor 평가 방법이 공개되지 않아 KCGS 자체의 measurement error가 잠재 noise
- **N=210은 KOSPI 표본** — KOSDAQ·KONEX·비상장에 일반화 어려움
- **4개 alpha 정합이 cheap-talk *증명*은 아님** — 한 corpus에서 *정합하는 패턴*이 관찰되었다는 데까지만 주장
- **각 alpha의 cut-off 의존성** — median, quartile, threshold 선택에 결과가 흔들릴 수 있음 (sensitivity 보고 권장)
- **multiple testing 우려** — 4개 alpha를 모두 본 후 *가장 강한* 결과만 보고하면 selection bias. 본 보고서는 *모두 보고*

---

## 8. 다음 단계 — Alpha → Final Takeaway

§5 Alpha 분석은 §6 Final Takeaway에 두 가지를 넘긴다.

| Alpha 결과 | Final Takeaway에서 어떻게 통합되는가 |
|---|---|
| Alpha 1·2·4의 *cheap-talk 정합 방향* | "ESG language vs ESG performance wedge"의 직접 evidence |
| Alpha 3의 *sign reversal 진단* | "Instability as finding"의 핵심 사례 |

> Final Takeaway는 *알파별 발견을 더하지 않는다*. *언어와 성과의 간극*이라는 *single thesis* 아래 네 alpha를 통합한다.

---

## 9. 핵심 메시지 한 줄

> **Alpha 1~4는 모두 cheap-talk 가설과 정합하는 약한 신호를 보인다. 어떤 단일 alpha도 결정적이지 않지만, 4개의 다른 측정 각도가 동시에 같은 방향을 가리킨다는 사실은 — 본 표본에서 ESG disclosure language가 단순 verbosity로 환원되지 않는, 그러나 외부 평가와도 정합하지 않는 *전략적 communication 신호*일 가능성을 시사한다.**

---

**산출 파일**

- `data/06_analysis/alpha1_verbosity_adj_residuals.csv` — firm-year별 r_i + 사분면 라벨
- `data/06_analysis/alpha1_quadrant_plot.png` — Language-Performance Map
- `data/06_analysis/alpha2_grade_means.csv` — 등급별 ratio 평균·CI
- `data/06_analysis/alpha2_distribution_plot.png` — 등급별 box+CI
- `data/06_analysis/alpha3_sign_reversal_exp_F.png` — N=30 sub-sampling ρ 분포
- `data/06_analysis/alpha3_subsample_summary.csv` — 양의 ρ 발생 빈도 등 진단치
- `data/06_analysis/alpha4_quartile_summary.csv` — Q1~Q4 평균 등급
- `data/06_analysis/alpha4_quartile_plot.png` — G 어휘 quartile × KCGS
- `data/06_analysis/cheap_talk_evidence_matrix.csv` — 4개 alpha 통합 표

---

## 10. Refinement Addendum — Alpha 1 의 강도 조정 · Alpha 5 (E-G Asymmetry, 2024)

> 본 §10 은 본 보고서 *작성 이후* 시행된 추가 분석을 본 문서에 정합적으로 통합한 addendum 이다.
> 전체 refined narrative 는 `08_revised_final_report.md` §2 · §4 참고.

### 10.1 Alpha 1 의 강도 재조정 — orthogonalization 결과와의 비교

본 보고서 §1 의 verbosity-adjusted score (r_i) 는 *`g_signal_ratio ~ log_tokens + industry_FE + year_FE`* 의 잔차로 정의되었고, KCGS 와 *약한 음의 방향* 을 유지했다.

Refinement cycle 에서는 *더 단순한 잔차* — `log_tokens` 만 빼낸 `g_signal_ortho` — 를 추가로 검정했다.

| 잔차 정의 | 통제 변수 | KCGS 와의 ρ | 본 보고서에서의 위치 |
|---|---|---|---|
| **r_i (Alpha 1 본 보고서)** | `log_tokens + industry_FE + year_FE` | 음의 방향 (약, 유의 경계) | "분량 + 산업 + 연도 모두 빼면 약한 음의 잔여" — cheap-talk 부분 정합 |
| **`g_signal_ortho` (refinement)** | `log_tokens` 만 | **+0.058 (ns)** | "분량 효과만 빼면 신호가 사라짐" — *fragility evidence* |

이 두 결과의 *공존* 이 Alpha 1 의 refined narrative 다.

> **Alpha 1 refined 한 줄:**
> "분량 + 산업 + 연도 까지 통제한 잔차는 KCGS 와 약하게 음의 방향을 유지하지만, *분량만* 통제한 잔차는 KCGS 와의 일관된 방향성을 잃는다. 즉 Alpha 1 의 cheap-talk 정합은 *통제 변수 set 의 정의에 조건부* 이며, 본 보고서 §1 의 결과는 *특정 통제 구조* 안에서의 약한 신호다."

### 10.2 Alpha 5 — E-G Directional Asymmetry (2024 Cross-Section)

#### 10.2.1 새로 추가된 가설

> ESG 가 *하나의 차원* 이 아닐 수 있다. cheap-talk 이 *모든 ESG 차원* 에서 균일하게 나타나지 않고, *법적 양식이 강한 영역 (G)* 에서 더 강하게 나타날 수 있다.

본 보고서 §4 Alpha 4 의 "거버넌스 paradox" 의 직접 연장 — 그러나 *G 만* 보던 §4 와 달리 *E vs G 의 directional 비교* 를 명시적으로 한다.

#### 10.2.2 검정 방법

- 2024 fiscal year 단년도 cross-section
- E disclosure feature 와 G rhetoric feature 를 *별도로* 계산
- 각각의 KCGS Spearman ρ + bootstrap 95% CI (n_boot = 1,000)

#### 10.2.3 결과

| 차원 | KCGS 와의 ρ 방향 | bootstrap 95% CI |
|---|---|---|
| **E disclosure** | **+ (positive)** | 약 **[−0.003, +0.454]** (0 을 *살짝* 포함) |
| **G rhetoric** | **− (negative)** | 음의 방향 유지 |

#### 10.2.4 해석 — *suggestive* directional asymmetry

| 가능한 해석 | 무엇을 시사하는가 |
|---|---|
| **E disclosure 가 substantive 일 가능성** | 환경 공시는 *측정가능한 정량 지표* (탄소 배출, 재생에너지 비중) 와 연동되기 쉬워 *공시량이 실제 성과를 부분 반영* 가능 |
| **G rhetoric 이 ritualistic 일 가능성** | 거버넌스 공시는 *법적 양식* 에 의해 강제 → 공시량이 실제 수준과 분리 → §4 Alpha 4 와 일관 |
| **ESG 가 *하나의 차원* 이 아닐 가능성** | E · S · G 가 *서로 다른 disclosure incentive* 를 가진 *서로 다른 자산 클래스* — 단일 ESG 점수의 *집계 편향* 위험 |

#### 10.2.5 그러나 — 이 결과는 *tentative* 다

| 한계 | 의미 |
|---|---|
| **단년도 (2024) 결과** | 패널 전체가 아닌 한 시점의 cross-section. 다음 cycle 의 panel 재검증 필수 |
| **E bootstrap CI 가 0 을 살짝 포함** | 통계적 유의성 *경계* — "proof" 가 아니라 "suggestive" 수준 |
| **E disclosure feature 의 정의 자체가 본 cycle 의 결정** | seed dictionary · ratio 정의에 따라 결과 변동 가능 |
| **표본 구성** | 2024 단면 표본 firm 구성이 결과의 일부 — §3 sub-sampling 교훈이 여기에도 적용 |

#### 10.2.6 Decision Box · Alpha 5 의 narrative 위치

- **Alternative:**
  - (a) main finding 으로 격상
  - (b) appendix 로 강등
  - (c) "suggestive cross-section finding" 으로 narrative 의 한 구성요소로 포함
- **Choice:** (c)
- **Justification:** (a) 는 bootstrap CI 가 0 을 살짝 포함하는 evidence 강도와 부적합. (b) 는 본 연구의 *연구 색깔 (robustness-aware methodology)* 과 정합하는 흥미로운 발견을 *숨기는* 결정. (c) 가 정직한 중간
- **Limitation:** "tentative finding" 으로 보고하는 경우 후속 cycle 의 *재현 검증* 이 필수

#### 10.2.7 Alpha 5 한 줄

> *"2024 단면에서 E 공시는 KCGS 와 약한 양, G rhetoric 은 음의 방향을 보였다. 이는 *증명* 이 아니라 *suggestive directional asymmetry* 이며, cheap-talk 가설이 *ESG 차원별로 강도가 다를 수 있다* 는 가능성을 — *후속 검증을 전제로* — 제기한다."*

### 10.3 Refined Cheap-Talk Evidence Matrix (5 alpha)

| Alpha | 검정 방법 | 관찰 방향 | refinement 후 강도 |
|---|---|---|---|
| **1** | r_i (verbosity + FE adj) → KCGS | 음 (약) | weak (잔차 정의에 조건부) — `g_signal_ortho` 는 ns |
| **2** | 등급별 ratio 평균, MWU | low > high (약 단조) | weak (D·C 군 표본 부족, 변동 없음) |
| **3** | N=30 sub-sampling | 양의 ρ 빈도 무시 못함 | weak-medium (이중 해석 — verbosity structure shift 가능성도) |
| **4** | g_signal quartile vs KCGS | Q4 < Q1 (방향) | weak (verbosity 공선성에 종속) |
| **5 (new)** | 2024 단면 E vs G ρ | E(+) vs G(−) asymmetry | **suggestive** (CI 0 살짝 포함) |

### 10.4 통합 메시지 refinement

| 본 보고서 §5.2 의 통합 메시지 | §10 refinement 후 |
|---|---|
| "4개 alpha 모두 cheap-talk 가설과 정합하는 방향을 가리킨다" | "5개 alpha 가 *부분적으로* cheap-talk 가설과 정합하는 방향을 보이지만, 각 alpha 의 evidence 강도가 *feature construction · 통제 변수 set · 표본 구성* 에 종속됨. 새로 추가된 Alpha 5 는 *E vs G 의 directional asymmetry* 라는 — 단순 통합 ESG 신호로 환원되지 않는 — *suggestive* 차원을 제기" |

### 10.5 §10 한 줄

> *"Alpha 1 의 cheap-talk 정합은 통제 변수 set 의 정의에 조건부 이며, Alpha 5 는 ESG 의 차원별 disclosure-performance gap 가설을 — *suggestive 수준에서* — 새롭게 제기한다. 본 보고서 §1 ~ §9 의 4 alpha narrative 는 방향성으로는 유지되되, 그 강도는 본 §10 에서 *재조정* 된다."*

---

**§10 추가 산출 파일**

- `data/06_analysis/g_signal_orthogonalized_summary.csv` — Alpha 1 refinement (`g_signal_ortho` 잔차)
- `data/06_analysis/cross_section_2024_e_vs_g.csv` — Alpha 5 결과 + bootstrap CI
- `data/06_analysis/refined_evidence_matrix.csv` — Alpha 1 ~ 5 통합 (본 §10.3 의 데이터)
- `08_revised_final_report.md` — 본 §10 이 통합된 canonical final narrative
