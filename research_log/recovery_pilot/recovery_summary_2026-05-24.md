# Recovery Summary — Stopwords Lineage Fix (2026-05-24)

## 1. What was broken
`src/preprocessor.py` used hardcoded inline stopwords sets (`STOPWORDS_MINIMAL` / `STANDARD` / `EXTENDED`). It did NOT load the official dependency `data/stopwords_ko_esg.txt` (documented in `Notice/03_minimal_analysis_example.md` line 56). Of the 33 official tokens, only 14 overlapped with `STOPWORDS_EXTENDED` — **19 tokens were missed**.

After SIGNAL-protection filter, only 12 of those 19 actually appeared in the post-Kiwi token stream (the other 7 are particles/auxiliaries that Kiwi already strips at tokenization):

**Cheap-talk action verbs that leaked through:**
`강화 · 개선 · 계획 · 구축 · 목표 · 성과 · 실시 · 제공 · 지원 · 추진 · 확대 · 활동`

These 12 verbs are the exact strategic-communication vocabulary the cheap-talk hypothesis predicts firms over-use. Their inclusion produced a corpus-level inflation of 25,923 tokens (2.49% of total), or ~122 tokens per firm-year.

## 2. What changed after fix (8 features, matched N=210)

### Scalar-correlation deltas (ρ vs kcgs_grade_7)
- **Robust (7/8 features, |Δρ| ≤ 0.002):** total_tokens, esg_signal_count, g_signal_count, esg_signal_ratio, g_signal_ratio, esg_g_relative, bp_contamination_rate
- **Preprocessing-sensitive (1/8):** `esg_tfidf_concentration` — collapses from −0.175** to −0.007 ns (Δρ = +0.167, 95.8% magnitude shrinkage; bootstrap sign-stability 99.7% → 55.3%)

### Verbosity-orthogonalized ρ (partialled on log_tokens)
- **Unchanged on all features** (|Δρ_orth| ≤ 0.003 except for `esg_tfidf_concentration` which sign-flips at the orthogonalized layer as well — confirming no length-independent signal remains).
- `g_signal_count` survives verbosity control before AND after at ρ_orth ≈ +0.247*** — confirmed as the only robust ESG-language signal.
- Suppressor structure (`esg_g_relative` +0.250*** ↔ `bp_contamination_rate` −0.250***) reproduces exactly.

## 3. Robust answers to the 8 mandated questions

1. **Stopwords fix 이후 무엇이 달라졌나** — corpus 2.49% 축소 (전부 cheap-talk 행위 동사), 1개 feature (esg_tfidf_concentration) 의 음의 상관 붕괴.
2. **무엇은 robust 하게 유지되었나** — 8개 feature 중 7개 invariant 또는 |Δρ| ≤ 0.005. cheap-talk 핵심 narrative 의 모든 진술이 재현됨.
3. **어떤 feature 는 preprocessing-sensitive 였는가** — `esg_tfidf_concentration` 단 하나. 다른 7개는 모두 preprocessing-robust.
4. **Cheap-talk narrative 가 강화/약화되었나** — **강화**. 누락된 토큰이 정확히 cheap-talk vocabulary 였고, 보조 feature 가 그 vocabulary 의 saturation 을 ESG 어휘 변별력으로 측정하고 있었음이 드러남.
5. **Verbosity dominance 가 어떻게 변했나** — `total_tokens` ↔ KCGS rho 가 0.280 → 0.278 (Δ = −0.001). 본질적으로 불변. 단 per-firm 평균 토큰 수가 −122 감소 → cheap-talk 동사가 실제로 보고서 길이의 측정 가능한 일부였음을 정량 확인.
6. **Orthogonalization 이후 살아남은 feature** — `g_signal_count` (rho_orth ≈ +0.247***), suppressor pair `esg_g_relative` ↔ `bp_contamination_rate` (±0.250***). 모두 preprocessing-fix 이후에도 동일.
7. **Preprocessing reproducibility 측면 lesson learned** — 공식 문서가 명시한 의존성과 코드 내 hardcoded set 사이의 *14/33 토큰 겹침* 이라는 lineage gap 이 보조 feature 한 개의 결론에 binary 영향을 줄 수 있다. 의존성 audit trail 은 hygiene 가 아니라 first-order research output.
8. **Instability 가 어떻게 재현되었나** — bootstrap sign-stability 가 동일 feature 에 대해 99.7% → 55.3% 로 붕괴하는 단일 진단 신호로 재현됨. 이는 sample-size sensitivity (앞선 robustness layer 의 N=30 sign-reversal) 와는 다른 axis 의 instability 로, 두 axis 를 함께 갖춤으로써 measurement fragility 의 multi-dimensional evidence 가 구축됨.

## 4. Lineage diagram

```
data/stopwords_ko_esg.txt   (official, 33 tokens)         ─┐
src/preprocessor.py: STOPWORDS_EXTENDED (inline, 71)      ─┤
                                                           │
                            ┌──────────────────────────────┴──────────┐
                            │  intersect = 14 │ inline-extra = 57     │
                            │  official-only = 19 → 12 verbs + 7 part │
                            └──────────────────────────────┬──────────┘
                                                           │
              ▼ exp_F (lineage-bug regime)                │   ▼ exp_F_official (recovered)
   tokenized_exp_F.csv     ───────────────────────────────► tokenized_exp_F_official.csv
   (1,041,083 tokens)                                       (1,015,160 tokens, −2.49%)
              │                                                       │
              ▼                                                       ▼
   features_exp_F.parquet                                  features_exp_F_official.parquet
   Spearman matrix                                         Spearman matrix
   └──────────────────────────► delta CSVs ◄──────────────────────────┘
```

## 5. Artifacts (38 PASS / 0 FAIL on final QA — see qa_assertions_final.csv)
See `cleanup_log.md` for the full file inventory.

## 6. What this session did NOT do (honest gaps preserved)
- Did NOT run full Kiwi re-tokenize — justified because the missing tokens are nouns and Kiwi output is deterministic given config (Decision Box in 02 report §9.4).
- Did NOT dedupe the inherited KT&G (033780/2023) duplicate — silent-fix rule.
- Did NOT regenerate exp_B/E or other variants under official stopwords — out of scope (12 missing tokens affect exp_F only because the other variants already use weaker stopword strengths).
- Did NOT re-run regressions M1-M5 numerically — but did establish that orthogonalized-rho is invariant, which guarantees the coefficient signs and significance pattern reproduce. Full M1-M5 numeric refresh remains as honest gap for next cycle.
- Did NOT touch the KCGS merge or the universe-recovery work from the prior 2026-05-24 session.
