# 00 · Ingest Report — DART × KCGS firm-year 통합 결과

> **이 문서가 답하는 질문 한 줄**
> "우리가 ESG 언어를 분석하기 *전에*, 그 분석의 단위가 되는 firm-year document는 어디서, 어떻게, 얼마나 만들어졌는가?"

본 문서는 발표 슬라이드의 보조 자료이자, 처음 합류하는 팀원이 *코드를 열기 전에* 읽는 한 페이지 안내서다.
같은 폴더의 `notebooks/00_ingest_pipeline.ipynb` 와 짝을 이루며, 노트북은 *흐름과 시각화*, 본 md는 *수치와 의사결정*에 비중을 둔다.

---

## 1. 한눈에 보기

| 항목                                | 값                                  |
| --------------------------------- | ---------------------------------- |
| 분석 단위                             | **firm × fiscal_year**             |
| 표본                                | KOSPI 상장 **81개 기업**                |
| 회계연도                              | FY **2021, 2022, 2023** (3년)       |
| 수집된 DART 사업보고서                    | **243건** (failed_logs.csv 0건)      |
| KCGS 등급 데이터                       | **240건** (미공개 1, 누락 3)             |
| **최종 firm-year (analysis-ready)** | **240건** (회귀 시 미공개 제외 → 최대 239)    |
| 결합 키 (join key)                   | `[stock_code, fiscal_year]`        |
| 절대 사용하지 않는 키                      | `corp_name` (표기 불일치 위험)            |
| 데이터 소스                            | DART OpenAPI · KCGS(한국ESG기준원) 웹 수집 |

초기 수집 대상은 77개 기업 3개년 기준, 213개 firm-year -> KCGS ESG 등급 데이터와 inner join 하는 과정에서 3개 firm-year가 미매칭됨 -> 최종 분석 표본 N=210

---

## 2. 데이터 구조

### 2.1 DART (공시 측)

| 파일 | 행 수 | 주요 컬럼 |
|---|---|---|
| `data/01_raw/corp_code_map.csv` | 3,965 | corp_code, stock_code, corp_name |
| `data/01_raw/collected_reports.csv` | 243 | stock_code, corp_code, rcept_no, fiscal_year, esg_year, report_date, zip_path |
| `data/01_raw/failed_logs.csv` | 0 | (수집 실패 firm-year — 현재 0건) |
| `data/zip_cache/*.zip` | 243 | rcept_no.zip (원본 사업보고서) |

`corp_code_map.csv` 는 KRX 전체 상장사 매핑 테이블. 우리는 그 중 81개만 사용한다.

### 2.2 KCGS (외부 평가 측)

| 파일 | 행 수 | 주요 컬럼 |
|---|---|---|
| `data/kcgs_grades_raw.csv` | 240 | stock_code, corp_name, fiscal_year, kcgs_grade, kcgs_grade_E/S/G |
| `data/kcgs_esg_ratings.csv` | 240 | + `kcgs_grade_7`(1-7), `kcgs_grade_4`(1-4), data_source |

`kcgs_grade_7`, `kcgs_grade_4` 는 통계 분석을 위한 ordinal 인코딩이다.
`data_source` 컬럼은 \"언제 어디서 수집했는지\"를 남기는 **lineage 흔적**이다.

### 2.3 분석 단위(firm-year)로의 변환 흐름

```
KCGS 등급                  DART API                       파일 시스템
   │                          │                              │
stock_code  ──매핑──▶  corp_code  ──검색──▶  rcept_no  ──다운로드──▶  ZIP
(6자리)                (8자리)              (14자리)
   │                                                          │
   └──────── inner join on [stock_code, fiscal_year] ────────┘
                              │
                              ▼
                  240 firm-year documents
```

---

## 3. KCGS 등급 분포 (실측)

### 3.1 연도별 분포

| fiscal_year | A+ | A | B+ | B | C | D | 미공개 | 합 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 7 | 52 | 15 | 4 | 0 | 0 | 1 | 79 |
| 2022 | 3 | 47 | 16 | 10 | 2 | 2 | 0 | 80 |
| 2023 | 12 | 49 | 12 | 5 | 3 | 0 | 0 | 81 |
| **합** | **22** | **148** | **43** | **19** | **5** | **2** | **1** | **240** |

> 연도별 합이 81에 미치지 못하는 까닭: 신규 상장(카카오페이·SK바이오팜)으로 일부 firm-year가 KCGS 평가 대상이 아니었기 때문. 누락 사유는 §5 참조.

### 3.2 7단계 ordinal 인코딩

| 원본 | `kcgs_grade_7` | 빈도 | 비중 |
|---|---:|---:|---:|
| S | 7 | 0 | 0.0% |
| A+ | 6 | 22 | 9.2% |
| A | 5 | 148 | 61.7% |
| B+ | 4 | 43 | 17.9% |
| B | 3 | 19 | 7.9% |
| C | 2 | 5 | 2.1% |
| D | 1 | 2 | 0.8% |
| 미공개 | NaN | 1 | 0.4% |

### ==3.3 분포 해석 — **S등급 부재와 하위등급 희소성**

- **S=0**: 우리 표본 3개 연도 어디에도 S등급 firm은 없다. 이건 표본 추출 오류가 아니라 KCGS 자체가 S를 매우 보수적으로 부여하기 때문이다.
- **A 등급에 표본의 61.7%가 몰림**: KOSPI 우량주를 ==층화추출==했기 때문에 자연스러운 분포다.
- **C+D = 7건 (2.9%)**: 통계적으로 outlier에 가깝다. 회귀에서 \"극단 등급의 신호\"는 거의 검정되지 않으며, 본 연구의 핵심은 ==**A vs B+ 의 가운데 등급 차이**를 잡아내는 것이 된다.
- 그래서 본 연구는 처음부터 분류 정확도가 아닌 **==Spearman 순위상관**과 **ordinal regression**을 핵심 분석으로 잡았다.==


#### Decision Box — 등급 인코딩 단계 수

- ==**Alternative**: 7단계 그대로 사용 / 4단계로 합치기== / S,C,D 등급이 이상치로 판정될 가능성 존재재
- **Choice**: 둘 다 컬럼으로 유지(`kcgs_grade_7`, `kcgs_grade_4`), 분석 단계에서 선택
- **Justification**: C·D가 너무 희소해 7단계 ordinal regression이 불안정해질 위험이 있음. 4단계로 합치면 그 위험은 줄지만 B+ vs B 같은 미세 차이를 잃음.
- ==**Limitation**: 분석 결과가 \"등급 인코딩에 robust한가\"를 두 버전으로 모두 확인해야 함.

---

## 4. 표본 규모와 stratified sampling rationale

### 4.1 왜 81 firms · 3 years 인가

- **계량 분석 최소 n**: ordinal regression이 안정적으로 추정되려면 셀당 충분한 관측이 필요. 200건 내외(n=240)가 \"검정력은 약하지만 0으로 무너지지 않는\" 실용적 하한.
- **3년 패널**: 같은 firm의 시점별 변화를 보려면 최소 2년, 안전하게는 3년 필요. fixed effect 모델의 여지를 남김.
- **연구 단계 현실**: 학부 과정 프로젝트의 시간/연산 자원 내에서 lineage·전처리 품질을 보장 가능한 규모.

### ==4.2 stratified sampling rationale

순수 무작위로 81개를 뽑으면 A 등급이 65건 이상을 차지하고 C/D가 0개일 가능성이 높다. 이 경우 \"하위 등급에서 ESG 언어가 어떻게 다른가\"를 *전혀* 검정할 수 없게 된다.

-> KOSPI 대형주에 편향될 가능성이 있어 층화추출을 사용함
==-> 파일럿은 상위 10개 KOSPI 기업만 포함되어 양의 상관이 왜곡되었고, 전체 표본에서는 다양한 기업 및 업종이 포함되며 결과가 역전됨==
: 즉, **표본편향(Sampling Bias)를 줄이기위함

본 프로젝트는 다음과 같이 **층화추출**했다.

1. KCGS가 2021·2022·2023 모두 평가한 KOSPI firm 풀에서 후보 추출.
2. 2023년 등급 기준으로 A+, A, B+, B, C 5개 stratum 정의.
3. 각 stratum에서 비율을 유지하되 하위 등급(C, D)은 의도적으로 oversample 시도.
4. 결과: 2023 기준 분포 A+ 12 / A 49 / B+ 12 / B 5 / C 3 (D는 0).

#### Decision Box — Sampling 전략

- **Alternative**: pure random / stratified by grade / stratified by industry
- **Choice**: ==stratified by KCGS grade== (industry는 미사용)
- **Justification**: 종속변수 분포 자체가 검정의 출발이므로 등급 다양성 확보가 우선.
- **Limitation**: 산업 분포가 불균형해질 수 있음(예: 금융 과대표본). 회귀에서 산업 통제변수를 넣을 때 일부 셀이 비어 있을 위험. 향후 `induty_code` 보강 후 sensitivity check 필요.
	- 산업 분포 불균형: 금융사는 E(환경) 언급이 적고, IT는 G(지배구조) 비중이 높음
		- ESG 언어 때문인지, 원래 산업 특성 때문인지 구분 어려움
	- 산업 통제변수: 어떤 산업은 특정 등급이 없을 수 있음 -> 빈 셀, 희소 표본 가능성 존재
		- 산업코드 정리 후, 통제 전후 결과 비교 => 민감도 분석

> [!summary] 산업별 ESG 공시 특성이 달라서 산업 효과를 통제할 필요가 있음, 현재 표본에서는 일부 산업의 관측치가 적어 회귀계수 불안정 가능성 존재, 산업코드 보강 후 robustness/sensitivity check가 필요함

---

## 5. 누락된 firm-year의 \"이유 있는\" 기록

분석 단위에서 빠진 행은 모두 사유가 추적 가능해야 한다.

### 5.1 KCGS 평가 자체가 없는 3건 (DART 보고서는 존재)

| stock_code | corp_name | fiscal_year | 사유 |
|---|---|---|---|
| 326030 | 에스케이바이오팜 | 2021 | 2020-07 상장. KCGS 평가 대상 진입 지연 |
| 377300 | 카카오페이 | 2021 | 2021-11 상장. 1차 평가 미포함 |
| 377300 | 카카오페이 | 2022 | 상장 1년차로 KCGS 평가 사이클 미일치 |

==처리: **inner join으로 자연 제외**. 0이나 평균등급으로 채우지 않는다.

### 5.2 KCGS 등급이 \"미공개\"인 1건

| stock_code | corp_name | fiscal_year | 사유 |
|---|---|---|---|
| 096770 | SK이노베이션 | 2021 | KCGS가 해당 연도 등급 게시 안 함 |

==처리: **행은 유지하되 등급 값은 NaN**. 회귀 단계에서 자연 결측 처리.

### 5.3 DART 수집 실패

현재 `failed_logs.csv` = 0행. 81 × 3 = 243건 *완전 패널* 확보.
실패가 0이 된 비결은 §6의 캐시·재시도 설계.

---

## 6. lineage 생성 이유 — \"왜 굳이 ID 5개를 끌고 다니나\"

본 프로젝트는 모든 firm-year 행이 **5개 식별자**를 항상 유지한다.
- lineage: 이 프로젝트 맥락에서 데이터가 어디에서 왔고, 어떻게 변형됐는지 **추적 가능한 경로**

| 식별자           | 역할                 | 깨졌을 때의 비용        | 추가 설명                       |
| ------------- | ------------------ | ---------------- | --------------------------- |
| `stock_code`  | 외부 ESG등급(KCGS)과 연결 | 외부 데이터 결합 불가     | KRX 상장 기업 식별                |
| `corp_code`   | DART API 재호출       | 보고서 재다운로드 불가     | DART 내부 회사 코드               |
| `rcept_no`    | 어떤 ZIP인지 특정        | outlier 원문 추적 불가 |                             |
| `fiscal_year` | 분석 시점              | 시계열 분석 불가        |                             |
| `esg_year`    | 보고 시점              | 시간차 해석 모호        | KCGS 평가 연도(fiscal_year + 1) |
- fiscal_year = 보고서 기간 -> 시계열 분석 불가: ESG 언어 feature 자체가 매년 변화하고 전처리에 민감 => 시간 순 변화로 해석X
	- ESG feature가 공시 언어에 의존하기 때문. ESG 언어는 매년 변경 가능하며, `회사 전략, 분량, boilerplate 제거 여부, tokenizer, 전처리` 등 여러 요소에 민감함. 
- esg_year = 평가 연도 -> 시간차 해석 모호: 외부 평가 기준과 공시 시점 차이 존재 -> 일반화된 해석X, 연관분석만 가능
	- fiscal_year + 1, 작년에 작성한 보고서를 올해 성과 기준으로 보고서를 해석하면, 실제 성과인지 단순한 차이인지 알 수 없음.

*disclosure란 기업이 사업보고서에서 ESG에 대해 어떻게 말하고 있는가를 알려줌*

**fical year VS ESG year**

| 구분          | 정의                  | 용도                         |
| ----------- | ------------------- | -------------------------- |
| fiscal_year | 기업 회계연도             | 원문 보고서 추출, firm-year 문서 생성 |
| esg_year    | KCGS ESG 평가가 발표된 연도 | 외부 ESG 등급과 매칭, 타이밍 확인용     |

lineage 유지의 실제 효용:

- **재현성**: 다른 팀원도 같은 stock_code -> corp_code -> rcept_no -> firm-year document -> feature 과정을 그대로 따라할 수 있다.
- **디버깅(오류 추적)**: 회귀에서 표준화 잔차가 큰 firm-year가 나오면 rcept_no로 원문 ZIP을 즉시 다시 연다.
- **무결성**: 중간 transformation 버그가 lineage를 깨지 않는 한 결과는 신뢰 가능.
- **편향 설명**: 빠진 행을 \"몰래 0으로 채우는\" 대신 사유를 명시할 수 있다.

>[!summary] 본 프로젝트의 black rule: **\"0으로 채우지 않는다, 평균으로 채우지 않는다, 이름으로 join하지 않는다.\"**

---

## 7. 산업(섹터) 분포 — 부분 정보와 한계 명시

현재 ingest 단계는 산업분류(KSIC `induty_code`)를 lineage에 *포함하지 않는다*. 이건 의도된 단순화다.

- DART `corpCode.xml` 자체에 산업 정보가 없다.
- 산업 보강은 DART `company.json` 의 `induty_code` 별도 호출이 필요.
- 외부 `company_master.csv`(한국ESG기준원 anchor 기업 리스트)와 매칭하면 일부(81 중 20)만 산업이 잡힌다.

### 7.1 현재 매칭 가능한 산업 분포 (부분, n=20)

| industry | n |
|---|---:|
| 금융지주 | 3 |
| 화학 | 2 |
| 인터넷/플랫폼 | 2 |
| 물류 / 철강 / 반도체 / 지주회사 / 자동차 / 정유 / 비철금속 / 전기전자 / IT서비스 / 은행 / 바이오의약품 / 에너지·화학 / 식품 | 각 1 |

부분 정보이지만 **KOSPI 대표 산업이 골고루 포함**되어 있음을 시사. 본격 회귀에 industry FE를 넣으려면 다음 단계에서 81개 전체에 대해 `induty_code` 보강이 필요하다.

#### Decision Box — 산업 보강 시점

- **Alternative**: ingest 단계에서 산업까지 결합 / 회귀 직전 별도 모듈에서 보강
- **Choice**: 회귀 직전 별도 모듈로 분리
- **Justification**: ingest를 단순하게 유지해 디버깅 비용을 낮춤. 산업은 본 연구의 *부수 통제변수* 라 ingest 단계의 필수 lineage가 아니다.
- **Limitation**: 산업이 ESG 언어량의 강한 confounder(교란변수)일 가능성. 산업 보강을 너무 늦추면 검정의 해석에 보조설명이 길어진다.
	- 반도체 기업은 원래 ESG 관련 단어가 많아서 ESG 등급도 높음. 환경 단어 빈도 수 증가에 따른 ESG 등급 상승보다는 반도체 산업 효과일 가능성이 높음
	- 교란변수 통제가 필요함

- 산업은 중요한 통제변수지만, ingest 단계에서는 핵심 lineage만 관리하고, 나중 회귀 단계에서 덧붙임임

---

## 8. Fix History — 실제로 발생했던 함정과 수정

| 시점 | 증상 | 원인 | 수정 |
|---|---|---|---|
| 초기 | corp_code 조회 일부 실패 | `pd.read_xml`이 `\"00126380\"`을 int로 읽어 `126380` 으로 변환 | `dtype=str` 강제 + `corp_code.str.zfill(8)` |
| 수집 1차 | 같은 firm·연도에 보고서 다중 등장 | DART는 정정공시도 별개 rcept_no | `pick_latest_report()` — `rcept_dt` 내림차순 첫 행 |
| 수집 2차 | rate limit 오류 | 연속 요청 간 지연 부재 | `REQUEST_DELAY = 0.5s` + 재시도 시 점진 대기 |
| KCGS 결합 | 카카오페이/SK바이오팜 매칭 실패 | 신규 상장, KCGS 평가 부재 | inner join + 사유 기록(§5.1) |
| KCGS 정리 | SK이노베이션 FY2021 \"미공개\" | KCGS 비공개 | 행 유지, 값 NaN(§5.2) |
| 구조 변경 | sample_firms.csv (10개) 검정력 부족 | 표본이 너무 작음 | `sample_firms_expanded.csv` (81개) + `collect_expanded.py`로 신규 71개만 증분 수집, 기존 ZIP은 캐시 재사용 |
| ingest 통합 | fiscal_year vs esg_year 혼동 | 두 연도의 의미가 다름(보고 시점 vs 평가 시점) | join은 `fiscal_year` 로만 수행, esg_year는 메타로만 보존 |

이 표는 **\"이 코드를 새로 짤 때 절대 다시 만들지 말아야 할 버그 리스트\"** 이기도 하다.

---

## 9. 다음 단계와의 연결

ingest 단계의 산출물 `(stock_code, fiscal_year)` firm-year 인덱스는 다음 단계의 *입력*이 된다.

```
00_ingest_pipeline.ipynb  (이 문서가 설명)
        │  → 240 firm-year × KCGS 등급 × rcept_no
        ▼
01_section_extract       II / IV / VI 섹션만 추출
        ▼
02_passage_filter        ESG seed 단어를 포함한 문장만 보존
        ▼
03_preprocess            형태소 분석, 사용자 사전, stopword
        ▼
04_feature_build         TF-IDF / cosine / 사전 매칭 점수
        ▼
05_merge_for_stats       feature × KCGS 등급 결합
        ▼
06_analysis              Spearman, OLS, Ordered Logit
```

### 9.1 짝을 이루는 노트북 · 문서

| 파일 | 역할 |
|---|---|
| `notebooks/00_ingest_pipeline.ipynb` | **이 문서의 노트북 버전** (시각화 포함) |
| `notebooks/01_token_inspection.ipynb` | 토큰화 결과 점검 |
| `notebooks/02_preprocessing_eval.ipynb` | 전처리 실험 비교 |
| `notebooks/03_external_validation.ipynb` | KCGS와의 외부 검증(Spearman) |
| `VALIDATION_WORKFLOW.md` | 검정 워크플로우 전체 흐름 |
| `전처리_설계_분석.md` | 전처리 결정의 근거 |
| `전처리결과_비판적분석.md` | 결과의 비판적 검토 |

### 9.2 다음 단계의 첫 번째 질문

> **\"240개 firm-year 텍스트 중, ESG 문장 추출률에 큰 편차가 있는가?\"**
>
> 만약 일부 firm의 II/IV/VI 섹션이 짧거나 비어 있다면, *언어량 자체* 가 등급과 상관된다는 사실이 분석의 \"가짜 신호\"로 작동할 위험이 있다. 그래서 다음 단계는 `total_word_count` 통제 변수 만들기에서 출발한다.

---

## 10. 마지막 한 가지 — 이 ingest가 \"측정\"하는 것은 무엇인가

본 연구는 ESG *수준* 을 예측하려는 것이 아니다.
ingest 단계가 만들어내는 240행은 단지 \"같은 firm-year에 대해 *언어*와 *외부 평가*가 짝지어진 표본\" 일 뿐이다.

그 위에서 우리가 결국 보려는 것은:

- 기업이 ESG에 대해 *더 많이 말한다고 해서* KCGS 등급도 더 높은가?
- 아니면 그 둘 사이에 *말과 행동의 괴리(cheap talk)* 가 보이는가?

이 질문이 의미를 가지려면 ingest 단계의 *분석 단위 정의* 부터 흔들리지 않아야 한다.
그래서 본 문서는 등급 분포나 코드보다 \"왜 firm-year인가, 왜 lineage인가, 왜 0으로 채우지 않는가\" 에 가장 많은 분량을 썼다.

---

## Appendix

### robustness

1. 모향 바꿔도 방향 유지되는지
OLS, Ordered Logit, Binary Logit -> g_signal_ratio의 방향이 같음 => 모형 Robust

2. 전처리 바꿔도 결과 유지되는지
exp_B, exp_E, exp_F 비교 -> -0.197, -0.190, -0.195 으로 방향이 같음=> 전처리 Robust

3. 산업 통제 넣어도 결과 유지되는지
grade ~ g_signal_ratio + log_tokens + industry_dummy -> g_signal_ration 으로 방향이 같음 => 산업 효과 Robust

4. 이상치 제거해도 유지되는지
상위 1% 제거 후에도 방향이 동일하면 Robust

5. 등급 체계 바꿔보기
D~S등급를 상/중/하 로 바꿔보기 -> 결과 유지 => Robust

### sensitivity check
threshold 최적 경계값 설정

## project에 적용

너희 프로젝트에서 현실적으로 제일 좋은 robustness/sensitivity는:

exp_B/E/F 비교
OLS vs Ordered Logit 비교
산업 통제 추가 여부
threshold 변화
extreme outlier 제거

이미 1번은 꽤 잘 되어 있음.

---

*작성: 2026-05-19. 본 문서의 모든 수치는 `data/01_raw/collected_reports.csv` 와 `data/kcgs_esg_ratings.csv` 의 실측에서 계산됨.*
