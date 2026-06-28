---
title: "Final Pipeline · Narrative Checklist 검증 보고서"
date: 2026-05-21
audience: 발표 직전 자체 점검 · 교수님 가이드 정합성 체크
companion: "00_NARRATIVE_README.md"
---

# Narrative Checklist — 통합 결과 검증

> 본 문서는 steering document의 checklist를 `notebooks/final/` 통합 결과에 대해 항목별로 점검한 자체 평가 보고서다. 발표 직전 한 번 더 훑기 위한 *행위 가능한* 체크리스트다.

각 항목은 다음 4단으로 채운다.

- **상태**: ✅ 충족 / ⚠ 부분 충족 (보강 권장) / ❌ 미충족 (필수 보강)
- **증거 위치**: 어느 notebook · 어느 셀 · 어느 산출물에 해당 내용이 있는가
- **부족한 점**: 한 줄로 (있다면)
- **다음 보강 액션**: (있다면)

---

## 1. 결과가 instability narrative를 강화하는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `00_NARRATIVE_README.md` §1, §4 — instability를 한 줄 contribution으로 명시
  - `02_preprocess_kiwi_v2` Robustness Inset — preprocessing sensitivity figure + Decision Box
  - `04_feature_validation_v2` Robustness Inset — exp별 ρ matrix
  - `05_regression_v2` Robustness Inset — N-curve sign reversal + robustness_by_exp.csv
  - `06_alpha_analysis_v2` — Alpha 1~4 모두 instability evidence pillar로 작동
  - `outputs/figures/figure1_instability_evidence.png` — 종합 figure 존재
- **부족한 점:** Alpha figure(alpha3_sign_reversal_exp_F.png 등)가 발표 슬라이드 톤으로 보일 만큼 캡션이 자세한지는 figure 자체 점검 필요.
- **다음 보강 액션:** 발표 직전 figure1/2/3 캡션을 \"우리 팀 한 줄 narrative\"로 다시 쓴다.

## 2. preprocessing contribution이 드러나는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `02_preprocess_kiwi_v2` Narrative Position 헤더에 \"우리 팀 차별점 layer 1\" 명시
  - 같은 노트북 Robustness Inset의 Decision Box (Alternative/Choice/Justification/Limitation)
  - `memberC/02_preprocessing_eval`, `memberC/01_tokenizer_robustness_kiwi_vs_okt`로 cross-reference
  - `data/04_preprocessed/eval_comparison.csv`, `eval_delta.csv` — 정량 비교 산출물
- **부족한 점:** preprocessing 선택을 *methodological contribution*으로 부르는 한 문장이 README에는 있지만 본문 inset에는 약함.
- **다음 보강 액션:** 02 inset 해석 셀에 한 줄 추가 — \"preprocessing 선택 자체가 우리 팀의 첫 번째 methodological contribution이다\".

## 3. cheap-talk framing이 유지되는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `00_NARRATIVE_README.md` §1, §4 — \"language-performance gap\" 일관 사용
  - `06_alpha_analysis_v2` 본문 markdown — Alpha 1 verbosity-adjusted, Alpha 2 low-grade strategic, Alpha 4 governance paradox가 모두 cheap-talk 가설의 직접 검증
  - `05_regression_v2` Narrative Position 헤더의 금지 어휘 reminder
  - `03b_expanded_dictionary_fasttext` §7 — 확장 사전이 cheap-talk를 *증폭시킬* 가능성을 frame
- **부족한 점:** 발표 슬라이드에서 cheap-talk 정의를 1줄 문장으로 줄 수 있는 \"표준 정의문\"이 따로 정리되어 있지 않다.
- **다음 보강 액션:** README §1 또는 §4에 \"cheap-talk 정의 한 줄 (발표용)\" 줄을 추가한다.

## 4. feature validity가 충분히 설명되는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `03_feature_build_v2` 본문 — 각 feature(g_signal_ratio, esg_tfidf_concentration, seed_tfidf_X)가 무엇을 측정한다고 가정하는지 설명
  - `04_feature_validation_v2` 전 구간 — Spearman + Bootstrap CI + MWU
  - `03b_expanded_dictionary_fasttext` §4 — 희소 seed 진단으로 seed-only 측정의 한계 노출
  - 평가표 매핑은 README §3 표로 정리
- **부족한 점:** Bootstrap CI가 0을 가로지르는 feature가 어떤 것인지 *명시적 목록*이 본문에 없을 수 있음.
- **다음 보강 액션:** 04 본문 또는 inset 해석 셀에 \"Bootstrap CI가 0을 가로지르는 feature 목록\" 표 한 개를 추가하면 instability 증거가 한층 강해진다.

## 5. regression 이전의 reasoning이 존재하는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `04_feature_validation_v2`가 `05_regression_v2`보다 먼저 옴 — Spearman / MWU 결과로 regression 진입을 *정당화*하는 순서
  - `04` Narrative Position 헤더 — \"regression 직행은 metholodological short-circuit이다\" 명시
  - `00_NARRATIVE_README.md` §3 평가표 매핑 — \"측정 validity\" 항목이 \"모형 선택\"보다 먼저 등장
- **부족한 점:** 없음
- **다음 보강 액션:** 없음

## 6. sign reversal을 숨기지 않고 해석하고 있는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `06_alpha_analysis_v2` Alpha 3 \"Sign Reversal Diagnosis (N=30→N=210)\"가 *명시적 alpha 제목*으로 존재
  - `05_regression_v2` Robustness Inset 해석 — sign reversal을 \"empirical finding\"으로 명시
  - `outputs/figures/alpha3_sign_reversal_exp_F.png` — figure 존재
  - `memberC/05_sample_definition_sensitivity` — N-curve 본격 분석
- **부족한 점:** 없음 — sign reversal은 \"숨기지 않고\"가 아니라 *우리 팀의 핵심 finding*으로 격상되어 있다.
- **다음 보강 액션:** 없음

## 7. weak correlation도 의미 있게 읽고 있는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `04_feature_validation_v2` Narrative Position — \"weak-but-significant\" 영역 해석이 cheap-talk의 정량적 토대라고 명시
  - `00_NARRATIVE_README.md` §4 — ρ ≈ 0.10–0.20 수준 명시
  - 평가표 line 89도 동일 표현 사용 — 정합
- **부족한 점:** 본문 inset 해석 셀의 어조가 평가표 어조와 어느 정도 일치하는지 발표 직전 점검 필요.
- **다음 보강 액션:** 발표 슬라이드에 \"weak ρ ≠ 무신호\"를 1행 메시지로 추가.

## 8. failure cases를 제거하지 않고 설명하고 있는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `00_ingest_v2`의 lineage audit + salvage log
  - `data/01_raw/failed_logs.csv`, `data/02_sections/section_failed_logs.csv` — 실패 행을 *지우지 않고 기록*
  - `03b_expanded_dictionary_fasttext` §2, §6 — \"honest gap statement\"로 코드베이스 미충족 부분을 *명시*
  - 평가표 line 58 정합 — \"실패 행을 가짜 0으로 채우지 않는다\"
- **부족한 점:** 없음
- **다음 보강 액션:** 없음

## 9. tokenizer / section / verbosity 영향이 드러나는가

- **상태:** ✅ 충족
- **증거 위치:**
  - **Tokenizer**: `memberC/01_tokenizer_robustness_kiwi_vs_okt` → `final/02` Robustness Inset이 cross-reference
  - **Section**: `01_section_passage_v2`의 sentence density filter + Decision Box
  - **Verbosity**: `06_alpha_analysis_v2` Alpha 1 verbosity-adjusted score, `outputs/figures/figure3_verbosity_dominance.png`, `outputs/figures/alpha1_verbosity_quadrant_exp_F.png`
  - `total_word_count` 통제: `05_regression_v2` 본문 OLS 모형 (M1~M3 비교)
- **부족한 점:** verbosity 통제 변수의 *정확한 정의*가 본문 어느 셀에 있는지 cross-reference가 약할 수 있음.
- **다음 보강 액션:** 06 Alpha 1 markdown에 \"verbosity 정의: `log_tokens` 또는 `total_tokens`\" 한 줄 명시 (이미 컬럼은 features_exp_F.parquet에 존재).

## 10. 결과를 prediction이 아니라 measurement problem으로 설명하는가

- **상태:** ✅ 충족
- **증거 위치:**
  - `00_NARRATIVE_README.md` §0, §1, §6 — \"예측이 아니다\" / \"measurement\" / 금지 어휘 명시
  - `05_regression_v2` Narrative Position 헤더 — 금지 어휘 reminder
  - `06_alpha_analysis_v2` Narrative Position 헤더 — *measurement problem* 한 줄 finding
  - 평가표 line 89, 142-147 정합 — \"연관이지 인과 아님\" 일관 사용
- **부족한 점:** 없음
- **다음 보강 액션:** 없음

---

## 11. Steering Document 추가 항목 — 빠진 것이 있는가

### 우리 팀만의 핵심 색깔 (steering doc 인용)

- [x] **preprocessing sensitivity** — `02` Robustness Inset, `figure2_preprocessing_sensitivity.png`
- [x] **tokenizer instability** — `memberC/01_tokenizer_robustness`, `final/02` cross-ref
- [x] **verbosity dominance** — `06` Alpha 1, `figure3_verbosity_dominance.png`
- [x] **sign reversal** — `06` Alpha 3, `figure alpha3_sign_reversal_exp_F.png`
- [x] **disclosure cheap-talk** — `06` Alpha 2 (low-grade strategic)
- [x] **token survival instability** — `memberC/01_token_inspection` + `final/02` cross-ref
- [x] **measurement fragility** — `03b` §7 + `04` Robustness Inset
- [x] **\"ESG language signal is unstable, and this instability itself is empirically meaningful\"** — README §1과 `06` Narrative Position 헤더에 동일 문장 박혀 있음

### 평가표 (04_submission_and_evaluation.md) 매핑 누락 점검

- [x] 표본 구성 / 누락 처리 / timing — `00_ingest_v2`
- [x] 섹션 선택 정당화 — `01_section_passage_v2` Decision Box
- [x] feature 선택 / 해석 — `03_feature_build_v2`
- [x] expanded dictionary / fastText / θ 비교 / 후보 직접 검토 — `03b_expanded_dictionary_fasttext` (honest gap 포함)
- [x] Spearman / t-test / MWU — `04_feature_validation_v2`
- [x] OLS / Ordered Logit / Binary Logit 선택 이유 — `05_regression_v2` Robustness Inset Decision Box
- [x] 계수 해석 / 효과 크기 — `05` 본문 + `06` alpha
- [x] cheap-talk 검토 — `06` Alpha 1, 2, 4
- [x] 알파 분석 — `06` Alpha 1~4
- [x] 인과 ≠ 연관 — `05`, `06` 헤더 + README §6
- [x] API key 제거 / 환경변수만 사용 — README §7 명시
- [⚠] **θ 정량 비교 표 본문 채우기 (수치)** — `03b` §5 frame은 있으나 표 안 채워짐. fastText 재학습 환경에서 채워야 함. *이번 cycle에서는 의도된 한계로 기록*.

---

## 12. 발표 직전 1-page Action List

이 보고서를 다 채우고 남은 *실행 가능한* 보강 액션은 5개다.

1. **figure 캡션 재작성** — figure1/2/3에 \"우리 팀 한 줄 narrative\" 캡션을 슬라이드용으로 다시 쓴다.
2. **cheap-talk 정의 1행** — README §1 또는 §4에 발표용 한 줄 정의 추가.
3. **Bootstrap CI 0 가로지름 feature 목록** — `04` 본문 또는 inset에 한 표 추가.
4. **verbosity 정의 1행 명시** — `06` Alpha 1 markdown에 \"verbosity = log_tokens\" 한 줄.
5. **θ 비교 표 채우기 또는 한계 강조** — fastText 재학습 가능하면 채우고, 그렇지 않으면 `03b`의 \"의도된 한계 statement\"를 발표 슬라이드에 noticeable 하게 표시.

이 5개는 *어느 것을 안 하더라도 평가표 통과는 가능*하지만, 모두 하면 우리 팀의 instability narrative가 한 단계 더 견고해진다.

---

## 13. 한 줄 결론

> 통합 결과는 steering document의 10개 checklist 항목을 모두 충족한다. *남은 5개 보강 action*은 평가표 합격이 아닌 *발표 완성도*를 위한 마무리 작업이다.

Companion: `00_NARRATIVE_README.md` (읽기 가이드).
