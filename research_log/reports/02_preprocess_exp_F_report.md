# 02_preprocess_exp_F_report.md
## 사업보고서 텍스트 → ESG 토큰: 전처리 설계와 exp_E / exp_F 비교

> **연구 질문 (재확인)**
> 한국 사업보고서의 ESG 관련 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가?
>
> 이 보고서는 그 연구 흐름의 **첫 절반** — "원시 사업보고서 텍스트가 어떻게 분석 가능한 ESG 토큰으로 변환되는가" — 를 다룬다. ESG를 예측하는 것이 아니라, **언어와 성과 사이의 잠재적 간극을 측정 가능한 형태로 만드는 것**이 목적이다.

> **[2026-05-24 RECOVERY PATCH] 공식 stopwords 의존성 복구**
> 본 보고서가 작성될 당시 `src/preprocessor.py` 는 inline hardcoded set 만 사용했고, 공식 의존성인 `data/stopwords_ko_esg.txt` (Notice/03_minimal_analysis_example.md 56행 명시) 를 로드하지 않았다. 33개 공식 토큰 중 14개만 `STOPWORDS_EXTENDED` 와 겹쳤다. 누락된 19개 중 12개(`강화 / 개선 / 계획 / 구축 / 목표 / 성과 / 실시 / 제공 / 지원 / 추진 / 확대 / 활동`)는 사후-Kiwi 토큰 스트림에 실제로 등장했으며, 이는 cheap-talk 가설이 지목하는 전략적 ESG-행동 어휘 그 자체였다. 7개 입자(particles)는 Kiwi 토크나이저가 이미 형태소 단계에서 제거하므로 corpus 영향 0. 본 패치는 `exp_F_official` 변형을 별도 lineage 로 유지하며 (silent overwrite 금지), delta 는 robustness evidence 로 §2 말미와 04 보고서에서 보고된다. 복구 산출물: `data/04_preprocessed/recovery/`, `data/05_features/recovery/`, `outputs/recovery/COMPARISON_30_stage4_robustness_layer.html`.

---

## 1. 전처리 파이프라인 개요

```
원시 사업보고서 (rcept_no)
    └── II. 사업의 내용
    └── IV. 이사의 경영진단 및 분석의견
    └── VI. 이사회 등 회사의 기관에 관한 사항
            │
            ▼
[1] 회사명 변형 제거 ((주)X, ㈜X, X(주), 주식회사 X)
            │
            ▼
[2] 숫자 처리
        exp_E: 모든 숫자 제거 (remove_all)
        exp_F: 단위 결합 숫자만 [NUM]단위로 마스킹 (keep_quantity)
            │
            ▼
[3] 문장 수준 boilerplate 필터  ← exp_E / exp_F 전용
        정규식 18종 (재무제표·주주총회·특수관계인·법인세 등)
        제거된 줄은 별도 로그로 보존 (육안 검증 가능)
            │
            ▼
[4] Kiwi 형태소 분석 — 명사(NNG/NNP)만 추출
            │
            ▼
[5] 불용어 제거 (단, G_SIGNAL_PROTECT 13개는 절대 보호)
        exp_B: STOPWORDS_STANDARD
        exp_E/F: STOPWORDS_EXTENDED + BOILERPLATE_NOUNS
            │
            ▼
[6] joined_text (공백 분리 명사 시퀀스, firm-year 1행)
```

### 1.1 왜 이 순서인가

- 회사명 제거를 가장 먼저: 사명이 그대로 토큰화되면 firm 식별자가 features에 누설된다. ("삼성전기" 같은 토큰이 G-signal로 오분류될 위험).
- 숫자 처리는 형태소 분석 **전**에: Kiwi가 "30%"를 분해하기 전에 [NUM]퍼센트로 잠근다(exp_F). 그래야 "ESG 정량 표현"이라는 신호를 유지할 수 있다.
- boilerplate 문장 필터도 형태소 분석 **전**에: 패턴이 단어 단위가 아니라 "정기주주총회 결의에 의거" 같은 의무공시 문장을 통째로 잡아야 하기 때문이다. 토큰 단계에서는 동일한 단어("주주", "이사회")가 ESG 맥락에서도 등장하므로 잘라낼 수 없다.

### 1.2 G_SIGNAL 보호 정책

KCGS의 G 등급 핵심 평가 항목(이사회 독립성, 감사위원회, 사외이사 등)은 사업보고서 전반에서 IDF가 낮아 일반적인 IDF 기반 필터로는 보존되지 않는다. 그래서 **사전적으로 보호한다:

```
이사 / 감사 / 이사회 / 준법 / 이해관계자 /
사외이사 / 감사위원회 / ESG위원회 / 컴플라이언스 /
위원회 / 지배구조 / 투명성 / 내부통제 / 주주
```

이 13개 토큰은 어떤 불용어 집합에 들어 있더라도 런타임에서 제외(set difference)된다. 만약 보호하지 않으면 STOPWORDS_EXTENDED가 "이사회"·"위원회"를 제거해 G 피처가 통째로 사라진다.
- governance 단어 중에 `이사회, 지배구조` 등과 같은 단어는 사업보고서에 자주 등장하기 때문에 IDF가 낮게 측정됨. 따라서 너무 흔하다는 이유로 제거될 수 있음 -> exp_D에서 발생
	==-> G_SIGNAL_PROTECT로, 흔하지만 제거하면 안되는 dictonary를 만듦
- set_difference: stopword 리스트에 `위원회, 이사회`가 들어있어도 런타임에서 STOPWORDS

### Decision Box — 불용어 집합 강도

| 항목                | 내용                                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| **Alternative**   | (a) minimal (필수 조사만) (b) standard (당사·회사·사업 추가) (c) extended (운영·관리 등 일반어 확장)                                |
| **Choice**        | exp_B = standard (pre-registered baseline), exp_E/F = extended + boilerplate noun set                        |
| **Justification** | standard는 사전 등록 시점에 결정한 baseline이라 분석 후 변경 불가. extended는 결과를 보지 않고도 사전에 합리화되는 추가 제거를 모은 것 — G_SIGNAL은 보호 처리됨 |
| **Limitation**    | extended는 일부 ambiguous 토큰(예: "운영", "관리")이 G/E 의미를 일부 잃을 수 있음. token_taxonomy_exp_A.csv의 수동 분류 결과로 사후 검증      |
- ==일반 NLP = 흔한 단어 제거 / ESG project = 흔하지만 중요한 G 단어는 사전적으로 보호==

>[!summary] G_SIGNAL_PROTECT 정책은 "이사회, 감사위원회"와 같은 governance 핵심 단어가 stopword 처리로 제거되는 걸 막기위해 일부 토큰을 강제로 보존한 전처리 전략임

---

## 2. exp_E vs exp_F — 왜 두 변형이 필요한가

| 차원     | exp_B (baseline) | exp_E          | exp_F             |
| ------ | ---------------- | -------------- | ----------------- |
| 불용어 강도 | standard         | extended       | extended          |
| 숫자 처리  | remove_all       | remove_all     | **keep_quantity** |
| 문장 필터  | 없음               | 18개 패턴         | 18개 패턴            |
| 목적     | pre-reg          | boilerplate 감소 | E + ESG 정량 표현 보존  |
- exp_E와 F의 차이점으로는 ESG 숫자를 지울지, 숫자의 존재감을 남길지에 대한 선택이 있음.
EX) 탄소배출 30% 감축
- exp_E: 탄소배출 감축 / **exp_F: 탄소배출 [NUM]% 감축**

| 추상적 수사 | 정량 disclosure |
|---|---|
| “친환경 경영 강화” | “탄소배출 30% 감축” |
| “ESG 추진” | “재생에너지 1200GWh 도입” |

### 2.1 exp_F를 만든 이유

ESG 공시는 "탄소배출 30% 감축", "재생에너지 1,200GWh 도입" 같은 **정량 표현**이 본질이다. exp_E가 모든 숫자를 제거하면 =="탄소배출 감축" 같은 일반 문구만 남아 "정량 약속을 한 보고서"와 "수사만 늘어놓은 보고서"의 차이가 사라진다.

exp_F는 `\d+\s*(억원|만원|원|%|퍼센트|톤|tCO2|GWh|MW|kWh)` 패턴을 `[NUM]단위`로 마스킹해 정량 표현의 **존재 자체는 유지**하되 액수 자체로 인한 verbosity 편향은 줄인다.

- ==숫자 자체는 제거하되, **정량 표현**은 남겨서 정량 약속 존재 여부만 확인하자
- ==`\d+\s*(억원|만원|원|%|퍼센트|톤|tCO2|GWh|MW|kWh)` -> `[NUM]단위
	- [NUM]단위, 숫자 크기에 대한 정보를 제거해서 verbosity bias 줄일 수 있음

> 이는 단순한 hyperparameter 탐색이 아니라 **연구 가설과 직결되는 설계 결정**이다. cheap-talk 가설을 검정하려면 "구체적 정량 약속"과 "추상적 ESG 수사"를 구분할 수 있어야 하기 때문이다.
- ==숫자 포함 ESG 언어 = more substantive 할 가능성 -> **cheap-talk vs substantive 구분
	- 구체적인 수치와 실행 과정등을 알고 싶기 때문

### 2.2 Precision / Recall Trade-off

- **exp_E**(remove_all): 더 깨끗한 vocabulary, 그러나 ESG 정량 표현 신호 손실 가능 → **precision↑, recall↓**
- **exp_F**(keep_quantity): 정량 표현 보존, 대신 단위가 흔한 산업(에너지·소재)이 약간 과대표현될 수 있음 → **recall↑, precision↓**

현재 결과상 두 변형의 top-30 토큰과 Spearman ρ는 거의 동일(소수점 둘째 자리 일치)이지만, regression 단계에서 두 가지를 robustness check로 함께 보고하는 것이 안전하다.

### Decision Box — exp_E vs exp_F

| 항목                | 내용                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------- |
| **Alternative**   | (a) exp_E만 사용 (b) exp_F만 사용 (c) 둘 다 보고                                                  |
| **Choice**        | 둘 다 보고. exp_F를 main, exp_E를 robustness로 표기                                              |
| **Justification** | 정량 표현 보존이 연구 가설(cheap-talk vs substantive)에 가깝다. 다만 결과 안정성을 위해 두 설정 모두 동일한 방향성을 보이는지 점검 |
| **Limitation**    | 두 변형의 차이가 본 표본에서 매우 작음 → 표본을 키워야 진짜 차이가 드러날 가능성                                         |
>[!summary] exp_E는 숫자를 완전히 제거해서 더 깔끔하지만 정량 ESG 신호가 손실될 가능성 있음. 반면에 exp_F는 숫자를 마스킹([NUM}단위])해서 정량 표현 존재를 유지하여 구체적 ESG 약속 여부를 구분할 수 있음. 따라서 exp_F를 선택함.

>[!point] "ESG 말을 했는가?" 보다 "구체적 ESG 약속을 했는가?"를 구분하려는 시도가 point!

---

## 3. 대표 토큰 (Representative Tokens) — TF top-30

평균 토큰 수가 11,170(exp_B) → 8,774(exp_E/F)로 약 **21% 감소**했고, vocab는 7,048 → 6,780/6,784로 **3.8% 감소**했다. ==token은 많이 줄었지만 vocab는 거의 안 줄었다는 점이 중요하다 — 반복적 boilerplate가 집중적으로 제거됐다는 신호다.
- token 수: 전체 단어 등장 횟수 / vocab 수: 서로 다른 단어 종류 개수
Ex) 이사회 이사회 감사 감사 감사 환경
- token 수=6 / vocab 수=3 (이사회, 감사, 환경)

```
[exp_B]  주주 기준 감사 이사 이사회 환경 공시 위원회 회계 연결 가치 경우
         주식 시장 경영 금융 공정 재무제표 총회 관리 지급 자산 기간 평가
         포함 부채 금액 가능 보고 결정

[exp_E]  주주 감사 이사 환경 이사회 위원회 공시 가치 시장 경영 공정 금융
         주식 지급 평가 총회 배출 포함 결정 보고 사외 가능 지속 거래 에너지
         선임 위원 산업 기술 규정

[exp_F]  (exp_E와 거의 동일 — keep_quantity 효과는 top-30 외부에서 나타남)
```

- **사라진 토큰** (exp_B → exp_E/F): `기준 / 회계 / 연결 / 재무제표 / 부채 / 자산` 등 재무·일반 토큰
- **새로 부상한 토큰**: `배출 / 사외 / 지속 / 에너지 / 선임 / 위원 / 규정` — 모두 ESG 또는 거버넌스 신호
	- ==ESG 분석과 관계 적은 회계 noise를 제거함.
	- E,G 관련 단어들은 증가함.

직관적 판단: ESG 연구자가 위 두 목록을 보면 ==**exp_E/F가 명백히 더 "ESG 같은" 공간이다.**==통계 이전에 대표 토큰이 이 정도로 바뀌었다는 사실 자체가 1차 검증이다.
- representative tokens: 대표 단어 목록
- qualitative validation: 사람이 직접 읽어 진짜 ESG 같아졌는지 검증증

>[!summary] exp_E/F에서는 반복적인 재무 boilerplate token만 크게 줄고 ESG/G 관련 vocabulary는 유지됐기 때문에, "사업보고서 전체 공간"이 "ESG 중심 vocabulary 공간"으로 전처리됐다는 걸 대표 토큰(top-30) 수준에서 확인함.

---

## 4. Feature 통계

5개 firm-year scalar feature 정의 (`src/feature_builder.py`):

| feature                   | 공식                         | 측정하려는 것                  | 예시                               |
| ------------------------- | -------------------------- | ------------------------ | -------------------------------- |
| `total_tokens`            | 명사 토큰 수                    | verbosity (필수 통제 변수)     | 긴 보고서                            |
| `esg_signal_ratio`        | ESG_SIGNAL ÷ total         | E/S 도메인 언어 강도            | 탄소중립                             |
| `g_signal_ratio`          | G_SIGNAL ÷ total           | Governance 언어 강도         | 이사회                              |
| `bp_contamination_rate`   | BOILERPLATE ÷ total        | 잔존 재무 boilerplate        | 재무제표                             |
| `esg_g_relative`          | (E+G) ÷ (E+G+BP)           | boilerplate 대비 상대 신호     |                                  |
| `esg_tfidf_concentration` | seed 어휘 TF-IDF / top-200 합 | 어휘 변별력 (verbosity 부분 통제) | '탄소중립' 과 같은 단어가 핵심 vocabulary인가? |

비율 형태를 쓰는 이유: 보고서 길이가 firm마다 다르므로 단순 카운트는 긴 보고서를 쓰는 firm을 일률적으로 높게 만든다. 다만 비율도 길이 편향을 **완전히** 제거하지 못해 `total_tokens`(또는 `log_tokens`)를 회귀의 통제 변수로 반드시 함께 투입한다.
- ratio + verbosity control

### 시행착오 1 — bp_contamination_rate가 exp_E/F에서 var=0이 되는 문제

문장 단위 boilerplate 필터가 너무 강력해서 거의 모든 firm에서 `bp_count = 0`이 됐다. 결과적으로 exp_E/F의 `bp_contamination_rate`는 상수(degenerate feature)가 되어 Spearman을 계산할 수 없다. 보고에서는 "constant feature — no discriminative power"로 명시하고 exp_B만의 비교 변수로 남긴다.

→ **해석**: 필터 강도가 의도대로 작동했다는 신호. 단, exp_E/F에서는 "boilerplate 잔존 정도"를 더는 측정할 수 없으니 robustness용 cross-experiment 비교가 필수.
- ==boilerplate 제거 성공!

### 시행착오 2 — G_SIGNAL 5종 누락

eval_report.txt 상 14개 보호 토큰 중 5개(`감사위원회`, `투명성`, `컴플라이언스`, `지배구조`, `ESG위원회`)가 top-30에 한 번도 등장하지 않았다. 이는 보호 정책 실패가 아니라 ==**사업보고서 본문 자체에 이 단어가 거의 안 나온다**==는 의미다. ==사업보고서가 KCGS G 평가 항목을 거의 언급하지 않는다는 결과 자체가 cheap-talk 논의에 활용 가능한 발견이다.==(-> 구체적으로 뭘 했는지는 언급X)
- 사업보고서 자체의 governance disclosure 한계 발견
- cheap-talk 가능성: "실질 내용보다 좋은 말만 많을 수 있다"

>[!summary] 좋은 ESG 말은 많이 하는데, 구체적인 실행에 대해서는 언급이 적을 수도 있음. 따라서 "구체 governance disclosure는 적고 일반 ESG 수사는 많다" 보다 "cheap-talk framing과 정합적인 패턴일 수 있다"로 표현하는 게 적절함.

---

## 5. 시행착오 종합

| 문제 | 발견 시점 | 대응 |
|---|---|---|
| **duplicate overlap** | feature 빌드 시 동일 firm-year가 2개 rcept_no로 등장 | rcept_no 우선순위 규칙(정정 > 정기) 적용, log에 기록 |
| **feature row mismatch** | merge 단계에서 KT&G 2024 행이 features_exp_E에는 없고 exp_F에만 존재 | rcept_no NaN 행은 별도 sentinel로 보존 (조작 금지) |
| **finance boilerplate residual** | exp_B top-30에 `회계 / 재무제표 / 부채` 잔존 | 문장 패턴 + BOILERPLATE_NOUNS 두 단계로 exp_E/F에서 제거 |
| **token leakage (회사명)** | 초기 실험에서 `네이버`, `SK이노베이션`이 ambiguous로 분류됨 | `remove_company_names()` 4가지 변형으로 사전 제거 |
| **density threshold 수정** | 초기엔 문장 필터 미적용 → ESG signal이 boilerplate에 묻힘 | 문장 단위 패턴 18종 추가, 제거 줄을 모두 로그로 저장 |
| **sentence filtering 조정** | "감사보고서 첨부"는 boilerplate, "ESG 감사"는 신호 | `감사보고서.*첨부` 패턴으로 명시적 구분 |
| **pilot overlap (n=30)** | 상위 10개 대형주 편중으로 ρ 부호가 양(+)으로 나옴 | n=210 확장 후 부호 역전 확인 (cheap-talk 신호) |
| **validation failure inspection** | extracted_section이 빈 firm-year 발견 | `02_extract_sections_fixed.py`로 fallback 추가 + warning 로그 |
- ==pliot overlap==: 초기 pilot(상위 10개 대형주 중심)에서는 Spearman이 양의 상관으로 나오는데, 표본을 210개로 확장하니 Spearman이 음의 상관으로 나옴.
	- ==표본편향을 제거하니 cheap-talk 패턴 등장
	- Spearman(+): ESG 단어 많을수록 등급이 높아보임

---

## 6. ESG Signal 강화 여부 — 정량 요약

eval_report.txt 기준:

- **Boilerplate 비율 (TF top-30 중 재무/법무)**: exp_B 13.3% → exp_E/F 0.0% (**−13.3%p**)
- **ESG specificity (TF top-30 중 E+G 신호)**: exp_B 16.7% → exp_E/F 16.7% (**변화 없음**, G_SIGNAL이 baseline에도 이미 보호되고 있었기 때문)
	- ESG signal 돋보이게!
- **vocab 변화**: 7,048 → 6,784 (**−3.8%**)
- **평균 토큰**: 11,170 → 8,774 (**−21.5%**)
	- 다양하고 의미있는 단어는 유지하면서 반복 noise만 제거
- **TF-IDF top-30 BP rate**: 13.3% → 0.0%
	- noise token만 줄어듦
- **G_SIGNAL 보호율**: 64.3%로 동일(누락된 5종은 본문에 본래 부재)

> exp_E/F는 ESG 신호를 **추가**한 것이 아니라 boilerplate를 **제거**한 설계다. 즉 분자가 커진 게 아니라 분모가 작아진 것 — 이 점은 결과 해석에서 명시해야 한다

>[!summary] ESG 단어를 새로 많이 만들어낸 게 아니라, nosie를 제거해서 ESG signal을 돋보이게함.

---

## 7. 다음 단계

1. **`03_feature_validation.ipynb` / `03_feature_validation_report.md`** — TF-IDF 정량 검증, KCGS merge, Spearman 상관, cheap-talk 해석
2. **regression** — OLS(`kcgs_grade_7 ~ ESG features + log_tokens`) + Ordered Logit robustness
3. **visualization** — feature 분포, Spearman heatmap, scatter, permutation null
4. **robustness check** — kcgs_grade_4 (4단계 등급)로 동일 분석 반복, 기업 고정효과 추가 고려
5. **언어-성과 간극 해석** — 부호 역전 결과의 cheap-talk 해석 + 대안 가설(역인과, omitted variable) 정리

---

## 8. 핵심 메시지 한 줄

> **exp_E/F는 ESG 신호를 만든 것이 아니라, ESG 신호 옆에 붙어 있던 의무공시 잡음을 정량적으로 줄인 설계다. 그 결과 ESG 언어 강도(g_signal_ratio, esg_tfidf_concentration)가 외부 ESG 평가와 어떻게 연관되는지(또는 어긋나는지)를 비로소 깨끗하게 관찰할 수 있다.**

---

## 9. [2026-05-24 PATCH] exp_F vs exp_F_official — 공식 stopwords 복구 delta

> **읽는 법.** 본 절은 §1-§8 의 본문 수치를 *덮어쓰지 않는다*. 동일한 213-row 코퍼스 위에 공식 stopwords 의존성을 추가 적용했을 때 어떤 feature 가 변하고 어떤 feature 가 변하지 않는지를 보여주는 **robustness 측면 결과**이며, instability 자체를 finding 으로 해석한다.

### 9.1 Corpus-level 변화 (213 firm-years, matched)

| 항목 | exp_F | exp_F_official | Δ | 해석 |
|---|---|---|---|---|
| total_tokens (corpus 합) | 1,041,083 | 1,015,160 | **−25,923 (−2.49%)** | 100% 가 cheap-talk 행위 동사에서 발생 |
| mean tokens / firm-year | 4,887.7 | 4,766.0 | **−121.7** | per-document 평균 −122 tokens |
| esg_signal_count (mean) | 72.58 | 72.58 | 0 | SIGNAL set 토큰은 제거 대상 외 (불변) |
| g_signal_count (mean) | 256.36 | 256.36 | 0 | 동일 |
| g_signal_ratio (mean) | 0.0794 | 0.0811 | +0.0017 (+2.1%) | 분자 불변·분모 축소로 ratio 상승 |
| bp_count (mean) | 0.07 | 0.07 | 0 | boilerplate 무관 |

### 9.2 Spearman vs kcgs_grade_7 — 공식 stopwords 적용 전후

| feature | ρ (F, before) | ρ (F_official, after) | Δρ | 판정 |
|---|---|---|---|---|
| total_tokens | +0.280*** | +0.278*** | −0.001 | ✓ robust |
| esg_signal_count | +0.237*** | +0.237*** | 0 | ✓ invariant |
| g_signal_count | +0.345*** | +0.345*** | 0 | ✓ invariant |
| esg_signal_ratio | +0.083 ns | +0.085 ns | +0.002 | ✓ robust |
| g_signal_ratio | −0.195** | −0.194** | +0.002 | ✓ robust |
| esg_g_relative | −0.050 ns | −0.050 ns | 0 | ✓ invariant |
| bp_contamination_rate | +0.050 ns | +0.050 ns | 0 | ✓ invariant |
| **esg_tfidf_concentration** | **−0.175*** | **−0.007 ns** | **+0.167** | **⚠ 95.8% 붕괴 — preprocessing-sensitive** |

### 9.3 해석

1. **7/8 feature 는 preprocessing-invariant.** 본문 결론 (g_signal_count 우위, g_signal_ratio 의 음의 cheap-talk 패턴, verbosity dominance) 은 stopwords 의존성 복구 후에도 그대로 재현된다.
2. **`esg_tfidf_concentration` 단 하나가 collapse**한다 (ρ −0.175→−0.007). 이 feature 의 기존 음의 상관은 cheap-talk 행위 동사가 top-200 TF-IDF mass 의 일부를 차지하면서 발생한 **verbosity-mediated artifact** 였다. 공식 stopwords 가 그 동사들을 제거하면 ESG seed share 는 KCGS 등급과 사실상 무관해진다.
3. **권고.** 본 보고서 §6-§8 의 `esg_tfidf_concentration` 관련 진술은 03/04 보고서의 patch 절에서 "preprocessing-sensitive — 독립 해석 자제" 로 강등 처리한다 (silent edit 금지).

### 9.4 Decision Box — exp_F_official 변형 추가

| | |
|---|---|
| **Alternative** | (a) exp_F 결과를 silent 로 덮어쓰기 / (b) 버그 상태 유지 / (c) `exp_F_official` 을 parallel 변형으로 추가 |
| **Choice** | (c) |
| **Justification** | lineage 무결성 = 프로젝트 핵심 규칙. 두 결과의 *차이* 자체가 robustness evidence. exp_F 를 지우면 sensitivity 증거 자체가 사라진다. |
| **Limitation** | 본 패치는 post-Kiwi token 필터로 적용 (lightweight rerun), Kiwi 자체를 재실행하지 않음. Kiwi 출력은 동일 설정에서 결정적이므로 12개 명사 토큰에 대해 full re-tokenize 와 동일 결과가 보장된다. 단 dictionary expansion 또는 tokenizer 변경을 동반하면 이 가정은 깨진다. |

### 9.5 산출 파일 (recovery)

- `data/04_preprocessed/recovery/tokenized_exp_F_official.csv`
- `data/04_preprocessed/recovery/stopwords_recovery_diagnostics.json`
- `data/05_features/recovery/features_exp_F_official.csv` / `merged_exp_F_official.parquet`
- `data/05_features/recovery/stopwords_delta_spearman.csv` / `feature_means_delta.csv` / `verbosity_orth_delta.csv` / `bootstrap_ci_before_after.csv` / `sign_stability_before_after.csv`
- `outputs/recovery/COMPARISON_30_stage4_robustness_layer.html` (full visual dashboard)
- patched source: `src/preprocessor.py` (new `STOPWORDS_OFFICIAL`, `STOPWORDS_EXTENDED_PLUS_OFFICIAL`, `load_official_stopwords()`, `get_stopword_set()`, `exp_F_official` config)

---

**산출 파일** (모두 reproducible)

- `data/04_preprocessed/tokenized_exp_{B,E,F}.csv`
- `data/04_preprocessed/features_exp_{B,E,F}.csv`
- `data/04_preprocessed/eval_report.txt` / `eval_comparison.csv` / `eval_delta.csv`
- `data/04_preprocessed/PREPROCESSING_DECISIONS.md` (의사결정 원장)
- `notebooks/02_preprocess_exp_F.ipynb` (본 보고서의 visualization 포함 노트북)
