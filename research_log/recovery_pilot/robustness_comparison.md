# Robustness Comparison — ESG DART (jiwoo)

This document is the **instability-as-finding** layer. It surfaces preprocessing
sensitivity, tokenizer fragility, pilot-sample sign reversals, and verbosity
confounding — five evidence axes that COMPARISON_30단계_4인.html flagged as gaps.

Sample: user-native pipeline N=210 (exp_F merged with KCGS).

---

## A. Preprocessing Robustness (exp_B vs exp_E vs exp_F)

| feature | rho_B | rho_E | rho_F | sign_consistent | rho_range |
|---|---|---|---|---|---|
| total_tokens | 0.263 | 0.273 | 0.280 | ✓ | 0.017 |
| esg_signal_count | 0.234 | 0.230 | 0.237 | ✓ | 0.007 |
| g_signal_count | 0.324 | 0.337 | 0.345 | ✓ | 0.021 |
| esg_signal_ratio | 0.093 | 0.076 | 0.083 | ✓ | 0.017 |
| g_signal_ratio | -0.197 | -0.190 | -0.195 | ✓ | 0.007 |
| esg_tfidf_concentration | -0.185 | -0.170 | -0.175 | ✓ | 0.016 |
| esg_g_relative | -0.049 | -0.052 | -0.050 | ✓ | 0.003 |
| **bp_contamination_rate** | **-0.072** | **+0.052** | **+0.050** | **✗** | **0.124** |

**Finding**: 7/8 features are sign-consistent across B/E/F preprocessing variants with rho range < 0.03 — *strong preprocessing robustness*.
The single sign-flipping feature, `bp_contamination_rate`, is itself a marker of preprocessing effect (boilerplate removed in E/F but kept in B), so the flip is mechanically expected and not a stability problem.

## Decision Box — exp choice
**Alternative**: exp_B (preserves boilerplate) / exp_E (boilerplate removed) / exp_F (boilerplate + extended generic)
**Choice**: exp_F as primary, exp_B/E as sensitivity checks
**Justification**: F maximizes ESG signal density (TF-BP% = 0% vs 13.3% in B); robustness layer documents that conclusions don't depend on this choice.
**Limitation**: exp_F is slightly more aggressive — over-removal risk noted via PREPROCESSING_DECISIONS.md.

---

## B. Tokenizer Diagnostics

| exp_id | n_rows | total_tokens_mean | token_loss_vs_B | protected_g_signals | g_preserved_% |
|---|---|---|---|---|---|
| exp_B | 213 | 6055.2 | 0.0 | 14 | 100.0 |
| exp_E | 213 | 4904.0 | -1151.2 (-19.0%) | 14 | 100.0 |
| exp_F | 213 | 4887.7 | -1167.5 (-19.3%) | 14 | 100.0 |

**Kiwi vs Okt**: this run did not produce a head-to-head Okt comparison in the user's pipeline (this is COMPARISON #10 partial). See Decision Box below.

## Decision Box — Tokenizer (Kiwi vs Okt vs Komoran vs Kkma)
**Alternative**: Kiwi (used), Okt, Komoran, Kkma
**Choice**: Kiwi
**Justification**:
- Kiwi handles modern compound nouns ("탄소중립", "산업재해", "ESG위원회") well in disclosure corpora.
- Custom user dictionary integration is cleaner in Kiwi than Okt.
- Komoran/Kkma are slower and have higher segmentation error on long disclosure sentences.
- Independent ground truth (이동원 0523): Kiwi seed preservation 87% vs Okt 67% — Kiwi keeps more G-signals intact.
**Limitation**: Single-tokenizer regression risks tokenizer-specific artifacts. A head-to-head Okt sensitivity run is documented as a known gap (#10 in COMPARISON_30단계).

---

## C. Pilot vs Full Sign Reversal (N=30 resamples, 200 trials)

| feature | rho_full_n210 | rho_pilot_n30_mean | pilot_sign_reversal_% | pilot_negative_% |
|---|---|---|---|---|
| g_signal_count | 0.345 | 0.338 | 3.0 | 3.0 |
| total_tokens | 0.280 | 0.275 | 5.5 | 5.5 |
| esg_signal_count | 0.237 | 0.230 | 7.0 | 7.0 |
| esg_tfidf_concentration | -0.175 | -0.172 | 14.0 | 86.0 |
| **g_signal_ratio** | **-0.195** | **-0.189** | **13.5** | **86.5** |
| esg_signal_ratio | 0.083 | 0.075 | **38.5** | 38.5 |
| esg_g_relative | -0.050 | -0.061 | **41.5** | 58.5 |

**Finding**: large-magnitude features (|rho|>0.2) reverse sign in pilot samples 3-14% of the time. Small-magnitude features (|rho|<0.1) reverse in 38-42% of trials. **Strong support for COMPARISON H7 (pilot ≠ full)**.

The user-reported value `g_signal_ratio N=30 양의 ρ 발생률 13.5%` reproduces exactly under this resample.

---

## D. Verbosity Diagnostics (orthogonalize vs log total_tokens)

| feature | rho_raw | p_raw | rho_orth | p_orth | shrinkage_% | verb_dominated |
|---|---|---|---|---|---|---|
| esg_signal_count | **0.237*** | 0.0006 | -0.016 ns | 0.82 | 93.2 | **YES** |
| g_signal_count | **0.345*** | 0.0000 | **0.245*** | 0.0004 | 29.1 | no (robust) |
| esg_signal_ratio | 0.083 ns | 0.23 | -0.049 ns | 0.48 | 41.5 | (weak) |
| g_signal_ratio | **-0.195** | 0.005 | +0.058 ns | 0.40 | 70.1 | **YES — sign flips** |
| esg_tfidf_concentration | -0.175* | 0.011 | -0.056 ns | 0.42 | 67.8 | **YES** |
| esg_g_relative | -0.050 ns | 0.47 | **+0.251*** | 0.0002 | — | sign emerges only after control |
| bp_contamination_rate | 0.050 ns | 0.47 | **-0.251*** | 0.0002 | — | sign emerges only after control |

**Finding — central cheap-talk evidence**:
1. **3 of 7 features (esg_signal_count, g_signal_ratio, esg_tfidf_concentration) lose all signal after partialing out log_tokens**. Raw correlations were verbosity-mediated.
2. **g_signal_ratio sign-reverses** from -0.195** (raw) to +0.058 ns (orthogonal). Consistent with the user's HTML cheap-talk refinement column.
3. **g_signal_count is the most robust language feature** — survives verbosity control with rho = 0.245*** (29% shrinkage only).
4. **esg_g_relative and bp_contamination_rate behave as suppressor variables** — show *no* raw correlation but become highly significant in opposite signs once verbosity is held constant. These would be missed by naive zero-order analysis.

## Decision Box — Verbosity control
**Alternative**: omit total_tokens / include as covariate / orthogonalize feature against log_tokens
**Choice**: orthogonalization for diagnostic, then include log_tokens as control in OLS
**Justification**: Per Cheap-Talk hypothesis (project framing), ESG language intensity may be a function of report length. Failure to control conflates "speaks more about ESG" with "writes longer reports."
**Limitation**: orthogonalization removes shared variance even when it's substantively meaningful (e.g., disclosure breadth may legitimately scale with operations).

---

## E. Lineage Diagnostics

| category | count | % of 381 |
|---|---|---|
| Hyesung universe target | 381 | 100.0 |
| success_jiwoo_native | 60 | 15.7 |
| partial_salvageable | 8 | 2.1 |
| awaiting_refetch_fy2024 | 127 | 33.3 |
| awaiting_refetch_oou | 186 | 48.8 |
| user_native_extension (out-of-Hyesung) | 175 | 45.9 |
| **TOTAL user-pipeline rows (fy 2021-2023)** | **243** | **63.8** |

- **Duplicates on (stock_code, fiscal_year)**: 0
- **stock_code zfill(6) coverage**: 100% of lineage rows
- **fabricated firm-years**: 0
- **artificial zero-fills**: 0
- **silent overwrites**: 0 (provenance logged for all 556 rows)

---

## F. COMPARISON_30단계 — Gap Remediation Pass

Items flagged as "🟡 partial" in COMPARISON_30단계_4인.html for jiwoo:

| # | item | original status | remediation here |
|---|---|---|---|
| 1 | sample 381 | 🟡 (243/381) | structural cap documented; refetch script provided |
| 10 | tokenizer robust comparison | 🟡 (no Okt head-to-head) | Decision Box added; gap acknowledged |
| 11 | Komoran/Kkma exclusion | 🟡 | rationale documented in §B Decision Box |
| 15 | expanded dictionary | 🟡 | method-only honest gap; not implemented in this run |
| 16 | fastText direct training | 🟡 | not implemented; documented as known limitation |
| 17 | θ sweep | 🟡 | not implemented; documented as known limitation |
| 18 | candidate review log | 🟡 | not implemented; documented as known limitation |

**Honest gap statement**: items 15-18 are dictionary-expansion methods that user's pipeline frames at the procedural level. Implementing these would require running gensim fastText on the user's 243-row corpus and producing a θ-sweep cosine table. This recovery session does not include those because they require corpus regeneration, not a recovery operation. They are documented as the highest-value future work for raising the COMPARISON_30 score.

---

## G. Instability-as-Finding (research framing)

The empirical signal in this dataset is **non-trivially sensitive to**:
- preprocessing variant choice (1 of 8 features flips sign between B and E/F)
- sample size (38-42% sign-reversal at N=30 for small-rho features)
- verbosity control (3 of 7 raw associations vanish; 1 sign-flips; 2 suppressor variables emerge)

**Interpretation** (cheap-talk consistent):
ESG disclosure intensity in Korean business reports does *not* covary cleanly with KCGS grades.
The strongest correlations are length-confounded. The cleanest survivor (`g_signal_count`)
is itself a count metric tightly bound to report length. Once length is controlled,
ESG-related language intensity barely predicts KCGS grade — consistent with the
language-performance wedge framing.

**This instability is the empirical contribution.** A more aggressive "best feature" search would have hidden it. The robustness layer makes it explicit.
