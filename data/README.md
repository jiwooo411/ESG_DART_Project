# data/

이 프로젝트의 분석 단위는 **127개 상장기업 × 2022–2024년 = 381 firm-year**다.

## 구성

| 경로 | 내용 | 행 수 |
|---|---|---|
| `sample/company_master.csv` | 최종 분석 모집단 정의 (127개사) — stock_code, corp_code 매핑 | 127사 |
| `sample/universe_127x3.csv` | 127사 × 3개년 = 381 firm-year의 최종 lineage 키 (stock_code, corp_code, rcept_no, fiscal_year, esg_year) | 381 |
| `dictionary/seed_dictionary.csv` | E/S/G seed 단어 사전 (TF-IDF 1단계 입력) | — |
| `dictionary/stopwords_ko_esg.txt` | 도메인 stopword 목록 | — |

## 데이터 계보(lineage) 원칙

이 프로젝트는 다음 식별자만으로 모든 데이터를 연결한다:

- `stock_code` (종목코드, 6자리)
- `corp_code` (DART 고유번호, 8자리)
- `rcept_no` (접수번호 — 특정 사업보고서 1건을 가리키는 키)
- `fiscal_year` (사업연도)
- `esg_year` (KCGS 등급 기준연도)

**회사명(company_name)으로 병합하지 않는다.** 동명이사·계열사 표기 차이로 인한 오결합을 막기 위함이다.

## 결측 처리 원칙

수집·전처리 단계에서 실패한 firm-year는 **가짜 값으로 채우지 않고, 사유를 로그로 남기고 표본에서 제외한다.** 0으로 채우는 것과 "ESG 언어가 0건이라 측정된 것"은 다른 의미이기 때문이다. M2 모델(재무 통제 포함)의 n=344는 재무 데이터 결측으로 인한 **listwise exclusion** 결과이며, 결측치를 추정해 메운 것이 아니다.

## 알려진 한계

`company_master.csv`의 `esg_year` 컬럼은 현재 `fiscal_year`와 동일한 값으로 라벨링되어 있다. 원래 가이드 정의는 `esg_year = fiscal_year + 1`(해당 사업연도 보고서가 발표된 다음 해의 KCGS 등급을 매칭)이지만, 실제 CSV 라벨은 이를 따르지 않아 한 해 어긋날 가능성이 있다. 이는 `recovery_N381/README_N381.md`에서도 동일하게 확인된 한계로, 최종 해석에 영향을 줄 수 있는 지점이므로 명시해 둔다.

## 이 폴더에 없는 것

- 원문 사업보고서 ZIP/XML 원본 (용량 문제로 제외 — 재현 시 `scripts/01_collect.py`로 재수집)
- KCGS 등급 원본 CSV (웹 스크레이핑 데이터로 재배포 권한 불명확 — `.gitignore` 처리)
- 중간 산출물(exp_B/E 등 구버전 feature, 243-row 단계 lineage 등) — `research_log/recovery_pilot/`, `research_log/recovery_N381/`에 과정 기록으로만 보존
