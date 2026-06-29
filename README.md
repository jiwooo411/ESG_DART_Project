# ESG Disclosure Language vs. ESG Ratings
### Talk–Walk Gap: 공시 언어와 ESG 평가 사이의 간극을 측정하는 프레임워크

**More ESG words do not mean a better ESG rating — disclosure volume does most of the talking.**

사업보고서의 ESG 공시 "언어"가 외부 ESG "평가"(KCGS 등급)와 실제로 정합하는지를, 127개 상장기업 × 2022–2024년(381 firm-year)으로 진단한 공시 연구 프로젝트

![Data](https://img.shields.io/badge/data-DART%20사업보고서-blue)
![Sample](https://img.shields.io/badge/sample-381%20firm--year-blueviolet)
![Method](https://img.shields.io/badge/method-TF--IDF%20→%20OLS%2FLogit-orange)
![Stats](https://img.shields.io/badge/stats-Spearman%20·%20Mann--Whitney-informational)
![Python](https://img.shields.io/badge/python-3.x-3776AB?logo=python&logoColor=white)

<p align="center">
  <img src="paper/figures/fig2_talkwalk_gap_quadrant.png" width="640" alt="Talk-Walk Matrix 2x2 유형 분류"><br>
  <sub><b>Figure 2.</b> Talk–Walk Matrix — 공시 언어(Talk)와 외부 평가(Walk)의 격차로 기업을 4유형으로 분류. 표본의 <b>44%</b>(과잉공시·과소공시)가 어긋난 유형에 위치(N=381).</sub>
</p>

> 원본 사업보고서 ZIP/XML과 KCGS 등급 CSV는 용량·라이선스 문제로 미포함. 코드·문서·검증표·그림만 공개. → [`data/README.md`](data/README.md)

---

## 30초 요약

**질문.** 사업보고서의 ESG 관련 표현은 외부 ESG 평가(KCGS 등급)와 통계적으로 연관되는가. ESG 성과 자체가 아니라 **공시 언어와 외부 평가 사이의 간극(gap)** 을 측정.

**핵심 발견.**
- 공시 **분량**(단순 토큰 수)이 어떤 ESG 단어 기반 feature보다 등급과 강하게 연관 — 분량이 ESG 언어보다 강한 신호.
- 분량·규모를 통제하면 E·S 신호는 사라지고 **G(거버넌스)만 독립 신호로 잔존**.
- 표본의 **44%** 가 말(공시 언어)과 등급이 어긋나는 Talk–Walk Gap에 위치 — 이를 **Talk–Walk Matrix**(과잉공시·과소공시·정합·일관저조 4유형)로 분류하면 유형마다 필요한 전략이 다르다.
- 기업은 E·S·G에 균일하게 공시하지 않고 특정 축은 부풀리고 다른 축엔 침묵 — **선택적 공시**.

**내 역할.** 4인 팀 프로젝트(김혜성·이동원·김지우·신지영). 수집·전처리·feature 설계·검증·회귀·해석을 공동 수행, 개별 구간을 단독 기여로 분리하지 않음.

**방법.** DART 사업보고서 II/IV/VI 섹션 → Kiwi 형태소 + 사용자 사전 → TF-IDF(seed → 확장 사전 → cosine) → Spearman·Mann-Whitney → OLS / Ordered Logit / Binary Logit.

**의미.** 이 프로젝트는 ESG 텍스트 분석이나 ESG 성과 예측이 아니다. **분량 효과를 제거해 측정 타당성을 확보하고, 그 위에서 Talk–Walk Gap으로 기업을 유형화하는 측정 프레임워크**다.

---

## 왜 중요한가

선행연구는 두 갈래로 멈춘다. 공시를 잘하면 등급이 높다는 평균효과 진단에서 그치거나, ESG를 하나의 점수로 합쳐서 기업이 어떤 축은 부풀리고 다른 축은 침묵하는 축 간 선택을 보지 못한다. 이 프로젝트는 두 빈틈을 모두 겨냥해, 기업이 사업보고서에서 **무엇을 말하는지(Talk)** 와 외부 기관(KCGS)에 **어떻게 평가받는지(Walk)** 사이의 간극을 firm 단위로 측정한다.

분량 통제가 출발점인 이유는 단순하다. 표본 보고서의 글자 수는 최소 4,513자에서 최대 189,606자까지 약 42배 벌어진다. 보고서가 길면 어떤 단어든 더 많이 등장하므로, ESG 어휘가 많다는 사실만으로 평가가 좋다고 읽으면 분량 효과를 신호로 착각한다. 분량을 통제해야 비로소 ESG 어휘 자체의 신호를 볼 수 있다.

분량을 걷어내자 등급과 함께 가는 신호는 거버넌스(G) 어휘만 남았다. 여기서 멈추지 않고 회귀의 평균효과를 개별 기업 단위로 끌어내린 것이 Talk–Walk Gap이다 — 기업이 자기 등급에 비해 ESG를 얼마나 과하게 또는 적게 말하는지를 계산해 유형화하고 처방까지 잇는다.

실무적 의미도 이 진단에서 나온다. 공시 어휘량을 액면 그대로 믿으면 분량·규모 착시에 노출되고, 합산 등급은 축 간 차이를 가린다. Talk–Walk Matrix는 등급과 언어 중 무엇을 더 보강해야 하는지를 기업 단위로 짚어 준다.

이 프로젝트의 산출물은 ESG 점수를 예측하는 모델이 아니라, **분량 효과를 제거해 측정 타당성을 확보하고, 그 위에서 기업을 Talk–Walk Matrix로 유형화해 전략을 제안하는 측정 프레임워크**다.

---

## 데이터 & 분석 단위

| 항목 | 값 |
|---|---|
| 분석 단위 | firm-year (기업 × 사업연도) |
| 표본 | 127개 상장기업, 2022·2023·2024 사업연도 = **381 firm-year** |
| 외부 평가 변수 | KCGS ESG 등급 (7단계 / 4단계 변환) |
| 분석 섹션 | 사업보고서 II(사업의 내용)·IV(경영진단)·VI(이사회·기관) |
| 병합 식별자 | `stock_code` → `corp_code` → `rcept_no` → `fiscal_year` (회사명 병합 안 함) |

> 섹션을 3개로 제한한 것은 ESG 언어가 집중되는 영역이기 때문이며, 다른 섹션의 ESG 서술은 미포함 — 의도된 범위 제한이자 한계. 계보·결측 처리 원칙: [`data/README.md`](data/README.md).

---

## 기술 스택

| 구분 | 도구 |
|---|---|
| 언어 | Python 3.x |
| 데이터 수집 | OpenDART API · requests · lxml · BeautifulSoup |
| 한국어 처리 | Kiwi (kiwipiepy) · KoNLPy(Okt) + 사용자 사전 |
| Feature | scikit-learn TF-IDF (seed → FastText 확장 사전 → cosine 유사도) |
| 통계·회귀 | Spearman · Mann-Whitney U / Kruskal-Wallis · OLS · Ordered/Binary Logit |
| 시각화 | matplotlib |

---

## 파이프라인

```
사업보고서 원문 (DART)
   ↓  섹션 추출 (II / IV / VI)
ESG 관련 단락(passage)
   ↓  Kiwi 형태소 분석 + 사용자 사전
토큰
   ↓  TF-IDF (seed → 확장 사전 → cosine 유사도)
숫자 feature (E/S/G 점수, 분량 등)
   ↓  Spearman·Mann-Whitney 검증 → OLS / Ordered Logit / Binary Logit
통계적 연관성 → 해석 + 한계
```

각 화살표가 하나의 방법론적 선택. "문장이 어떻게 숫자가 되었는지", "그 숫자가 회귀식에서 무엇을 의미하는지"는 [`notebook/3조_분석노트북.ipynb`](notebook/3조_분석노트북.ipynb)의 Decision Box에 단계별 기록.

---

## 설계 의사결정

> 핵심은 결과 수치가 아니라 "왜 그렇게 설계했는가". 채택하지 않은 방법과 제외한 산출물까지 기록.

| 결정 | 이유 |
|---|---|
| 식별자 기반 병합 (회사명 X) | `stock_code → corp_code → rcept_no → fiscal_year` 계보로 firm-year 정합성 보장, 회사명 병합 오류 차단 |
| 분량(log_n_tokens) 통제 | 분량이 ESG 언어보다 강한 신호 → 통제하지 않으면 신호가 과대평가됨. 통제 후 G만 잔존 |
| 회귀 3종 병행 | OLS·Ordered Logit·Binary Logit 교차 확인 — 등급의 순서형 특성·이분화에도 결론이 일관되는지 검증 (가정 위반 차원은 방향성만 해석) |
| TF-IDF 채택, SBERT 제외 | dense 임베딩(`ko-sroberta-multitask`)이 단어 기반 TF-IDF보다 성능 낮음 → 채택 안 한 결과도 정직하게 기록 |
| N=209 pilot 표 공개 제외 | 최종 N=381과 결론이 충돌(G 계수 부호 상이)·혼동 우려 → "없는 것이 틀린 것보다 낫다"는 재현성 우선 원칙 |

> 해석은 "~와 연관된다" 수준에 한정. "개선한다·예측한다·야기한다"는 쓰지 않음 — association ≠ causation.

---

## 핵심 결과

네 가지 발견이 분량 효과 → 거버넌스 신호 → Talk–Walk Matrix → 선택적 공시 순으로 이어지며, 모든 수치는 N=381 표본 기준.

**발견 1 — 가장 강한 신호는 ESG 어휘가 아니라 분량이다.** KCGS 등급과의 Spearman ρ 비교에서 단순 토큰 수(log_n_tokens, ρ=0.663)가 모든 ESG 단어 기반 feature보다 등급과 강하게 연관. 수치는 논문 Table 2(`paper/`).

**발견 2 — 분량을 걷어내면 거버넌스만 남는다. 이 결과가 이후 Talk–Walk Gap 계산의 전제가 된다.** 분량·규모를 통제한 M1→M2 회귀에서 G feature만 유의하게 잔존(β=1.955, p<0.001), E·S 신호는 약해지거나 사라진다.

<p align="center">
  <img src="paper/figures/fig1_governance_survives_controls.png" width="700" alt="분량·규모 통제 후 거버넌스 신호만 잔존"><br>
  <sub><b>Figure 1.</b> 분량(log_n_tokens)과 기업 규모(log_assets)를 통제한 M1→M2 회귀 비교. E·S 관련 신호는 약해지거나 사라지는 반면 <b>G(거버넌스) 관련 feature는 통제 이후에도 유의하게 잔존</b>.</sub>
</p>

**발견 3 — Talk–Walk Matrix: 44%가 어긋나고, 유형마다 처방이 다르다.** 회귀가 평균적 연관을 보여준다면, 분량을 걷어낸 말(talk)–등급(walk)의 격차는 개별 기업이 그 평균에서 얼마나 벗어났는지를 보여준다. 말과 등급을 각각 분량으로 잔차화한 뒤 2×2로 나눠 **Talk–Walk Matrix**(과잉공시·과소공시·정합·일관저조 4유형)를 만들면 표본의 44%가 비대각 유형(과잉공시·과소공시)에 위치한다. 이 매트릭스가 본 프로젝트의 대표 결과이며, 다음 표의 유형별 전략 제언으로 이어진다.

<p align="center">
  <img src="paper/figures/fig2_talkwalk_gap_quadrant.png" width="640" alt="Talk-Walk Matrix 2x2 유형 분류"><br>
  <sub><b>Figure 2.</b> Talk–Walk Matrix — 분량 잔차화 후 말(가로)×등급(세로) 2×2 유형 분류. 과잉공시 72 · 과소공시 96 · 정합 119 · 일관저조 94(N=381). 비대각 유형(과잉·과소공시)에 표본의 <b>44%</b>가 위치.</sub>
</p>

수익성은 네 유형 간 차이가 없어(Kruskal-Wallis p=0.205) 과잉·과소공시 모두 부실기업의 문제는 아니다. 이 두 유형만 처방이 필요하며, 처방의 방향이 서로 다르다.

| 유형 | 특징 | 공시 전략 제언 |
|---|---|---|
| **과잉공시(over-talk)** | 소형·저등급 중심, 구조적 11개사 | 등급에 비해 말이 앞서 신뢰 할인·greenwashing 점검 위험 — 배출량, 안전교육 이수율, 사외이사 비율 등 검증 가능한 수치로 서술 보강 |
| **과소공시(under-talk)** | 대형·고등급 중심, 구조적 21개사 | 실력에 비해 ESG 언어가 약해 저평가 위험 — 실질 성과를 별도 ESG 섹션·요약으로 응집해 가시화 |

> 정합·일관저조 유형은 처방 대상이 아님. 근거: 논문 5.2절, 설계 근거 [`research_log/reports/05b_talkwalk_gap_design_rationale.html`](research_log/reports/05b_talkwalk_gap_design_rationale.html).

**발견 4 — 마지막 층위, 축 간 선택적 공시.** Talk–Walk Matrix는 E·S·G를 하나로 합친 종합 격차였다. 종합 점수로는 가려졌던 결을 보려면 한 단계 더 들어가 세 축을 따로 떼어봐야 한다. firm-year의 47.2%가 한 축은 부풀리고(top_inflated) 다른 축엔 침묵(most_silent)한다 — 균일한 공시가 아니라 선택적 공시다. 사회(S)를 부풀린 기업은 실제 S등급이 2.08로 전체 평균(3.03)보다 낮아 약점 은폐에 가깝고, 거버넌스(G)를 부풀린 기업은 실제 G등급이 평균 이상으로 강점 신호에 가깝다. 분량 효과 제거(발견 1·2)와 기업 단위 유형화(발견 3)를 축 단위로 한 번 더 분해한 결과로, 이 저장소가 도달하는 가장 세밀한 해석 층위다.

<details>
<summary><b>해석 시 주의할 별도 통계</b></summary>

<br>

127개사 중 76개(**59.8%**)는 3개년 내내 같은 분면에 머무는 구조적 고착을 보임. 이는 "44% 불일치"와는 다른 질문(연도 간 안정성)에 대한 답이므로 혼동하지 않아야 함. Talk–Walk Gap을 헤드라인 지표로 선택한 설계 근거(대안 비교 포함): [`research_log/reports/05b_talkwalk_gap_design_rationale.html`](research_log/reports/05b_talkwalk_gap_design_rationale.html).

</details>

---

## 기여 (팀 프로젝트)

> 4인 공동 프로젝트(김혜성·이동원·김지우·신지영). 아래는 면접에서 방어 가능한 범위.

| 영역 | 한 일 |
|---|---|
| 문제 정의 | ESG 측정이 아니라 공시 언어–외부 평가의 간극(gap) 측정으로 재정의 |
| 데이터 계보 | 회사명 대신 식별자 체인 병합, firm-year 정합성·결측 처리 원칙 수립 |
| Feature 설계 | seed → FastText 확장 → cosine 3단계 TF-IDF, SBERT 비교 후 미채택 기록 |
| 통계·회귀 | Spearman·Mann-Whitney 사전 검증 후 OLS·Ordered·Binary Logit 교차 |
| 해석·재현성 | 분량 통제 해석, N=209 stale 표 제외 등 데이터 디서플린 |

**정직한 경계.** 인과 주장 없음(association ≠ causation) · 분석은 II/IV/VI 섹션 한정 · M2 n=344(재무 결측 listwise) · S차원 Ordered Logit은 가정 위반으로 방향성만, seed_G Binary Logit은 준완전분리로 제외 · 개별 팀원 기여를 단독으로 분리하지 않음.

---

## Key Takeaway

이 프로젝트의 메시지는 두 단계로 이어진다.

첫째, **"ESG 공시의 양과 ESG 평가의 질은 다르다."** 분량이라는 교란 변수를 통제하기 전과 후의 결론이 달라지므로(E·S 신호 소멸, G만 잔존), ESG 텍스트 분석은 **무엇을 통제했는가**가 결과를 좌우한다. 측정 대상을 "ESG 성과"가 아니라 "언어와 평가의 간극"으로 좁힌 설계가 과장 없이 방어 가능한 결론을 가능하게 했다.

둘째, **기업은 동일한 ESG 전략이 아니라 Talk–Walk 유형별 전략이 필요하다.** 같은 44%의 불일치라도 과잉공시형과 과소공시형의 원인과 처방은 정반대다 — 전자는 검증 가능한 수치 보강이, 후자는 실질 성과의 가시화가 필요하다. Talk–Walk Matrix는 이 차이를 기업 단위로 짚어내는 이 프로젝트의 핵심 산출물이다.

---

<details>
<summary><b>한계</b></summary>

<br>

1. `esg_year`가 `fiscal_year`와 동일 기록 → 가이드 정의(`esg_year = fiscal_year + 1`)와 한 해 어긋날 가능성.
2. M2의 n=344는 재무 데이터 결측에 따른 listwise exclusion (결측을 0으로 채우지 않음).
3. S차원 Ordered Logit은 비례오즈 위반 → 방향성만, seed_G Binary Logit은 준완전분리 → 제외.
4. 업종 통제는 결측 약 79%로 해석 보류.
5. 분석은 II/IV/VI 섹션 한정 → 다른 섹션의 ESG 서술 미포함.
6. 모든 결과는 연관(association)이며 인과 주장 없음.

</details>

<details>
<summary><b>재현</b></summary>

<br>

```bash
git clone <repo-url>
cd ESG_DART_Project
pip install -r requirements.txt

cp config.example.py config.py
export OPENDART_API_KEY=<발급받은 키>

jupyter notebook notebook/3조_분석노트북.ipynb   # 전체 분석 (Decision Box 포함)
```

원본 사업보고서 ZIP/XML과 KCGS 등급 CSV는 용량·라이선스 문제로 미포함. 재수집 절차: `scripts/01_collect.py` · `research_log/recovery_N381/collect_381.py`.

</details>

<details>
<summary><b>협업 규칙</b></summary>

<br>

팀 저장소 기준 협업 흐름. AI 에이전트(Claude · Codex 등) 작업 시에도 동일 규칙 준수. 상세: [`CONTRIBUTING.md`](CONTRIBUTING.md).

- **흐름.** `main` pull → 작업 브랜치 → commit → push → PR → 리뷰 → merge.
- **브랜치 네이밍.** `<type>/<short-topic>`. `claude/*`·`codex/*` 임의 브랜치 금지.
- **커밋.** [Conventional Commits](https://www.conventionalcommits.org) — `feat`·`fix`·`docs`·`refactor`·`chore`.
- **PR.** 무엇을·왜·리뷰 포인트만 간단히. merge는 팀 확인 후 수행.

</details>

---

## 저장소 구조

```
.
├── README.md · CONTRIBUTING.md · LICENSE · requirements.txt · config.example.py
├── paper/         # 최종 논문(docx) + figures (fig1·fig2)
├── notebook/      # 3조_분석노트북.ipynb — 최종 분석 (Decision Box 포함)
├── src/           # 수집·전처리·feature 빌드 모듈
├── scripts/       # 파이프라인 실행 스크립트 (01~05 단계)
├── data/          # README + sample(127사/381 firm-year 정의) + dictionary(E/S/G 사전)
├── research_log/  # reports · recovery_pilot · recovery_N381 · notebooks_archive
└── results/       # validation(Spearman·Mann-Whitney·분량직교성, N=381) + tables(NOTE)
```

> 원본 데이터·API 키·N=209 stale 산출물은 `.gitignore`로 제외. `results/tables/`를 비워 둔 이유는 [`results/tables/NOTE.md`](results/tables/NOTE.md) 참조 — 잘못된 표보다 빈 폴더를 택함.

---

## 데이터 출처 및 라이선스

- 사업보고서 원문: [OpenDART](https://opendart.fss.or.kr) (금융감독원 전자공시시스템)
- ESG 등급: 한국ESG기준원(KCGS) — 등급 원본은 재배포 권한 불명확으로 미포함
- 코드: 3조 작성, 학술 프로젝트 목적

본 저장소는
ESG 점수 예측 모델이 아니라
공시 언어와 외부 평가 사이의 간극을 분석하는 연구 프로젝트이다.
