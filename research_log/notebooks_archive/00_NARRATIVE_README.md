---
title: "ESG DART · Final Pipeline Narrative README"
date: 2026-05-21
audience: 발표 평가자 · 팀 내부 검토 · 처음 보는 팀원
role: "final/ 시리즈 읽기 순서 + 평가표 매핑 + instability narrative 한 페이지 요약"
---

# Final Pipeline 읽기 가이드

> 이 README는 분석 코드가 아니다. **`notebooks/final/` 시리즈를 어떤 순서로, 어떤 질문을 들고 읽어야 하는지** 안내하는 발표용 navigation 문서다.

---

## 0. 우리 팀이 답하려는 한 줄 질문

> 한국 사업보고서의 ESG 관련 표현은 외부 ESG 평가(KCGS)와 통계적으로 연관되는가?

이 질문은 의도적으로 "**연관**"이라는 단어를 쓴다.
우리는 ESG 등급을 예측하려는 것이 아니다 — **언어와 평가 사이의 패턴을 측정**하려는 것이다. 그리고 그 측정이 얼마나 안정적인지를 동시에 본다.

## 1. 이 프로젝트의 진짜 contribution

다른 팀과 우리 팀이 다른 점은 한 줄로 정리된다.

> **ESG disclosure language signal is unstable, and this instability itself is empirically meaningful.**

즉 우리는 "**더 좋은 ESG predictor**"를 만드는 팀이 아니라, **ESG textual measurement의 fragility(preprocessing sensitivity · tokenizer instability · verbosity dominance · sign reversal · cheap-talk)**을 empirical하게 드러내는 팀이다.

이 framing이 모든 notebook에 일관되게 들어 있어야 한다. 결과가 깨끗하지 않을 때 우리는 그것을 *실패*가 아니라 *발견*으로 읽는다.

## 2. Pipeline narrative 흐름 — 한눈 보기

```
[데이터 lineage]
  00_ingest_v2              표본 구성 · 누락 처리 · firm-year 식별자 체인
  01_section_passage_v2     II/IV/VI 섹션 발췌 · seed 문단 필터

[Preprocessing 선택과 그 fragility]                ← 우리 팀 차별점 layer 1
  02_preprocess_kiwi_v2     Kiwi exp_F 토큰화 (canonical choice)
      └── Robustness insets
           · memberC/01_tokenizer_robustness_kiwi_vs_okt   (tokenizer instability)
           · memberC/02_preprocessing_eval                 (exp_B vs E vs F)
           · memberC/01_token_inspection                   (top-N 토큰 직접 읽기)

[Feature 구성과 measurement validity]              ← 우리 팀 차별점 layer 2
  03_feature_build_v2       seed TF-IDF · esg_tfidf_concentration · 차원별 TF-IDF
  03b_expanded_dictionary_fasttext  fastText 확장 · θ 비교 · 후보 검토
                                    (전처리/ 팀원 notebook 통합)
      └── Robustness inset
           · memberC/02_seed_dictionary_validation         (seed별 개별 ρ)

[측정 타당도 검증]
  04_feature_validation_v2  Spearman + Bootstrap CI + MWU
      └── Robustness inset
           · data/06_validation/spearman_matrix.csv      (exp별 ρ matrix)

[회귀 추정과 instability]                          ← 우리 팀 차별점 layer 3
  05_regression_v2          OLS (M1~M3) + Ordered Logit (M4) + Binary Logit (M5) + VIF
      └── Robustness inset
           · memberC/05_sample_definition_sensitivity      (N-curve sign reversal)

[Cheap-Talk 심화 분석]                              ← 우리 팀 차별점 layer 4
  06_alpha_analysis_v2
      · Alpha 1 ★ Verbosity-Adjusted ESG Score   (verbosity 통제 후 잔여 signal)
      · Alpha 2 ★ Low-Grade Strategic Disclosure (B/C/D firm이 더 쓰는가)
      · Alpha 3 ★ Sign Reversal Diagnosis        (N=30→N=210 부호 역전)
      · Alpha 4   Governance Paradox             (G 어휘 ↑ ↔ G 등급 ↓?)
```

각 v2 notebook 상단에는 이 흐름의 어느 단계인지 명시한 **narrative position 헤더**가 있다. 그 헤더가 "이 notebook은 무엇을 측정/검증하려고 하는가"를 한 문단으로 말해준다.

## 3. 평가표(`04_submission_and_evaluation.md`) 매핑

평가표가 보고서/발표에서 보겠다는 모든 항목이 final/ 어디에 들어 있는지 직접 매핑한다.

| 평가 영역 | 평가표 요구 | 우리 notebook 위치 |
|---|---|---|
| 데이터 이해 | 표본 구성, 누락 처리, timing(`esg_year = fiscal_year + 1`) | `00_ingest_v2` (lineage audit, salvage log) |
| DART lineage | `stock_code`/`corp_code`/`rcept_no`/`fiscal_year` 구분, 추출 로그 | `00_ingest_v2` (rcept_no 14자리 검증, salvage log) |
| 섹션 선택 | II / IV / VI 발췌 정당화 | `01_section_passage_v2` (seed sentence density filter + section breakdown) |
| 텍스트 처리 | 형태소 분석기 / 불용어 / 사용자 사전 선택 정당화 | `02_preprocess_kiwi_v2` (Kiwi + 사용자 사전 + exp_F 설계) + memberC/02 Decision Box |
| Feature 종류 | seed TF-IDF, expanded TF-IDF, fastText, cosine similarity | `03_feature_build_v2` (seed) + `03b_expanded_dictionary_fasttext` (fastText 확장 + θ) |
| Feature 해석 | 각 feature가 무엇을 측정하는지 쉬운 말로 | 각 v2 notebook의 markdown 설명 + `06_alpha_analysis_v2` (verbosity-adjusted) |
| 측정 validity | Spearman 순위상관, t-test/MWU 검증 | `04_feature_validation_v2` (ρ + Bootstrap CI + MWU) + memberC/02_seed_dictionary_validation |
| 모형 선택 | OLS / Ordered Logit / Binary Logit 선택 이유 + 버린 대안 한계 | `05_regression_v2` (M1~M5 + VIF 진단 + Decision Box) |
| 해석과 한계 | 계수 방향·크기, cheap-talk 가능성, 표본 한계 | `05_regression_v2` (해석 셀) + `06_alpha_analysis_v2` (Alpha 1~4) |
| Alpha | 팀이 자체 설계한 추가 검증 | `06_alpha_analysis_v2` (4개 alpha) + memberC/05_sample_definition_sensitivity |
| 재현성 | API key 제거, 위→아래 실행 시 재현 | 모든 v2 notebook (`.env` 환경변수, 산출물 path lineage) |

## 4. Instability narrative — 발표 5분 요약 buffer

발표에서 이 한 페이지가 우리 팀의 색깔을 정한다.

**일반적인 ESG 텍스트 분석 narrative (다른 팀)**

> "ESG 단어를 많이 쓰면 ESG 등급이 높다 / 낮다. ρ = X.XX, p < 0.0X. 따라서 disclosure language는 ESG signal을 포함한다."

**우리 팀 narrative**

> "ESG 단어 빈도와 KCGS 등급 사이의 관계는 (preprocessing, tokenizer, 표본 크기, verbosity 통제) 어느 하나만 바뀌어도 부호가 뒤집힌다. ρ ≈ 0.10–0.20 수준의 약한 신호 위에 verbosity가 더 큰 비중으로 얹혀 있으며, 소표본에서 양의 ρ로 보이던 신호는 N=210으로 확장하면 음수로 역전된다. 이 instability는 분석 실패가 아니라 disclosure language의 본질적 특성 — *cheap-talk 가능성* — 을 empirical하게 드러내는 결과다."

이를 뒷받침하는 4개 evidence pillar:

1. **Preprocessing sensitivity** — `figure2_preprocessing_sensitivity.png`, exp_B/E/F 비교 (memberC/02_preprocessing_eval)
2. **Tokenizer instability** — Kiwi vs Okt 8지표 비교 (memberC/01_tokenizer_robustness)
3. **Verbosity dominance** — `figure3_verbosity_dominance.png`, Alpha 1 verbosity-adjusted (`06_alpha_analysis_v2`)
4. **Sign reversal** — `alpha3_sign_reversal_exp_F.png`, N-curve zone 분석 (memberC/05_sample_definition_sensitivity, Alpha 3)

이 네 가지가 모이면 `figure1_instability_evidence.png` 한 장으로 종합된다.

## 5. Decision Box — 우리 팀의 method log

본 프로젝트의 각 단계는 **Alternative / Choice / Justification / Limitation** 4단 구조로 선택을 기록한다. 결과를 보고 사후에 설정을 바꾸는 p-hacking을 막기 위한 원장이다.

주요 Decision Box 위치:
- 형태소 분석기 선택 (Kiwi vs Mecab vs Okt) — `02_preprocess_kiwi_v2`, memberC/02_preprocess_exp_F
- 섹션 선택 (II + IV + VI vs 전체) — `01_section_passage_v2`
- 문단 필터 (seed 1개 이상 vs 임계치 없음) — `01_section_passage_v2`
- 사전 확장 (seed-only vs fastText θ별) — `03b_expanded_dictionary_fasttext`
- 회귀모형 (OLS vs Ordered Logit vs Binary Logit) — `05_regression_v2`
- Verbosity 통제 변수 정의 — `06_alpha_analysis_v2` Alpha 1

## 6. Forbidden / Preferred 어휘 — 보고서·발표에서 일관 유지

**쓰지 않는다:**
- "예측한다 / 분류한다 / improves ESG / causes / true ESG"

**쓴다:**
- "associated with / positively related to / consistent with / weak-but-significant / 이 표본에서 / 연관이 관찰되었다"

## 7. 실행 재현성 메모

- 모든 입력/출력 경로는 `data/<단계>/...` 와 `outputs/<figures|tables>/...`로 통일.
- API key는 `.env`에만 저장 (코드 상수 금지).
- 각 notebook은 위→아래 실행 시 산출물이 재생산되도록 작성. 단 중간 산출물(parquet/csv)이 이미 있으면 재계산을 생략하는 셀 구조.
- exp_id 인자로 통제: 기본값 `exp_F` (canonical), 비교용 `exp_B`(baseline), `exp_E`(중간).

## 8. 다음 단계 (이 README 이후 작업)

이 통합 정리가 끝났을 때 다음을 점검한다 (`steering checklist`):

- [ ] 결과가 instability narrative를 강화하는가
- [ ] preprocessing contribution이 드러나는가
- [ ] cheap-talk framing이 유지되는가
- [ ] feature validity가 충분히 설명되는가
- [ ] regression 이전의 reasoning이 존재하는가
- [ ] sign reversal을 숨기지 않고 해석하고 있는가
- [ ] weak correlation도 의미 있게 읽고 있는가
- [ ] failure cases를 제거하지 않고 설명하고 있는가
- [ ] tokenizer/section/verbosity 영향이 드러나는가
- [ ] 결과를 prediction이 아니라 measurement problem으로 설명하는가

이 checklist는 `통합 결과 narrative checklist 검증` 단계(task #5)에서 항목별로 채워진다.
