# External Validation Workflow

## 실행 순서

```
# 1. KCGS 데이터 생성 (sample_firms.csv → kcgs_esg_ratings.csv)
#    이미 완료됨. data/kcgs_esg_ratings.csv 존재 확인.

# 2. Merge pipeline
python -m src.kcgs_merge

# 3. Validation notebook 실행
#    notebooks/03_external_validation.ipynb 를 Jupyter에서 위→아래 순서로 실행

# (선택) 스크립트로 직접 실행
python -c "
import os; os.chdir('.')
exec(open('notebooks/03_external_validation.ipynb').read())
"
```

## 파일 구조

```
data/
├── kcgs_esg_ratings.csv            ← KCGS 등급 (stock_code + fiscal_year 기준)
├── 04_preprocessed/
│   ├── features_exp_B.csv          ← pre-reg baseline
│   ├── features_exp_E.csv          ← sentence filter + hard stop
│   ├── features_exp_F.csv          ← E + quantity preservation
│   ├── spearman_results.csv        ← Spearman ρ + bootstrap CI 결과
│   ├── spearman_delta.csv          ← exp_B → exp_E Δρ
│   └── spearman_heatmap.png        ← 히트맵 시각화
└── 05_merged/
    ├── merged_exp_B.csv            ← features_exp_B × KCGS
    ├── merged_exp_E.csv
    ├── merged_exp_F.csv
    └── merge_quality_report.csv

notebooks/
└── 03_external_validation.ipynb   ← Spearman 검증 notebook
src/
└── kcgs_merge.py                  ← 재사용 가능한 merge 함수
```

## Merge 설계

- **key:** `stock_code + fiscal_year`
- **join:** inner (KCGS 미매칭 제거 — 데이터 조작 방지)
- **KCGS 등급 기준:** fiscal_year 활동 평가 (예: fiscal_year=2021 → kcgs_grade_2021)
- **temporal alignment:** esg_year ≠ KCGS 등급 연도. config 정의대로 esg_year = fiscal_year + 1 (보고서 제출 연도)이므로 merge는 반드시 fiscal_year 기준

## 파일럿 결과 요약 (n=30, 2026-05-19) — 상위 10개 KOSPI 기업 기반

| feature | exp_B ρ | exp_E ρ | 95% CI (exp_B) | 해석 |
|---|---|---|---|---|
| g_signal_ratio | +0.444★ | +0.418★ | [0.114, 0.691] | moderate-strong, CI⊅0 |
| esg_tfidf_concentration | N/A | +0.326· | - | moderate, CI⊃0 |
| esg_g_relative | +0.253 | [상수=1.0] | [-0.128, 0.582] | moderate, CI⊃0 |
| esg_signal_ratio | -0.147 | -0.014 | - | negligible |
| bp_contamination_rate | +0.088 | [상수=0] | - | negligible |

★ p<0.05  · p<0.10

⚠️  **파일럿 결과는 표집 편의(sampling bias)로 인한 허위 양의 상관 가능성 있음.**
상위 10개 대형주 편중 → 전체 표본에서 부호 역전 확인됨. (아래 참조)

---

## 전체 표본 결과 요약 (n=210, 2026-05-19) — 77개 기업, 3개 회계연도

### Spearman 순위상관 (kcgs_grade_7 기준)

| feature | exp_B ρ | exp_E ρ | exp_F ρ | 95% CI (exp_B) | 해석 |
|---|---|---|---|---|---|
| g_signal_ratio | -0.197★★ | -0.190★★ | -0.195★★ | [-0.326, -0.059] | weak negative, CI⊅0 |
| esg_tfidf_concentration | -0.185★★ | -0.170★ | -0.175★ | [-0.311, -0.045] | weak negative, CI⊅0 |
| total_tokens | +0.263★★★ | +0.273★★★ | +0.280★★★ | [0.124, 0.394] | moderate positive, CI⊅0 |
| esg_signal_ratio | +0.093 | +0.076 | +0.083 | [-0.046, 0.226] | negligible |
| esg_g_relative | -0.049 | -0.052 | -0.050 | - | negligible |
| bp_contamination_rate | -0.072 | +0.052 | +0.050 | - | negligible |

★★★ p<0.001  ★★ p<0.01  ★ p<0.05

### OLS 회귀 결과 (exp_B, n=209)

**모형 1:** `kcgs_grade_7 ~ g_signal_ratio + log_tokens`
- Adj. R² = 0.061, F-stat p = 0.0006
- g_signal_ratio: coef = -1.729, p = 0.312 (개별적으로 비유의)
- log_tokens: coef = +0.114, p = 0.145 (개별적으로 비유의)

**모형 2:** `kcgs_grade_7 ~ g_signal_ratio + log_tokens + esg_tfidf_concentration`
- Adj. R² = 0.062, F-stat p = 0.001
- 두 ESG 피처 간 상관으로 개별 유의성 희석됨 (다중공선성 가능성)

**해석:** 두 ESG 피처를 동시에 투입하면 개별 계수 유의성은 사라지지만, 모형 전체의 F 통계량은 유의함. 보고서 길이(verbosity)와 ESG 언어 강도의 교락 효과 존재.

### Ordered Logit 결과 (exp_B, n=209)

`kcgs_grade_7 ~ g_signal_ratio + log_tokens`
- g_signal_ratio: coef = -2.697, z = -0.732, p = 0.464 (비유의)
- log_tokens: coef = +0.246, z = 1.381, p = 0.167 (비유의)
- 방향성은 OLS와 일치; n=209 검정력 한계로 개별 유의성 미달

---

## 핵심 발견사항 — 파일럿 → 전체 표본 부호 역전

### 1. g_signal_ratio: +0.444 → -0.197 (부호 역전, 양방향 모두 유의)
- 파일럿의 양의 상관은 **표집 편의(상위 10개 대형주)**에서 비롯된 허위 신호
- 전체 표본에서는 KCGS 등급이 낮은 기업이 거버넌스 언어를 더 많이 사용
- Mann-Whitney U (exp_B): p = 0.054 (ρ < 0.1 수준에서 유의)
- preprocessing 선택(exp_B/E/F) 전체에서 방향 일관 → 방법론적 robust

### 2. esg_tfidf_concentration: +0.326 → -0.185 (부호 역전, 양방향 모두 유의)
- 동일한 방향의 역전. ESG 어휘 집중도 역시 낮은 등급 기업에서 더 높음
- Mann-Whitney U (exp_B): p = 0.034

### 3. total_tokens: 파일럿 미측정 → +0.263★★★ (전체 표본 신규 발견)
- 보고서 길이가 가장 강한 양의 연관 변수
- 낮은 등급 기업이 더 짧은 보고서를 작성하거나, 높은 등급 기업이 더 긴 보고서를 작성함
- **verbosity bias**: 보고서 분량이 ESG 등급과 양의 상관 → log_tokens 통제변수 필수

### 4. cheap-talk 가설과의 정합성
- ESG 언어 강도(g_signal_ratio, esg_tfidf_concentration)가 KCGS 등급과 **음의** 상관
- 해석: 외부 평가 등급이 낮은 기업이 보고서 내 ESG 언어를 더 적극적으로 사용하는 경향
- 이는 "언어 ≠ 성과(language ≠ performance)" 라는 cheap-talk 가설과 일관됨
- 인과 해석 불가: association ≠ causation

---

## 방법론적 한계

1. **n=77 기업** — 한국 코스피/코스닥 상장사 전체 대비 제한적
2. **KCGS 평가 불투명성** — 평가 방법론 비공개로 기준 불명확
3. **단면 + 패널 혼합** — 3개 연도 풀링, 기업 고정효과 미통제
4. **verbosity 교락** — log_tokens 통제 후에도 g_signal_ratio 개별 유의성 소실
5. **인과 불명** — 역인과 가능성: 낮은 등급 기업이 평가 대응으로 언어 전략 변경

---

## 다음 단계 (완료 기준)

- [x] Spearman 검증 — exp_B/E/F 전체
- [x] Bootstrap 95% CI
- [x] Mann-Whitney U 검정
- [x] OLS 회귀 (모형 1, 2)
- [x] Ordered Logit robustness
- [ ] kcgs_grade_4 (4단계) 동일 분석 반복 (robustness check)
- [ ] 최종 연구 보고서 작성
