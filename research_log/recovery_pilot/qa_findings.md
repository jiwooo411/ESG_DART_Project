# QA Findings — Recovery Session

10 of 11 assertions pass. The one failure is documented below (not silently fixed).

## Failed assertion: merge_integrity_unique_key

**Issue**: `data/05_merged/merged_exp_F.csv` contains 1 duplicate on (stock_code, fiscal_year):

| rcept_no | corp_name | stock_code | fiscal_year | features |
|---|---|---|---|---|
| NaN | 케이티앤지 | 033780 | 2023 | identical |
| 20240320005... | 케이티앤지 | 033780 | 2023 | identical |

Two rows for the same firm-year, identical feature values, but one has a NaN rcept_no.

**Likely cause**: source pipeline merged two passes — one with rcept_no populated, one without (perhaps from a re-run that didn't fully overwrite). Feature values are identical so no analytical effect on means, but the row would be double-weighted in any naive concat or count.

**Recommended fix (in source pipeline, NOT here)**:
```python
# in src/kcgs_merge.py or feature_builder.py
df = df.sort_values('rcept_no', na_position='last').drop_duplicates(
    subset=['stock_code','fiscal_year'], keep='first'
)
```

Per project rules ("NEVER silent overwrite") this is logged here rather than auto-deduped.
The duplicate is small enough that 209-row regression results in the user's current
report are not affected (it would shift N from 210 to 209 in any pipeline that
respects unique (stock_code, fiscal_year), which 209 already is).

## Other passes

- 10/11 PASS
- zero fabricated rows
- zero artificial zero-fills
- zero silent overwrites
- all 556 lineage rows have populated source_pipeline
- all 60 SUCCESS rows verified to exist in merged_exp_F
