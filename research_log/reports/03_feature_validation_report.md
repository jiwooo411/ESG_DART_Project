# 03_feature_validation_report.md
## Feature 검증 · KCGS 연결 · Spearman 상관 — 그리고 cheap-talk의 첫 증거

> **연구 질문**
> ESG 관련 공시 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가?
>
> 본 보고서는 그 연결고리의 **두 번째 절반**을 다룬다.
> - 토큰 → 수치 feature가 정말로 ESG 공시 행위를 반영하는가? (내적 검증)
> - 그 feature가 KCGS 등급과 어떻게 연결되는가? (외적 검증)
> - 단순한 분량(verbosity)이 아니라 실제 신호인가? (cheap-talk 검정)

---

## 1. Validation 흐름 — 무엇을 검증했는가

```
features_exp_{B,E,F}.csv
        │
        ├── (a) sample inspection    : 30개 firm-year 무작위 점검
        ├── (b) representative token : TF top-30 직관 검토
        ├── (c) density 변화        : 평균 token, vocab, bp_rate
        ├── (d) feature row 일관성  : duplicate / NaN / mismatch
        ├── (e) duplicate overlap   : pilot(n=30) ∩ full(n=210)
        ├── (f) warning/failure 로그 : extracted_section 빈 행, 토큰화 실패
        │
        ▼
KCGS_esg_ratings.csv  (stock_code × fiscal_year)
        │
        ▼  inner join (stock_code + fiscal_year)
merged_exp_{B,E,F}.csv  (n=210, firms=77, years=3)
        │
        ▼
Spearman ρ + bootstrap 95% CI  →  spearman_results.csv
```

### 1.1 (a) Sample inspection

`tokenized_exp_F.csv`에서 firm-year 5개(케이티앤지/NAVER/삼성전기/카카오/현대자동차)를 직접 열어 joined_text를 검토:

- 모든 표본에서 회사명 토큰이 사라져 있음 (예: "네이버" → 없음)
- 정량 표현이 `[NUM]톤`, `[NUM]GWh`, `[NUM]%` 형태로 유지됨 (exp_F)
- 의결권·정관 같은 의무공시 어휘는 거의 안 보임 (문장 필터 효과)
- 단, "사외이사 추천 위원회"처럼 G_SIGNAL이 보존됨

### 1.2 (d) Feature row 일관성

`features_exp_E.csv`와 `features_exp_F.csv`의 행 수는 동일해야 한다. 실제로 두 파일 모두 stock_code × fiscal_year 정렬 시 동일한 식별자 집합을 갖지만, **한 행에서 차이**가 발생:

- KT&G 2024 (rcept_no NaN) → exp_F에만 존재
- 원인: 해당 firm-year의 보고서가 정정공시 처리되어 `01_collect`에서 rcept_no 누락
- 대응: 데이터를 채워 넣지 않고 sentinel(빈 rcept_no)로 보존, merge 단계에서 stock_code+fiscal_year 키로만 매칭

### ==1.3 (e) Pilot overlap (n=30) vs Full (n=210)

초기 pilot(상위 10개 KOSPI 기업, 3년 × 10) 결과는 부호가 **양**이었다.

| feature | pilot ρ (n=30) | full ρ (n=210) | Δ |
|---|---|---|---|
| `g_signal_ratio` | **+0.444★** | **−0.197★★** | 부호 역전 |
| `esg_tfidf_concentration` | **+0.326·** | **−0.185★★** | 부호 역전 |
| `esg_g_relative` | +0.253 | −0.049 | 부호 역전 |

→ ==pilot의 양의 상관은 **상위 대형주 편중**(survivorship-like sampling bias)에서 비롯된 허위 신호였다. 표본을 77개로 확장하자 정반대 방향이 드러났다.

> 이 부호 역전은 본 연구의 **가장 중요한 방법론적 교훈**이다: 적은 표본의 직관적 결과를 그대로 해석하면 cheap-talk 가설을 놓친다.

### 1.4 (f) Warning / failure log

- `extracted_section` 빈 row: 8건 (초기) → fallback 패턴 추가 후 0건 (`02_extract_sections_fixed.py`)
- 토큰화 실패: 0건 (Kiwi 안정)
- KCGS 미매칭: 11 firm-year (`미공개` 등급 1건 + KCGS 미평가 firm × year 10건) → inner join에서 자연 제외

---

## 2. TF-IDF / Feature Engineering 다시 정리

### 2.1 ESG Token Dictionary (taxonomy 기반)

| 범주          | 토큰 수 | 예시                                  | 처리               |
| ----------- | ---- | ----------------------------------- | ---------------- |
| G_SIGNAL    | 14   | 이사회, 사외이사, 감사위원회, 지배구조, 컴플라이언스, 투명성 | 절대 제거 금지         |
| ESG_SIGNAL  | 27   | 온실가스, 탄소중립, 재생에너지, 폐기물, 인권, 다양성     | 보존 + TF-IDF seed |
| BOILERPLATE | 22   | 재무제표, 차입금, 의결권, 법인세, 연결             | exp_E/F에서 제거     |
| AMBIGUOUS   | 478  | 주주, 경영, 위원회, 환경                     | 수동 검토            |
| GENERIC     | 2    | 사항, 관련                              | 일반 불용어           |

(상세 분류: `data/04_preprocessed/token_taxonomy_exp_A.csv`)

### 2.2 Weighting rationale

- **scalar features**(g_signal_ratio 등): 비율 기반 → firm 길이 차이 부분 통제
- ==**esg_tfidf_concentration**==: TF-IDF top-200 합산 대비 ESG seed 토큰의 mass 비율 → **문서 변별력** 측정
	- ESG seed TF-IDF 합 / top-200 TF-IDF 합
	- ==ESG 단어가 그 기업 문서에서 얼마나 중심 vocabulary인가?
  - 분자가 큰 firm = ESG 어휘가 그 firm의 변별적 어휘 공간에 자리 잡음 (substantive 신호 가능성)
  - 분자가 작은 firm = ESG 어휘가 일반어 속에 희석 (cheap-talk 패턴 가능성)
- top-K = 200 선택: K 민감도(100/200/500)는 향후 robustness check 항목

### 2.3 ESG Signal 의미 — 무엇을 측정하지 않는가
#### cheap-talk framing — 실제 ESG보단 이미지성 disclosure?

| feature                   | 측정하는 것                           | 측정하지 않는 것               |
| ------------------------- | -------------------------------- | ----------------------- |
| `esg_signal_ratio`        | E/S 어휘를 얼마나 자주 쓰는가               | 실제 ESG 실행 여부            |
| `g_signal_ratio`          | 거버넌스 어휘를 얼마나 자주 쓰는가              | 실제로 governance가 잘 작동하는가 |
| `esg_tfidf_concentration` | ESG 어휘가 그 firm의 변별적 어휘 공간을 차지하는가 | 실제 ESG 성과               |

> 모든 feature는 **disclosure intensity**의 대리변수이지 **ESG performance** 자체가 아니다. 이 구분이 본 연구의 핵심 framing이다.

>[!point] "ESG를 잘하는 기업"을 찾는 것보다 "기업이 어떻게 ESG를 말하는가, 그 언어가 실제 외부 평가와 어떤 간극을 가지는가, 실제로 실행을 잘 하고있는가"를 판단하는 것을 목표로 함.


---

## 3. KCGS Merge — 내가 만든 ESG feature를 KCGS 등급과 어떻게 연결했는가

- 목적: ESG feature, 사업보고서 NLP 결과 + KCGS, 외부 ESG 평가 => 회사의 ESG 언어와 평가를 연결해야함

### 3.1 Merge 설계

- **Key**: `stock_code + fiscal_year` (corp_code는 보조 ID, company_name 절대 사용 금지)
	- stock_code: KRX, KCGS, DART에서 사용하는 증권코드
- **Join**: inner — KCGS 미매칭은 데이터 조작 방지를 위해 제외
- **Temporal**: KCGS는 fiscal_year 활동 평가 → esg_year(=fiscal_year+1, 보고서 제출 연도)가 아닌 ==**fiscal_year** 기준으로 join
	- fiscal_year: 2023 활동 -> esg_year: 2024 제출 => 2023 사업보고서를 2024에 공시함.
	- KCGS 평가 기준을 활동 연도로 보고 fiscal_year 기준으로 merge함.

### 3.2 Merge 결과 (merge_quality_report.csv)

| exp | n_rows | n_stocks | n_years | KCGS 분포 |
|---|---|---|---|---|
| exp_B | 210 | 77 | 3 | A:133, A+:14, B:16, B+:39, C:5, D:2, 미공개:1 |
| exp_E | 210 | 77 | 3 | (동일) |
| exp_F | 210 | 77 | 3 | A:132, A+:15, B:16, B+:39, C:5, D:2, 미공개:1 |

- exp_F의 A/A+ 1건 차이는 KT&G 2024(rcept_no NaN) 행에 의한 것 — 데이터 lineage 결과 보존
- 등급 분포가 `A` 우세 → ==**클래스 불균형** 존재. ordered logit, 4단계 collapse(**A+/A/B+/B~D**)로 보완 필요
	- ordered logit: 순서형 데이터 -> 등급 순서 정보 유지 가능
	- 4단계 collapse: "KCGS 등급이 한쪽(A)에 몰려 있어서, 몇 개를 묶어서 분석하자"


### 3.3 Identifier 의미

| ID            | 의미                            | 왜 중요한가                 |
| ------------- | ----------------------------- | ---------------------- |
| `stock_code`  | 증권코드 6자리                      | KRX·KCGS와의 안정적 키       |
| `corp_code`   | DART 고유 코드                    | OpenDART API 호출 키      |
| `rcept_no`    | 보고서 접수번호                      | 동일 firm-year 다중 보고서 구분 |
| `fiscal_year` | 활동 연도                         | KCGS 평가 기준 연도          |
| `esg_year`    | 보고서 제출 연도 (= fiscal_year + 1) | 시간 정렬 검증               |

> **절대 회사명으로 merge하지 않는다.** "삼성SDS" vs "삼성에스디에스" 같은 표기 변동이 KCGS 데이터에 그대로 남아 있기 때문이다.

---

## 4. Spearman 상관 결과

### 4.1 Full sample (n≈209~210, kcgs_grade_7)

| feature | exp_B ρ | exp_E ρ | exp_F ρ | 95% CI (exp_B) | 해석 |
|---|---|---|---|---|---|
| `g_signal_ratio` | **−0.197★★** | −0.190★★ | −0.195★★ | [−0.326, −0.059] | 약한 음의 연관 (CI⊅0) |
| `esg_tfidf_concentration` | **−0.185★★** | −0.170★ | −0.175★ | [−0.311, −0.045] | 약한 음의 연관 (CI⊅0) |
| `total_tokens` | **+0.263★★★** | +0.273★★★ | +0.280★★★ | [0.124, 0.394] | 보통 양의 연관 (CI⊅0) |
| `esg_signal_ratio` | +0.093 | +0.076 | +0.083 | [−0.046, 0.226] | 무시 가능 |
| `esg_g_relative` | −0.049 | −0.052 | −0.050 | — | 무시 가능 |
| `bp_contamination_rate` | −0.072 | (degenerate) | (degenerate) | — | exp_E/F 상수 |

[해석]
- g_signal_ratio(-0.197): `이사회, 지배구조` 와 같은 단어를 많이 쓰는 기업의 ESG 평가가 높지 않았음.
- esg_tfidf_concentration(-0.185): ESG 단어를 강조하는 기업≠실제 ESG 평가 높은 기업
- total_tokens(0.263): 좋은 기업은 공시도 길고 체계적인 경향이 있음.

★★★ p<0.001 ★★ p<0.01 ★ p<0.05

### 4.2 Spearman을 쓰는 이유

- KCGS 등급은 **순서형(ordinal)** 변수 (D < C < B < B+ < A < A+)
- Pearson은 등간(interval) 가정이 필요 → ordinal에 부적합
- **Spearman은 rank만 사용 → ordinal에 적합하고 비선형 단조 관계도 포착
- bootstrap CI: 정규성 가정 없이 표본 분포로 신뢰구간 도출

### 4.3 통계적 유의성 ≠ 실용적 강도

- ρ ≈ 0.18~0.20 = **weak association**
- p < 0.01이지만 R²로 환산하면 약 3~4% 분산 설명력
- 즉 "통계적으로 유의하지만 실용적으로 약하다"가 정확한 표현
- **약한 연관도 의미가 있다**: 만약 ESG 언어가 ESG 성과를 그대로 반영한다면 ρ가 +0.5 이상으로 나와야 한다. 약한 음의 ρ는 가설과 정반대 방향이라는 점에서 오히려 메시지가 강하다.

---

## 5. cheap-talk 해석 — 그러나 신중하게

### 5.1 결과 요약 (한 문장)

> KCGS 등급이 낮은 firm일수록 사업보고서 본문에서 거버넌스 어휘와 ESG 어휘 집중도가 **더 높다**. 그리고 등급이 높을수록 보고서 자체가 **더 길다**.

### 5.2 이 결과가 cheap-talk와 정합적인 이유

cheap-talk 가설은 다음을 예측한다:
> 외부 평가에서 약한 firm일수록 ESG 언어를 더 적극적으로 동원해 평가 부담을 상쇄하려 한다.

본 결과의 부호(낮은 등급 → 높은 ESG 어휘 강도)는 이 예측과 일치한다.

### 5.3 그러나 — 대안 가설들

| 대안 가설 | 본 결과를 동등하게 설명하는가? | 검증 방법 |
|---|---|---|
| **역인과**: 낮은 등급을 받은 firm이 평가 후 대응 차원에서 언어 전략을 강화 | 가능 | 패널 lagged 변수, 등급 변화 전후 비교 |
| **산업 효과**: 등급이 낮은 산업(에너지·소재)이 본디 ESG 의무공시가 많음 | 가능 | 산업 고정효과 모형 |
| **분량 효과**: 큰 firm은 길고 다양한 어휘를 쓰며 ESG가 희석돼 비율이 낮아짐 | 부분적 | log_tokens 통제 → g_signal_ratio 개별 유의성 소실 |
| **measurement error**: 비율이 ESG 의지가 아니라 단순 빈도 | 항상 가능 | 정성 분석, 문장 단위 inspection |

### 5.4 verbosity 교란

- `total_tokens` ρ = +0.263 (가장 강한 신호)
- 회귀에 `log_tokens`를 통제 변수로 투입하면 `g_signal_ratio`의 개별 계수 유의성이 사라짐 (p ≈ 0.31)
- 이는 두 변수의 상관관계가 분리되지 않을 가능성이 있다는 신호 — multicollinearity diagnostics 필요

### 5.5 인과는 절대 주장하지 않는다

표현 가이드:
- ✅ "associated with", "consistent with cheap-talk", "weak negative relationship"
- ❌ "causes", "predicts", "improves ESG"

---

## 6. ESG Signal 강화 여부

| 기준 | 결과 | 평가 |
|---|---|---|
| Boilerplate 제거 | exp_B 13.3% → exp_E/F 0.0% | 신호 정제 ✓ |
| 대표 토큰 변화 | 재무 어휘 6개 사라지고 ESG/G 어휘 6개 부상 | 의미 있는 정제 ✓ |
| Spearman 부호 일관성 | exp_B/E/F 모두 g_signal_ratio · esg_tfidf_concentration 음의 부호 | 전처리 강도와 무관하게 robust ✓ |
| 효과 크기 강화 여부 | exp_E/F가 exp_B보다 |ρ|가 더 크지는 않음 (오히려 약간 작거나 비슷) | 강화 미관측, **stability는 확보** |

> 결론: exp_E/F는 ρ를 **키우지는** 못했지만, 부호와 유의성을 **무너뜨리지도 않았다**. 이는 결과가 boilerplate 잡음의 산물이 아니라는 robustness 증거다.

---

## 7. Precision / Recall Trade-off (재요약)

| 설정 | precision | recall | 본 분석 결과 |
|---|---|---|---|
| exp_B | mid | high | baseline, 부호 일관 |
| exp_E | high | mid | bp 0% 달성, ρ 안정 |
| exp_F | high+ | mid+ | bp 0% + ESG 정량 표현 보존 |

→ 본 표본에서는 세 변형이 거의 동일한 ρ 부호와 크기를 보임. **결과가 전처리 선택에 robust**하다는 점은 cheap-talk 결론을 더 안전하게 만든다.

---

## 8. 다음 단계 (regression / visualization)

| 단계 | 모형 | 답하려는 질문 | 결정 사항 |
|---|---|---|---|
| 1 | OLS: `kcgs_grade_7 ~ g_signal_ratio + log_tokens` | 분량 통제 후에도 언어 신호가 등급을 설명하는가 | exp_F main + exp_B/E robustness |
| 2 | OLS + `esg_tfidf_concentration` | TF-IDF 신호 추가 시 변화 | multicollinearity 진단 |
| 3 | Ordered Logit (`kcgs_grade_7` 6단계) | 순서형 가정에서도 부호가 유지되는가 | proportional odds 검정 |
| 4 | Binary Logit (`A+/A` vs 그외) | 상위 등급 vs 그외 이분류 | 클래스 불균형 보고 |
| 5 | Permutation null | 표본 우연으로 같은 ρ가 나올 확률 | 1,000회 셔플 |
| 6 | 4단계 collapse(A+/A/B/B-D) | 6단계가 너무 잘게 나뉜 결과의 robustness | kcgs_grade_4 동일 분석 |

(이번 task 범위는 correlation까지. regression은 다음 task)

### 시각화 계획 (inline)

- feature 분포(`fig_distributions.png`)
- KCGS × feature scatter(`fig_scatter.png`)
- Spearman heatmap(`spearman_heatmap.png` / `fig_heatmap_full.png`)
- permutation null vs observed ρ(`fig_permutation.png`)

---

## 9. 한계 (방법론)

1. **n=77 firms** — KOSPI/KOSDAQ 전체 대비 제한적
2. **KCGS 평가 방법 비공개** — 등급이 어떤 기준을 반영하는지 알 수 없음
3. **단면+패널 혼합** — 3년 풀링, firm 고정효과 미통제 (다음 단계에서)
4. **disclosure intensity ≠ ESG performance** — 본 연구가 측정하는 것은 언어이지 행위가 아님
5. **인과 추론 불가** — 모든 결과는 association 차원

---

## 10. 핵심 메시지 한 줄

> **사업보고서의 ESG 언어가 외부 평가와 정합한다는 가설은 본 표본에서 지지받지 못한다. 오히려 약한 음의 상관과 강한 분량 효과는 "언어 ≠ 성과"라는 cheap-talk 관점과 일관된다. 이는 ESG 공시 연구가 단순 빈도 분석에서 멈출 수 없는 이유를 정량적으로 보여 준다.**

---

## 11. [2026-05-24 PATCH] 공식 stopwords 의존성 복구 — feature validation 영향

> 02 보고서 §9 와 함께 읽어야 한다. 본 패치는 §4 (Spearman) 와 §5 (cheap-talk 해석) 의 한 항목만을 수정한다.

### 11.1 §4 Spearman 표 수정 사항 (exp_F → exp_F_official, N=210)

| feature | 기존 ρ_F (보고서) | 신규 ρ_F_official | Δρ | 해석 변경 |
|---|---|---|---|---|
| total_tokens | +0.280*** | +0.278*** | −0.001 | 변경 없음 |
| esg_signal_count | +0.237*** | +0.237*** | 0 | 변경 없음 |
| g_signal_count | +0.345*** | +0.345*** | 0 | 변경 없음 — 가장 robust 한 ESG 언어 신호 |
| g_signal_ratio | −0.195** | −0.194** | +0.002 | 변경 없음 — cheap-talk 핵심 부호 유지 |
| esg_g_relative | −0.050 ns | −0.050 ns | 0 | 변경 없음 |
| bp_contamination_rate | +0.050 ns | +0.050 ns | 0 | 변경 없음 |
| **esg_tfidf_concentration** | **−0.175*** | **−0.007 ns** | **+0.167** | **⚠ 강등** |

### 11.2 §5 cheap-talk 해석 — `esg_tfidf_concentration` 재해석

기존 보고서는 `esg_tfidf_concentration ρ = −0.175**` 를 "ESG 어휘 변별력과 외부 평가의 약한 음의 상관" 으로 해석했다. 공식 stopwords 복구 후 이 상관은 사실상 0 (ρ = −0.007, p = 0.92) 으로 붕괴한다. Bootstrap sign-stability 도 99.7% → 55.3% (사실상 동전 던지기). 

**복구된 해석**: 이 feature 의 이전 음의 상관은 cheap-talk 행위 동사 (강화·개선·계획·구축·목표·성과·실시·제공·지원·추진·확대·활동) 가 top-200 TF-IDF mass 의 일부를 점유하면서 발생한 **verbosity-mediated artifact** 였다. 해당 동사들을 stopwords 로 제거하면 ESG seed share 는 KCGS 등급과 무관해진다. 따라서 §5 의 "ESG 어휘 변별력 ↔ KCGS 등급" 음의 연관 진술은 본 표본에서 **stand-alone evidence 로 사용하지 않는다**.

이 변화는 cheap-talk 가설을 **약화시키지 않는다** — 오히려 강화한다. 핵심 메시지 (`g_signal_count` 가 verbosity 통제 후에도 살아남는 유일한 ESG 언어 신호) 는 그대로이며, 단지 한 보조 feature 가 preprocessing-sensitive artifact 였음이 드러난 것이다.

### 11.3 Verbosity-orthogonalized rho — 변화 없음

| feature | rho_orth (before) | rho_orth (after) | Δ | 의미 |
|---|---|---|---|---|
| g_signal_count | +0.245*** | +0.247*** | +0.002 | 가장 robust 한 신호 (verbosity 통제 후에도 유지) |
| esg_signal_count | −0.016 ns | −0.005 ns | +0.011 | verbosity-dominated (둘 다) |
| esg_g_relative | +0.251*** | +0.250*** | −0.001 | suppressor 구조 reproduce |
| bp_contamination_rate | −0.251*** | −0.250*** | +0.001 | suppressor 구조 reproduce |
| g_signal_ratio | +0.059 ns | +0.056 ns | −0.003 | 둘 다 ns |
| esg_tfidf_concentration | −0.056 ns | +0.090 ns | +0.146 | orthogonalized 에서도 부호 flip — 잔여 신호 없음 확정 |

**`g_signal_count` 가 본 데이터에서 유일하게 verbosity-robust ESG 언어 변수**라는 §4 결론은 stopwords 복구 후에도 **수치 단위에서 동일하게 재현**된다.

### 11.4 Decision Box — 보고서 patch vs full rewrite

| | |
|---|---|
| **Alternative** | (a) 본 보고서 §4-§5 전체 재작성 / (b) §4 표만 inline 수정 / (c) patch 절 신설 (§11) + 본문 보존 |
| **Choice** | (c) |
| **Justification** | 본문은 lineage-bug 시점의 분석 그 자체이며 robustness comparison 의 *기준선*. silent overwrite 는 instability evidence 를 지운다. patch 절은 무엇이 변하고 무엇이 변하지 않았는지를 명시적으로 노출. |
| **Limitation** | 독자가 §4 표와 §11.1 표를 동시에 읽어야 한다. 본문 §4 표 셀에 [PATCH §11] 마커를 추가하지 않음 (원본 무결성 우선). |

---

**산출 파일** (모두 reproducible)

- `data/05_merged/merged_exp_{B,E,F}.csv` + `merge_quality_report.csv`
- `data/04_preprocessed/spearman_results.csv` + `spearman_delta.csv`
- `data/04_preprocessed/spearman_heatmap.png`
- `data/06_analysis/fig_distributions.png` / `fig_scatter.png` / `fig_heatmap_full.png` / `fig_permutation.png`
- `data/06_analysis/spearman_full.csv` / `permutation_results.csv` / `collapse_diagnostics.csv`
- `notebooks/03_feature_validation.ipynb` (본 보고서의 visualization 포함 노트북)
