# ESG DART — N=381 Full Sample Recovery 완료

**팀3 분석 노트북의 수집 방법론(`collect_one_firm_year` 등)을 적용해 381 firm-year 전수 복원.**

## 핵심 결과
| 단계 | 결과 |
|---|---|
| DART API 수집 | **381 / 381 SUCCESS** · FAIL = 0 |
| Section II/IV/VI 추출 | 381개 firm-year 모두 3개 섹션 0자 초과 |
| Kiwi 전처리 (exp_F) | 381개 모두 token_count > 0 |
| Feature 계산 | 381개 × 13개 scalar feature |
| KCGS 등급 merge | 381 / 381 매핑 (company_master 임베디드 등급 사용) |
| 중복 (stock_code × fiscal_year) | **0** |

## Universe
- 127 firms × fiscal_year {2022, 2023, 2024} = **381 firm-years**
- esg_year = fiscal_year (company_master 정의 그대로)
- 사업보고서 검색: search_year = fiscal_year + 1 (team3 timing rule)

## N=381 Spearman ρ vs KCGS 7-level
| feature | ρ | p |
|---|---|---|
| total_tokens | **0.6614** | *** |
| g_signal_count | **0.6387** | *** |
| esg_signal_count | **0.5061** | *** |
| esg_signal_ratio | 0.2357 | *** |
| esg_tfidf_concentration | -0.2300 | *** |
| g_signal_ratio | -0.1866 | *** |

## Mann-Whitney (A이상 N=138 vs B+이하 N=243)
- total_tokens, esg_signal_count, g_signal_count: 모두 p<0.001
- esg_signal_ratio, g_signal_ratio, esg_tfidf_concentration: 모두 p<0.01

## 핵심 cheap-talk 진단 — Verbosity orthogonalization
| feature | rho_raw | rho_orth(log_tokens) | 해석 |
|---|---|---|---|
| esg_signal_count | +0.51*** | **-0.31***** | sign flip · verbosity-dominated |
| g_signal_count | +0.64*** | +0.29*** | survives but shrinks |
| g_signal_ratio | -0.19*** | **+0.33***** | **sign reversal** |
| esg_tfidf_concentration | -0.23*** | **+0.20***** | **sign reversal** |

→ N=381에서도 **verbosity가 raw 신호의 상당 부분을 흡수**.
g_signal_ratio · esg_tfidf_concentration은 length 통제 후 부호가 정반대.
"cheap-talk = 길이로 위장된 ESG 신호" 가설과 일관.

## 파일
- `merged_full_sample_N381.csv` — 381 × 22 (firm-year × KCGS × features)
- `features_exp_F_N381.csv` — 381 × 13 (firm-year × features only)
- `spearman_N381.csv`, `mannwhitney_N381.csv`, `verbosity_orth_N381.csv` — validity 검증 결과
- `corpus_char_stats.csv` — 381개 섹션별 글자 수 분포
- `corpus_N381.tar.gz` — 원본 코퍼스 (381개 JSON)
- `tokens_exp_F_N381.tar.gz` — 전처리된 토큰 (381개 JSON, exp_F 설정)
- `collect_381.py` — 팀3 방법론 기반 재현 가능한 수집 스크립트

## 재현 절차 (다른 환경에서)
```bash
export OPENDART_API_KEY=...
python collect_381.py \
  --master company_master.csv \
  --corp_map corp_code_map.csv \
  --zip_dir ./zip_cache \
  --out_dir ./recovery_run \
  --api_key $OPENDART_API_KEY
# → corpus/, collection_meta.csv 생성 (Checkpoint pattern: 재시작 자동 복구)
```

## 사용 의사결정 기록 (Decision Box)
- **수집 universe**: company_master.csv (127×3=381) 채택. user 기존 81×3=243 sample은 별도 보존.
- **timing**: search_year = fiscal_year+1 사업보고서 수집, KCGS 등급은 company_master `[stock_code, fiscal_year]` 키로 join (team3와 동일).
- **섹션**: II · IV · VI 만 추출 (대분류 로마숫자 TITLE 경계, TABLE 블록 제거, 10자 미만 단락 제거).
- **전처리**: exp_F (extended stopwords, keep_quantity 숫자, 회사명 제거, boilerplate 문장/명사 필터). 사전 등록된 baseline은 exp_B이며, exp_B/E/F 비교는 별도 robustness 실행에서 가능.
- **feature**: 사용자 기존 `src/feature_builder.py` 그대로 사용 (taxonomy 일관성 유지).
- **fake row / 가짜 0 / company_name join**: 모두 **사용 안 함**. lineage = stock_code × fiscal_year.

## 가짜 0이 아닌 이유
- bp_contamination_rate / esg_g_relative 가 일정 분산을 안 보이는 것은 **실제 토큰 분포** 결과. 0은 boilerplate token이 보존된 문장에 들어가지 못한 결과이고, 1은 esg/g 어느 한쪽이 0일 때 ratio의 정의값.
- 모든 firm-year는 실제 DART API에서 수집된 사업보고서를 가지며, 합성/추정 없음.

## 한계
- KCGS 등급 매핑: company_master 임베디드 등급의 `esg_year` 라벨이 fiscal_year와 동일 (라벨링 차이 가능). 가이드 정의대로면 fiscal_year+1의 KCGS 등급이지만, CSV 라벨이 다르면 한 해 어긋날 수 있음 (team3 노트북에서도 같은 한계 명시).
- exp_B/E 비교 robustness는 별도 실행 필요 (이번 deliverable은 exp_F만).
- Okt/Komoran/Kkma robustness, fastText/θ sweep, expanded dictionary는 미실행 — 별도 작업 항목.
