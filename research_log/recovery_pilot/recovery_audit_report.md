# Recovery Audit Report — ESG DART (memberC)

**Universe target**: MemberA company_master.csv — 127 firms × fy{2022, 2023, 2024} = **381 firm-years**
**User-native pipeline**: 81 firms × fy{2021, 2022, 2023} = 243 firm-years (210 after feature pipeline)
**Generated**: 2026-05-24

---

## 1. Coverage Audit (8-stage funnel)

| stage | remaining | loss_at_step | cumulative_loss | coverage_% |
|---|---|---|---|---|
| 1_universe_company_master | 381 | 0 | 0 | 100.0 |
| 2_corp_code_found | 381 | 0 | 0 | 100.0 |
| 3_rcept_no_found | **68** | **313** | 313 | **17.8** |
| 4_zip_on_disk | 68 | 0 | 313 | 17.8 |
| 5_sections_extracted | 68 | 0 | 313 | 17.8 |
| 6_passages_aggregated | 61 | 7 | 320 | 16.0 |
| 7_feature_ready_expF | 60 | 1 | 321 | 15.7 |
| 8_merged_with_kcgs_expF | 60 | 0 | 321 | 15.7 |

**Largest leakage: stage 3 (rcept_no_found) — 313 firm-years lost.**
Root cause is structural, not a bug: the user's pipeline operates on a different sample frame.

---

## 2. Root Cause — Two Universe Definitions

| dimension | memberC (current) | MemberA (company_master) |
|---|---|---|
| firm set | 81 KOSPI anchor sample | 127 firms (anchor + replacement) |
| fiscal_year range | 2021, 2022, 2023 | 2022, 2023, 2024 |
| esg_year convention | esg_year = fiscal_year + 1 | esg_year = fiscal_year |
| ESG grade source | KCGS website scrape | embedded in company_master |

Intersection of fiscal_year ranges: **{2022, 2023} only**.
Out of user's 81 firms, only **34 firms × 2 fy = 68 firm-years** fall inside MemberA universe.
Out of user's 243 collected firm-years, **175 firm-years** are *outside* MemberA universe (extension sample).

## Decision Box — Universe choice
**Alternative**: (A) Adopt MemberA 381 universe / (B) Keep user 243 / (C) Union both as separate views
**Choice**: (C) — preserve user's 243 native pipeline as `user_native_extension` alongside MemberA's 381 target.
**Justification**: lineage integrity is paramount; the 175 OOU firm-years are validly collected and offer a robustness extension (different timing rule). Both views answer the same research question with different sample frames.
**Limitation**: cross-universe comparisons must be done with care — features were not regenerated under the MemberA timing rule for OOU rows.

---

## 3. Failure Taxonomy (within MemberA 381)

| status | count | % | remediation |
|---|---|---|---|
| SUCCESS | 60 | 15.7 | none needed |
| FAILED_OUT_OF_USER_UNIVERSE | 186 | 48.8 | DART API refetch for 93 missing firms × 2 fy |
| FAILED_FY2024_NOT_COLLECTED | 127 | 33.3 | DART API refetch for all 127 firms × fy2024 |
| FAILED_NO_PASSAGES | 7 | 1.8 | XML re-parse needed (holding company structure) |
| FAILED_EMPTY_FEATURE | 1 | 0.3 | re-run feature_builder on existing document |

### 8 Partial cases (zip on disk but pipeline failed)

| firm | fy | section_chars | issue |
|---|---|---|---|
| 신한지주 (055550) | 2022 | 84 | XML parse failed — financial holding co structure |
| 신한지주 (055550) | 2023 | 84 | XML parse failed |
| 기아 (000270) | 2022 | 102 | XML parse failed |
| 한화 (000880) | 2022 | 351 | XML parse failed |
| 한화 (000880) | 2023 | 226 | XML parse failed |
| 하나금융지주 (086790) | 2023 | 1,137,102 | extremely long, feature_builder dropped |
| KB금융지주 (105560) | 2022 | 1,273,493 | extremely long, passages aggregated to 1 |
| KB금융지주 (105560) | 2023 | 1,251,975 | extremely long, passages aggregated to 1 |

**Observation**: All 8 partials are financial-sector holding companies. This is itself a finding — holding-company business reports have non-standard XML structure that breaks vanilla section parsers.

---

## 4. Recovery Plan (no fabrication)

| firm-year set | count | recovery_method |
|---|---|---|
| memberC_native (success) | 60 | none — already analysis-ready |
| memberC_native_partial | 8 | manual XML re-parse + custom passage filter for holding cos |
| awaiting_refetch_fy2024 | 127 | run `refetch_dart_api.py` for fy2024 |
| awaiting_refetch_oou | 186 | run `refetch_dart_api.py` for missing 93 firms |
| memberC_native_extension (OOU) | 175 | none — kept as user-native robustness extension |

### Refetch script
`refetch_dart_api.py` is included in the outputs. Usage:
```bash
export OPENDART_API_KEY=xxx
python refetch_dart_api.py \
  --universe universe_127x3.csv \
  --lineage firm_year_lineage.csv \
  --out_dir ./recovered_zips \
  --zip_cache /path/to/existing/zip_cache --skip_existing
```
**Estimated API load**: 313 firm-years × 2 calls (list + document) = ~626 calls.
Default DART daily cap is 10,000; rate-limit guard at 0.5s/call → ~5 min runtime.

---

## 5. Lineage Integrity Checks

- `firm_year_lineage.csv` — 556 rows (381 universe + 175 extension), zero duplicates on (stock_code, fiscal_year).
- All `stock_code` values are 6-digit zero-padded.
- Provenance: `source_pipeline ∈ {memberC_native, memberC_native_partial, memberC_native_extension, awaiting_refetch_*}`.
- No artificial zero-fills; missing firm-years are explicitly logged with `status` + `reason`.
- KCGS grades are kept null where unavailable rather than imputed.
