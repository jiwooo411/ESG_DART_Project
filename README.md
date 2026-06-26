# 분량을 통제하면 거버넌스 어휘만 남는다

### 사업보고서 ESG 공시 언어와 KCGS 등급의 정합성 진단

127개 상장기업 × 2022–2024년 (381 firm-year)의 사업보고서를 분석해, **ESG 공시 "언어"가 외부 ESG "평가"와 실제로 정합하는지**를 진단한 프로젝트다.

> 이 프로젝트는 ESG를 측정하지 않는다. **ESG 언어와 ESG 평가 사이의 간극(gap)**을 측정한다.

---

## 핵심 발견 4가지

1. **공시 분량(分量)이 ESG 언어 자체보다 더 강한 신호였다.** 단순 토큰 수(log_n_tokens)가 어떤 ESG 단어 기반 feature보다도 KCGS 등급과 강하게 연관되었다.
2. **분량과 기업 규모를 통제하면, G(거버넌스)만 독립적인 신호로 남는다.** E·S 관련 언어의 연관성은 분량 통제 후 크게 줄거나 사라지지만, G는 통제 이후에도 유의하게 남는다.
3. **표본의 44%에서 Talk–Walk Gap(말과 등급의 불일치)이 관찰되었다.** 공시 언어 수준과 실제 등급이 어긋나는 기업이 절반에 가깝다.
4. **기업은 E·S·G 전반에 걸쳐 균일하게 공시하지 않는다.** 특정 축은 부풀리고 다른 축에는 침묵하는, 선택적·불균등한 공시 패턴이 나타난다.

이 네 가지가 이 저장소의 결론이다. 아래 내용은 모두 이 결론을 어떻게 얻었는지에 대한 설명이다.

---

## 목차

1. [이 프로젝트가 묻는 질문](#1-이-프로젝트가-묻는-질문)
2. [데이터 & 분석 단위](#2-데이터--분석-단위)
3. [파이프라인 개요](#3-파이프라인-개요)
4. [방법론 요약](#4-방법론-요약)
5. [핵심 결과](#5-핵심-결과)
6. [Cheap-Talk 관점과 한계](#6-cheap-talk-관점과-한계)
7. [저장소 구조](#7-저장소-구조)
8. [재현 방법](#8-재현-방법)
9. [데이터 출처 및 라이선스](#9-데이터-출처-및-라이선스)

---

## 1. 이 프로젝트가 묻는 질문

> "사업보고서의 ESG 관련 표현은 외부 ESG 평가(KCGS 등급)와 통계적으로 연관되는가?"

이 질문은 두 가지를 묻지 **않는다**:

- ESG 성과 자체를 예측하거나 측정하는 것이 아니다.
- 어떤 기업이 "진짜로" ESG를 잘하는지 평가하는 것이 아니다.

이 프로젝트는 **공시 연구(disclosure research)** 다. 측정 대상은 텍스트로 표현된 "언어"이고, 비교 대상은 KCGS라는 외부 평가 기관의 "등급"이다. 둘 사이의 관계, 그리고 둘 사이의 간극이 분석의 전부다.

---

## 2. 데이터 & 분석 단위

| 항목 | 값 |
|---|---|
| 분석 단위 | firm-year (기업 × 사업연도) |
| 표본 | 127개 상장기업 |
| 기간 | 2022, 2023, 2024 사업연도 |
| 총 관측치 | **381 firm-year** |
| 외부 평가 변수 | KCGS ESG 등급 (7단계 / 4단계 변환) |

데이터는 다음 식별자로만 연결된다 — **회사명으로 병합하지 않는다.**

`stock_code` → `corp_code` → `rcept_no` → `fiscal_year` / `esg_year`

자세한 계보 규칙과 결측 처리 원칙은 [`data/README.md`](data/README.md) 참조.

### 왜 사업보고서의 일부 섹션만 보는가

전체 보고서가 아니라 다음 3개 섹션만 분석 대상으로 삼았다.

| 섹션 | 내용 | ESG 언어가 등장하는 이유 |
|---|---|---|
| II. 사업의 내용 | 사업 전략, 제품/서비스 | 환경 리스크, 친환경 전략 언급 |
| IV. 이사의 경영진단 및 분석의견 | 경영진의 직접 진술 | 경영진이 ESG를 어떻게 "말하는지"가 가장 직접적으로 드러남 |
| VI. 이사회 등 회사의 기관에 관한 사항 | 지배구조 기구 | G(거버넌스) 정보의 주된 출처 |

전체 보고서를 다 보지 않은 만큼, 다른 섹션(재무제표 주석 등)에 있는 ESG 관련 서술은 이 분석에 포함되지 않는다 — 이는 의도된 범위 제한이며 한계이기도 하다.

---

## 3. 파이프라인 개요

```
사업보고서 원문 (DART)
   ↓  섹션 추출 (II / IV / VI)
ESG 관련 단락(passage)
   ↓  Kiwi 형태소 분석 + 사용자 사전
토큰
   ↓  TF-IDF (seed → 확장 사전 → cosine 유사도)
숫자 feature (E/S/G 점수, 분량 등)
   ↓  Spearman·Mann-Whitney 검증 → OLS/Ordered Logit/Binary Logit
통계적 연관성
   ↓
해석 + 한계
```

각 화살표가 하나의 방법론적 선택이다. "문장이 어떻게 숫자가 되었는지", "그 숫자가 회귀식에서 무엇을 의미하는지"는 `notebook/`의 Decision Box에 단계별로 기록되어 있다.

---

## 4. 방법론 요약

### Feature 구성 (3단계 계층)

1. **Seed TF-IDF** — 연구자가 정의한 E/S/G 키워드 사전 기반
2. **확장 사전 TF-IDF** — FastText cosine 유사도(θ=0.65)로 seed를 확장한 사전 기반
3. **참조문장 cosine 유사도** — 문서 임베딩과 E/S/G 대표 문장 간 유사도

한국어 SBERT(`ko-sroberta-multitask`) 기반 dense 임베딩도 비교했으나, 단어 기반 TF-IDF보다 성능이 낮았다 — 채택하지 않은 방법이지만, 정직하게 기록해 둔 결과다.

### 통계 검증 → 회귀

회귀 이전에 항상 **Spearman 순위상관**과 **Mann-Whitney U / Kruskal-Wallis 검정**으로 feature의 타당성을 1차 점검했다. 등급은 순서형(ordinal)이므로 Spearman이 적절하며, 통계적 유의성과 실질적 연관 강도(ρ)는 분리해서 해석했다(ρ 0.10–0.20은 약한 연관으로 간주).

회귀모형은 세 가지를 함께 사용했다.

| 모형 | 묻는 질문 |
|---|---|
| OLS (M1a) | 등급(연속 근사)과 feature는 선형적으로 연관되는가 |
| Ordered Logit (M1b) | 등급 순서를 그대로 살리면 결론이 같은가 (S차원은 비례오즈 가정 위반 → 방향성만 해석) |
| Binary Logit (M1c) | 상/하위 등급 이분화에도 결론이 같은가 (seed_G는 준완전분리 발생 → 해석에서 제외) |

M2는 재무 통제(log_assets, roa, leverage)를 추가한 모형이며, 재무 데이터 결측으로 인한 listwise exclusion 결과 n=344다 (결측을 0으로 채우지 않았다).

> 해석은 항상 "~와 연관된다", "~와 일관된다" 수준에 머문다. "ESG를 개선한다", "ESG 성과를 예측한다", "야기한다"는 표현은 쓰지 않는다 — association ≠ causation.

---

## 5. 핵심 결과

### 발견 1 — 분량이 ESG 언어보다 강한 신호

KCGS 등급과의 Spearman ρ를 비교하면, 단순 토큰 수(log_n_tokens)가 어떤 ESG 단어 기반 feature(seed/expanded/cosine, E·S·G 각 차원)보다도 더 강하게 등급과 연관된다. 자세한 수치는 `paper/`의 표(논문 Table 2) 참조 — 이 발견은 별도 그림이 아니라 표로 제시되어 있다.

### 발견 2 — 통제 후 G만 남는다

`paper/figures/fig1_governance_survives_controls.png`

분량(log_n_tokens)과 기업 규모(log_assets)를 통제한 M1→M2 회귀 비교에서, E·S 관련 feature의 연관성은 약해지거나 사라지는 반면 **G 관련 feature는 통제 이후에도 유의하게 남는다.**

### 발견 3 — Talk–Walk Gap, 44%

`paper/figures/fig2_talkwalk_gap_quadrant.png`

말(공시 언어 수준)과 등급을 각각 분량으로 잔차화(residualize)한 뒤 2×2로 나누면, 표본의 **44%**가 "말"과 "등급"이 어긋나는 비대각 분면(under-talk / over-talk)에 위치한다.

> 참고로 이와는 별개의 통계로, 127개사 중 76개(**59.8%**)는 3개년 내내 같은 유형(분면)에 머무는 구조적 고착을 보인다. 이는 "44% 불일치"와는 다른 질문(연도 간 안정성)에 대한 답이므로 혼동하지 않아야 한다.

### 발견 4 — 균일하지 않은, 선택적 공시

E/S/G 세 축을 동시에 보면, 한 기업이 특정 축을 부풀리고(top_inflated) 다른 축에는 침묵(most_silent)하는 패턴이 나타난다. 즉 ESG 공시는 세 축에 걸쳐 균일한 행동이 아니라 **선택적 행동**에 가깝다.

---

## 6. Cheap-Talk 관점과 한계

이 프로젝트는 cheap-talk 가설(기업이 ESG 언어를 전략적으로 과다 사용할 수 있다는 가설)을 핵심 관점으로 둔다. 발견 1·2가 이를 뒷받침한다 — 분량을 통제하지 않으면 신호가 부풀려져 보일 수 있다.

알아야 할 한계:

- `esg_year` 라벨이 `fiscal_year`와 동일하게 기록되어 있어, 가이드 정의(`esg_year = fiscal_year + 1`)와 한 해 어긋날 가능성이 있다.
- M2의 n=344는 재무 데이터 결측에 따른 listwise exclusion이다.
- S차원 Ordered Logit은 비례오즈 가정을 위반해 방향성만 해석했고, seed_G Binary Logit은 준완전분리로 해석에서 제외했다.
- 업종 통제는 결측이 커서(약 79%) 해석을 보류했다.
- 분석은 II/IV/VI 섹션에 한정되어 있어, 다른 섹션의 ESG 서술은 포함하지 않는다.
- association ≠ causation. 모든 결과는 "연관"이며 인과를 주장하지 않는다.

---

## 7. 저장소 구조

```
ESG_DART_Project/
├── README.md                  ← 이 파일
├── config.example.py          ← 설정 템플릿 (실제 API 키는 .gitignore 처리)
├── requirements.txt
├── pyproject.toml
│
├── paper/
│   ├── 3조_Short_Research_Paper.docx
│   └── figures/
│       ├── fig1_governance_survives_controls.png
│       └── fig2_talkwalk_gap_quadrant.png
│
├── notebook/
│   └── 3조_분석노트북.ipynb    ← 최종 분석 노트북 (Decision Box 포함)
│
├── src/                        ← 수집·전처리·feature 빌드 모듈
│
├── scripts/                    ← 파이프라인 실행 스크립트 (01~05 단계)
│
├── data/
│   ├── README.md               ← 데이터 계보·결측 처리 원칙
│   ├── sample/                  ← 최종 127사 / 381 firm-year 정의
│   └── dictionary/              ← E/S/G seed 사전, stopwords
│
└── research_log/
    ├── README.md
    ├── reports/                 ← 단계별 진행 보고서
    ├── recovery_pilot/          ← 초기 표본 복구 단계 기록
    ├── recovery_N381/           ← 전수(381) 수집 검증 기록
    └── notebooks_archive/       ← 최종 노트북 이전 작업 노트북
```

---

## 8. 재현 방법

```bash
git clone <repo-url>
cd ESG_DART_Project
pip install -r requirements.txt

cp config.example.py config.py
export OPENDART_API_KEY=<발급받은 키>

# 전체 분석은 notebook/3조_분석노트북.ipynb 참조
jupyter notebook notebook/3조_분석노트북.ipynb
```

원본 사업보고서 ZIP/XML과 KCGS 등급 원본 CSV는 용량·라이선스 문제로 저장소에 포함하지 않는다. 재수집 절차는 `scripts/01_collect.py`와 `research_log/recovery_N381/collect_381.py` 참조.

---

## 9. 데이터 출처 및 라이선스

- 사업보고서 원문: [OpenDART](https://opendart.fss.or.kr) (금융감독원 전자공시시스템)
- ESG 등급: 한국ESG기준원(KCGS) — 등급 원본 데이터는 재배포 권한이 불명확해 본 저장소에는 포함하지 않음
- 코드: 팀 3조 작성, 학술 프로젝트 목적

본 저장소는 학술 연구 프로젝트의 결과물이며, 상업적 ESG 평가 도구가 아니다.
