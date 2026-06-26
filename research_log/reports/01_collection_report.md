# 01 Collection — DART 사업보고서 ESG 패시지 수집 보고서

> **연구 질문**: 한국 사업보고서에 등장하는 ESG 관련 표현이 외부 ESG 평가와 통계적으로 연관되는가?
>
> 이 단계는 그 질문에 답하기 위한 **언어 데이터(텍스트)를 만들어내는 데이터 파이프라인**을 정의한다.
> 본 문서는 그 파이프라인의 설계 의도, 실행 결과, 한계, 그리고 디버깅 이력을 정리한다.

---

## 0. 한눈에 보는 결과 — SUCCESS / WARN / FAIL 요약

수집(`01_collect.py`) → XML 파싱 → 섹션 추출 → ESG 패시지 추출(`02_extract_sections.py`) 의 4단계 파이프라인을 81개 기업 × 3개 회계연도(FY2021–FY2023)에 대해 실행하였다. 동일 (stock_code, fiscal_year) 키 기준으로 `rcept_no` 1건만 채택(가장 최신 정정 공시) 하므로, 분석 단위는 **firm-year**가 된다.

| 단계 | 단위 | 건수 | 비율 |
|---|---|---:|---:|
| 1️⃣ DART API → ZIP 다운로드 성공 | rcept_no | **243** | 100.0% |
| 2️⃣ ZIP → XML 추출 성공 | rcept_no | **241** | 99.2% |
| 3️⃣ 섹션 II/IV/VI 추출 (text_length > 0) | rcept_no | **약 230** | ≈95% |
| 4️⃣ ESG 패시지 ≥ 1개 (firm-year document 생성) | firm-year | **213** | **87.7%** |

> **읽는 법** — 위 표가 "잃어버린 31건"이 어디서 새는지를 보여준다. 절반은 다운로드는 됐는데 정보가 없거나(보고서 본문이 첨부파일로 분리), 절반은 ESG 어휘가 매칭되지 않은(seed 사전 미커버) 케이스다.

### 0.1 실패 유형 분포 (단계별)

| Step | 유형 | rcept_no 고유 건수 | 대표 사례 |
|---|---|---:|---|
| `zip_download` | API 응답이 정상 ZIP이 아님 (status 014, 014="파일이 존재하지 않습니다") | 2 | 006110 삼아알미늄 FY2021, 009830 한화솔루션 FY2022 |
| `xml_extract` | `BadZipFile` — DART에서 ZIP 대신 오류 XML 반환 | 2 | (위와 동일 ZIP) |
| `passage_filter` | 섹션은 추출됐으나 ESG seed 0개 매칭 → `WARN_NO_PASSAGES` | 17 | LG(003550), 롯데지주(004990), 코웨이, 롯데쇼핑, 삼성E&A, 넷마블, 기아 등 |
| 기타 | 섹션이 추출됐지만 본문이 사실상 없음(text_length < 100) | ≈11 | 105560 KB금융, 055550 신한지주, 207940 셀트리온 일부 — **참조 안내문만 존재** |

### 0.2 WARN_NO_PASSAGES 17건의 패턴

| stock_code | 기업명 | 해당 fiscal_year |
|---|---|---|
| 000270 | 기아 | 2021, 2022 |
| 000880 | 한화 | 2022, 2023 |
| 003550 | LG | 2022 |
| 004990 | 롯데지주 | 2022, 2023 |
| 021240 | 코웨이 | 2021, 2022 |
| 023530 | 롯데쇼핑 | 2021, 2022, 2023 |
| 028050 | 삼성E&A | 2021, 2022 |
| 047050 | 포스코인터내셔널 | 2022 |
| 251270 | 넷마블 | 2022, 2023 |

지주회사(holding company)·완성차·유통 비중이 높다. 이들 보고서는 본문 대신 *"자세한 내용은 II. 사업의 내용을 참조하시기 바랍니다"* 형식의 참조 처리로 채워져 있어, 섹션 본문 자체가 짧다. 즉, **수집 실패가 아니라 "기업 공시 행태의 차이"가 우리 데이터에 그대로 흔적을 남긴 결과**다. 이 점은 분석 단계에서 "missing은 random하지 않다"는 한계로 기록되어야 한다.

---

## 1. 왜 ESG 패시지를 따로 뽑아야 하는가

연구 질문은 "보고서가 ESG 등급과 연관되는가"이지 "보고서 전체가 ESG 등급과 연관되는가"가 아니다.

사업보고서는 평균 **수십만 자**다. 그 안에는 재무제표, 감사보고서, 약정 조항, 부동산 임차계약, 임원 보수 등 ESG와 무관한 텍스트가 압도적이다. ESG 어휘를 그대로 TF-IDF에 넣으면 verbosity(전체 보고서 길이) 자체가 dominant signal이 되어버린다. cheap-talk 가설 — *"기업이 ESG 어휘를 과잉 사용하는 경향이 있는가"* — 을 검증하려면 먼저 **ESG가 등장할 가능성이 높은 구간만 분리**해야 한다.

### Decision Box — 전체 보고서 vs. 섹션 필터링
- **Alternative**: 전체 XML을 그대로 TF-IDF / KoBERT에 입력.
- **Choice**: 섹션 II / IV / VI만 추출.
- **Justification**: (1) ESG 언어는 특정 구간에 집중된다. (2) 노이즈가 dominant signal이 되는 것을 막는다. (3) firm-year 텍스트 길이 분산을 줄여 verbosity 통제 변수의 안정성을 높인다.
- **Limitation**: 사업의 내용에 ESG 표현을 적게 쓰고 별도 ESG 보고서로 분산하는 기업이 과소평가될 수 있다. 이는 placebo-style 한계로 명시되어야 한다.

---

## 2. 데이터 lineage — 한 줄 요약

```
stock_code  →  corp_code  →  rcept_no  →  ZIP  →  XML  →  섹션(II/IV/VI)  →  ESG 패시지  →  firm-year document
```

- `stock_code` : 증권코드(6자리). 외부 데이터(KCGS 등급, 재무)와 병합 키.
- `corp_code` : DART 고유 8자리 코드. API 호출 전 변환 필요(앞자리 0 보존을 위해 반드시 문자열로 처리).
- `rcept_no` : 공시 접수 번호. 정정 공시가 있으면 최신 것을 선택.
- `fiscal_year` : 보고서가 다루는 회계연도.
- `esg_year` : `fiscal_year + 1`. KCGS 평가가 다음 해에 공표되므로 시계열 정합성을 위해 분리해서 보관.

> [!summary] **lineage 원칙**: 어떤 단계에서도 `company_name`을 머지 키로 쓰지 않는다. 같은 기업이 같은 해 사업보고서를 정정 공시한 경우, `corp_code` + `report_date`로 식별한다.

---

## 3. DART OpenAPI 호출 흐름 (`01_collect.py` + `src/dart_api.py`)

### 3.1 4단계 호출

1. **corp_code 매핑 다운로드** — `https://opendart.fss.or.kr/api/corpCode.xml` (전체 기업 ZIP) → 한 번만 받아 캐싱.
2. **사업보고서 rcept_no 조회** — `/api/list.json` with `pblntf_detail_ty=A001`, `bgn_de=fy+1.01.01`, `end_de=fy+1.06.30`.
3. **정정 공시 최신본 선택** — `rcept_dt` 내림차순 정렬 후 첫 행.
4. **ZIP 다운로드** — `/api/document.xml` (응답이 실제로 ZIP인지 Content-Type으로 검증).

### 3.2 Decision Box — corp_code 캐싱
- **Alternative A**: 매 호출마다 `corp_code` 조회 API 사용.
- **Alternative B**: 전체 매핑 테이블을 한 번 받아 메모리/디스크 캐시.
- **Choice**: B.
- **Justification**: 상장 기업이 수천 개이므로 rate limit 위험이 크다. 매핑 자체가 빈번히 바뀌지 않는다.
- **Limitation**: 분기 중 상장/폐지 변동이 반영되지 않음. 수집 직전에 한 번 갱신하는 것을 표준 절차로 둔다.

### 3.3 Decision Box — 재시도 정책
- **Alternative A**: 단순 고정 대기.
- **Alternative B**: Exponential backoff.
- **Choice**: A (고정 대기 0.5초, 최대 3회).
- **Justification**: 81개 기업 × 3년 = 최대 243건 수준에서는 단순 정책으로 충분하다.
- **Limitation**: 수백 기업 단위로 확장 시 backoff로 전환해야 함.

---

## 4. ZIP → XML 파싱 — 가장 깊은 수렁

### 4.1 DART ZIP의 비표준성

DART 사업보고서 ZIP에는 보통 다음이 들어 있다:

```
└── 20230321001234.zip
    ├── (대표) 사업보고서.xml     ← 가장 큰 XML, 본문
    ├── 첨부_감사보고서.xml
    ├── 첨부_지배구조보고서.xml
    └── 이미지/PDF/기타 자료
```

- 파일명은 기업·연도·결재시스템마다 다르다.
- 인코딩이 `utf-8` / `euc-kr` / `cp949` 사이에서 가변적이다.
- XML 안에 HTML 테이블, 인라인 스타일, 깨진 태그가 혼재한다.

### 4.2 Decision Box — 본문 XML 선택 기준
- **Alternative A**: 파일명 패턴 매칭 (`*사업보고서*.xml`).
- **Alternative B**: 가장 큰 XML 선택.
- **Choice**: B.
- **Justification**: 파일명 규칙이 안정적이지 않아 패턴 매칭이 자주 깨진다. 본문이 일반적으로 가장 크다.
- **Limitation**: 별첨이 본문보다 큰 경우 오선택 가능. 이 경우 섹션 II/IV/VI 정규식이 결국 매칭에 실패해 `WARN_NO_PASSAGES`로 표면화된다.

### 4.3 Fix history — XMLSyntaxError와 `recover=True`

수집 초기에 `lxml.etree.XMLSyntaxError` 가 빈번하게 발생했다. 
원인:
- 닫히지 않은 태그 (`<P>` 만 있고 `</P>` 없음).
- HTML 엔티티 (`&nbsp;`, `&cr;`) 가 XML 파서에서 invalid로 판정.
- BOM·euc-kr 혼합 인코딩.

**해결 1**: 본문 추출은 `BeautifulSoup(xml_str, "html.parser")`로 일원화. `lxml` 대신 관대한(html.parser) 파서로 fallback.
- BeautifulSoup: 웹페이지나 XML/HTML 문서를 사람 대신 읽고 구조를 정리해주는 parser library

**해결 2** (이전 시도): `lxml.etree.parse(io.BytesIO(...), parser=etree.XMLParser(recover=True))` 를 시도. **`recover=True`** 옵션은 malformed XML에서 가능한 한 많은 노드를 복구하려고 시도한다. 다만 한국어 사업보고서의 비정상성은 단순 "끊긴 태그" 수준을 넘어서기 때문에, 최종적으로 `BeautifulSoup`이 가장 안정적인 선택이었다.
- recover=True: 깨진 부분이 있어도 읽을 수 있는 부분을 최대한 읽어보게함

**해결 3**: 인코딩 자동 탐지 (`utf-8 → euc-kr → cp949` 순서 디코딩 시도).

이 일련의 패치 이후 ZIP → XML 추출 성공률은 **약 92% → 99.2%**로 상승하였다.

### 4.4 잔존 XML 추출 실패 — DART가 빈 응답을 ZIP인 척 보내는 경우

| rcept_no | 기업 | FY | ZIP 크기 | 내용 |
|---|---|---|---|---|
| 20220325000460 | 삼아알미늄 | 2021 | 비정상 (작음) | `BadZipFile` |
| 20230316001209 | 한화솔루션 | 2022 | **147 bytes** | XML 응답: `<status>014</status><message>파일이 존재하지 않습니다.</message>` |

→ 즉 이건 코드 버그가 아니라 **DART 서버가 해당 rcept_no의 본문 파일을 제공하지 않은 케이스**다. 재시도해도 동일하다. 데이터 정직성 원칙에 따라 이 행은 절대 0으로 채우지 않고 `section_failed_logs.csv`에 사유와 함께 기록한다.
- ESG 단어가 없는 게 아니라 문서가 없는 거임

> [!summary] DART XML 이 깨지는 일이 빈번했고, parser 우회와 인코딩 처리, BeautifulSoup fallback으로 안정화함

---

## ==5. 섹션 추출 — II / IV / VI 만 분리

### 5.1 왜 이 세 섹션인가

| 섹션 | 제목 | 주된 ESG 신호 |
|---|---|---|
| **II** | 사업의 내용 | E (제품/환경 리스크/기술), 일부 S |
| **IV** | 이사의 경영진단 및 분석의견 | 경영진의 ESG narrative — cheap-talk 가설의 핵심 구간 |
| **VI** | 이사회 등 회사의 기관 | **G** (지배구조, 감사위원회, 사외이사) |

VI가 압도적으로 길고(중앙값 ≈ 130k자) ESG 패시지의 87%가 여기서 나온다. 이는 G 신호가 풍부함을 의미함과 동시에, "이사회 의결" 같은 정형 어휘가 `이사회`·`감사` 같은 G seed에 자주 매칭된다는 뜻이기도 하다. → ==분석 단계에서 G의 영향이 cheap-talk이 아니라 boilerplate일 가능성을 항상 의심해야 한다.==

> [!summary] 진짜 G 정보와 형식적인 반복 문구(cheap-talk) 구별 어려움
진짜 G정보: "감사위원회 독립성 강화" vs 형식&반복문구: "당사는 이사회 의결을 통해~"
G 신호가아니라 DART문서 형식의 boilerplate(반복되는 문구) 가능성 있음

### 5.2 Fix history — Fix F: 섹션 패턴 보강

#### 문제

삼성전자, SK하이닉스, LG화학 등 **대형 우량 기업**에서 섹션 II/IV가 수백 자만 추출되는 현상 발견. 예시:

| 기업 | FY | 섹션 II | 섹션 IV | 섹션 VI |
|---|---|---:|---:|---:|
| LG화학 | 2021 | **227자** | **66자** | 447,213자 |
| LG화학 | 2023 | **227자** | **66자** | 514,010자 |
| HD현대 | 2021 | 680자 | 565,949자 | 127자 |
| 셀트리온 | 2022 | 203자 | 181자 | 85자 |

#### 원인

기존 정규식은 ASCII 로마숫자(`II`, `IV`, `VI`)만 매칭했다. 그러나 DART XML에는 다음 변형이 혼재한다:

- 특수 유니코드 로마숫자: `Ⅱ` (U+2161), `Ⅳ` (U+2163), `Ⅵ` (U+2165)
- 제N장 표기: `제 2 장 사업의 내용`
- 숫자+점 표기: `2. 사업의 내용`
- 줄임 표기: `이사의 경영진단 및 분석` (뒤 단어 누락)
- -> text_length=0인 경우 많았음
#### 해결 (Regex 사용)

==`SECTION_PATTERNS` 에 **5종 변형 패턴을 추가하고, 첫 번째 매칭 위치를 채택한다.**
- 한 가지 제목 형식만 찾는 게 아니라 DART에서 쓰이는 모든 변형을 다 허용해서 찾음

```python
"II": [
    r"II[\.\s]*사업의\s*내용",
    r"Ⅱ[\.\s]*사업의\s*내용",          # U+2161
    r"제\s*2\s*장\s*사업의\s*내용",
    r"(?<!\d)2[\.\s]+사업의\s*내용",
    r"사업의\s*내용에\s*관한\s*사항",
]
```

#### Fix F의 효과

| 지표 | Fix F 이전 (추정) | Fix F 이후 |
|---|---:|---:|
| ZIP → XML 성공 | ≈ 90% | 99.2% |
| 섹션 II 미발견 (`text_length=0`) | ≈ 12 rcept_no | 4 rcept_no |
| firm-year document 생성률 | ≈ 75% | **87.7%** |
| 평균 ESG 패시지 / firm-year | (불안정) | **219개** (중앙값 161개) |

> 전처리 개선으로 실제 ESG text를 안정적으로 추출할 수 있게됨
> 
> ※ 정확한 pre/post 비교는 별도 ablation 로그가 필요. 위 값은 현재 결과를 보수적으로 기록한 것.

### 5.3 Fix history — 재무 hard stop (VI 섹션의 오확장 방지)

#### 문제

VI 섹션은 보고서 후반부에 위치하므로, 종료 위치를 찾지 못하면 그 뒤의 **재무제표 본문 / 감사보고서**까지 통째로 빨려 들어갔다. 그 결과 G 패시지에 `현금및현금성자산`, `매출채권` 같은 회계 boilerplate가 대량 유입.
- 이사회, 지배구조(G_signal) 찾으려고 하다보니 재무제표, 회계 주석과 같은 회계 boilerplate(부록)이 들어감 -> G_signal 보다는 재무제표 덩어리가 됨

#### 해결 — `FINANCIAL_STOP_PATTERNS`

VII / 재무에 관한 사항 / 감사보고서 시작 신호 / 재무제표 주석 키워드 등 9개 패턴 중 가장 빠르게 매칭되는 위치를 VI의 hard stop으로 적용.
- hard stop: "여기부터는 재무제표 시작" point를 생성, 이 단어 나오면 ==VI 섹션 강제 종료함으로써 재무제표 덩어리를 해체

```python
FINANCIAL_STOP_PATTERNS = [
    r"VII[\.\s]*재무에\s*관한\s*사항",
    r"독립된\s*감사의견\s*감사보고서",
    r"연결\s*재무제표\s*주석",
    r"본\s*감사인은.*재무제표에\s*대하여",
    r"(?m)^(현금및현금성자산|매출채권|유형자산|...)\s*[\d,]",
    ...
]
```

이 패치 이후 VI 섹션 평균 길이는 **약 700k자 → 225k자**로 줄어들었고, G 패시지의 finance boilerplate 비율이 눈에 띄게 감소했다.
: 우리가 측정하려는 ESG/G 언어와, 섞여 들어온 재무 boilerplate를 분리한 과정
- DART 사업보고서에서 ESG 관련 섹션만 안정적으로 추출하기 위해 regex 패턴 보강과 financial hard-stop 전처리를 수행했고, 이를 통해 ESG/G 언어와 재무 boilerplate를 효과적으로 분리함

---

>[!summary] 
>1. 제목 표기가 회사마다 달라서 II/IV/VI를 못 찾음 -> FIx F, 보고서에 사용된 모든 표현을 찾고 허용함 => ESG 텍스트 추출 안정화
>2. VI 뒤에 재무제표(부록)까지 빨려들어옴 -> Financial Hard Stop, 관련 신호 나오면 stop => 진짜 G-signal만 남기고 회계 boilerplate 제거

---
## 6. ESG 패시지 추출 (`src/passage_filter.py`) (필터링 규칙)

### 6.1 단위 — 왜 문단(paragraph)인가

- 단어 단위는 문맥을 잃는다. `환경` 이 `영업환경` 인지 `환경오염` 인지 구분 불가.
- 문장 단위는 너무 짧아 TF-IDF / BERT의 입력 분포가 불안정.
- → 문단 단위(min_length=30자, max_length=2000자)가 합리적 trade-off.

### 6.2 Seed 사전

```
E (16어): 탄소, 온실가스, 환경, 기후변화, 기후, 에너지, 재생에너지,
          탄소중립, 배출, 오염, 생태계, 녹색, 친환경, 탄소배출, 탄소발자국, 순환경제
S (15어): 안전보건, 인권, 다양성, 지역사회, 임직원, 공급망, 사회적, 노동, 복지,
          상생, 협력사, 산업재해, 사회공헌, 포용, 차별금지
G (12어): 이사회, 지배구조, 투명성, 윤리, 준법, 내부통제, 감사, 주주, 공시,
          ESG위원회, 이해관계자, 컴플라이언스
```

==`min_seed_count=1` 을 기본값으로 사용.== (sensitivity analysis는 `min_seed_count=2` 도 병행 저장.)
- 문단 안에 ESG seed 단어가 최소 1개만 있어도 ESG 후보 문단으로 인정함
- min_seed_count=1: recall 높음, ESG 문단 많이 살리지만 noise 증가
- min_seed_count=2: precision 높음, ESG 문단 놓칠 수 있지만 noise 감소


### 6.3 다단 필터 (3중 보존 원칙)

문단 → ESG seed 매칭만으로는 boilerplate 유입을 막을 수 없으므로, 세 가지 보수적 필터를 추가했다.

1. **G-protection rule**: `이사`, `감사`, `이사회` 등이 포함된 문장/문단은 **무조건 보존**. cheap-talk 가설 하에서 G 신호의 false negative가 가장 치명적이다.
	-  ==noise 있더라도 G 보존을 우선으로 둠
2. **Sentence-level density filter** (선택): 문단을 문장으로 쪼개 ESG/G seed 가 있는 문장 + 그 ±1 문장만 보존. 길이가 너무 길어진 문단의 정보 압축에 사용.
	- ==ESG 관련 문장 근처만 남김 -> 정보 압축 
3. **Boilerplate density filter** (선택): 어절의 25% 이상이 `재무제표`, `차입금`, `당기순이익` 같은 회계 단어이면 제거. 단 ESG/G seed가 있으면 통과.
	- ==재무제표 boilerplate 제거 

### 6.4 한 문단이 숫자가 되기까지 (sentence-level scoring)

`sentence_score()` 는 문장 한 줄을 다음 dict로 반환한다. 
: 문장 하나를 숫자로 바꾸는 함수

```python
{
  "is_g_protected": bool,
  "esg_hit": int, "g_hit": int, "generic_hit": int, "finance_hit": int,
  "length": int,
  "esg_density":     esg_hit / length * 100,
  "signal_density":  (esg_hit + g_hit) / length * 100,
  "generic_density": generic_hit / length * 100,
  "finance_density": finance_hit / length * 100,
}
```

여기서 **per-100자 정규화**가 핵심이다. 절대 빈도만 보면 보고서가 긴 기업이 ESG 어휘를 무조건 많이 쓴 것처럼 보이는 verbosity bias가 발생한다. 1자당 밀도로 환산하면 "기업이 ESG에 얼마나 *집중적으로* 말하는가"를 측정할 수 있고, 이는 cheap-talk vs. substantive ESG의 핵심 구분선이다.
- 보고서 긴 기업은 ESG 단어도 자동으로 많아짐 -> ESG 잘하는 기업인지, 그냥 문서가 긴건지 구분 어려움 => verbosity bias
- ==per-100자 정규화 (100자당 ESG 단어 몇 개?) 로 해결, 즉 **문서의 ESG 밀도로 판단**==

### 6.5 cheap-talk proxy 피처

문장 단위 점수를 firm-year로 집계한 결과 중에서 cheap-talk 가설에 직접 대응되는 feature를 proxy(대리변수)로 사용해서 보여줌
- cheap-talk 간접 지표

- ==`generic_rhetoric_ratio`== : ESG/G 신호 없이 *지속가능*·*글로벌*·*전략적* 같은 generic만 있는 문장 비율. → cheap-talk 강도의 proxy.
	- **높을수록 말만 많은 cheap-talk 가능성 높음
- ==`esg_to_generic_ratio`== : ESG 밀도 ÷ generic 밀도. → 높을수록 generic 미사여구로 희석되지 않고 substantive함.
	- **높을수록 실제 ESG 내용 많고, 미사여구가 적음
- `mean_finance_density` : 재무 boilerplate 밀도. → control variable.

---

> [!summary] ESG seed 단어만 매칭하지 않고, G_signal 보호 규칙·문장 밀도 필터·재무 boilerplate 제거를 결합한 다단 필터링을 통해 ESG 관련 문단을 필터링했으며, 이후 ESG 언어 밀도를 per-100자 기준으로 정규화하여 verbosity bias를 통제했다.

---
## 7. firm-year document — 분석의 최종 단위

`build_firm_year_document(passages)` 는 한 기업의 한 회계연도 ESG 패시지들을 단순 concatenation 해 하나의 큰 문자열로 만든다. 이것이 회귀분석의 단위가 된다.
- 최종 분석 단위: 기업 1개 x 연도 1개
	- '삼성전자-2023'이 각각 데이터 1행
- ESG 문단 -> 하나의 긴 ESG document = firm-year document

### 7.1 `passage_count` (a.k.a. `n_passages_body`) 분포

: 그 기업 연도에서 ESG로 잡힌 문단 개수

| 통계 | 값 |
|---:|---:|
| n (firm-year) | 213 |
| mean | 219.5 |
| std | 160.3 |
| min | 1 |
| 25% | 109 |
| median | 161 |
| 75% | 304 |
| max | 965 (POSCO홀딩스 FY2023) |

`total_char` (firm-year document 길이) 분포:

| 통계 | 값 |
|---:|---:|
| mean | 35,055자 |
| median | 24,031자 |
| min | 52자 |
| max | 169,589자 |

> **해석 주의** — passage_count가 큰 기업이 ESG가 강한 기업이 아니다. POSCO홀딩스 965개 패시지는 보고서 자체가 방대하기 때문이지, ESG 성과의 신호가 아니다. → ==회귀분석에서 반드시 `total_word_count` 또는 `total_char`를 통제 변수로 넣는다 (verbosity control).

- 원래 문서가 긴 효과를 제거함함

### 7.2 분포의 양극단

| 위치  | 기업                | FY         | passage_count | 비고                 |
| --- | ----------------- | ---------- | ------------: | ------------------ |
| 최저  | 셀트리온 (068270)     | 2022, 2023 |             1 | 본문이 "참조 안내문"으로만 구성 |
| 최저  | HD현대 (267250)     | 2021       |             1 | 동일                 |
| 상위  | POSCO홀딩스 (005490) | 2023       |           965 | 보고서 자체가 거대         |
| 상위  | POSCO홀딩스 (005490) | 2022       |           824 |                    |
| 상위  | 한화 (000880)       | 2021       |           676 |                    |

==극단값이 분석에 미치는 영향은 `log(passage_count)` 변환과 winsorization으로 통제한다.

---

## 8. 배치 수집 흐름 (`02_extract_sections.py --row_start --row_end --append`)

### 8.1 왜 배치인가

- 81 firm × 3 yr = 243 ZIP 처리. 한 ZIP이 평균 500KB ~ 1MB, 큰 것은 30MB 이상.
- 메모리 부담과 단일 실패 시 전체 손실 위험 때문에 50~100건씩 끊어 실행했다.
> 큰 DART XML 처리 안정화
### 8.2 checkpoint flush 메커니즘

- 매 배치는 `--row_start N --row_end M --append` 인자로 실행.
- `--append` 가 켜져 있으면 `extracted_sections.csv` 의 `rcept_no` 를 읽어 **이미 처리된 행을 자동 skip** (resume).
- 한 배치가 끝날 때마다 4개 CSV(`extracted_sections`, `esg_passages`, `firm_year_documents`, `section_failed_logs`) 가 모두 디스크에 flush 된다.
> 이미 처리한 rcept_no 자동 skip
### 8.3 batch success rate 추이

|                   배치 | 처리 rcept_no | 신규 firm-year doc |    누적 성공률 |
| -------------------: | ----------: | ---------------: | --------: |
|        초기 (Fix F 이전) |          30 |               22 |       73% |
|      중기 (Fix F 적용 후) |          80 |               74 |       86% |
| 후기 (재무 hard stop 추가) |         133 |              117 |       88% |
|                전체 누적 |     **243** |          **213** | **87.7%** |

> 위 표는 로그에 직접 기록된 수치가 아니라 패치 적용 시점을 기준으로 한 묶음 추정값이다. 정확한 추적이 필요하면 `data/02_sections/extract_run.log` 의 timestamp별 saved row count 차이를 재계산해야 한다.

>전처리와 regex 수정(Fix F, hard stop)을 할수록 ESG 문서를 훨씬 잘 추출하게 되었다.

### 8.4 Decision Box — 실패 행을 채울 것인가
- **Alternative A**: 실패 rcept_no를 0으로 채우거나 mean imputation.
- **Alternative B**: 실패 행은 별도 로그로 보관, 분석에서 제외.
- **Choice**: B.
- **Justification**: 데이터 정직성. 실패 패턴이 random하지 않으므로(지주회사 비중 ↑) imputation은 selection bias를 더 심각하게 만든다.
- **Limitation**: n 손실. 그러나 손실의 원인을 transparent하게 기록하는 것이 분석의 신뢰성을 높인다.

---

## 9. 한계와 위험 (반드시 분석 단계에 들고 갈 것)

1. **selection은 random하지 않다**. WARN_NO_PASSAGES 17건 중 다수가 지주회사·유통이다. ESG 어휘가 본문에 적게 등장하는 것은 *기업의 공시 전략 자체*일 수 있다 — 이미 cheap-talk 가설의 일부다.
2. **seed 사전은 사전적·관용적**. 산업별 ESG 표현(반도체의 *수자원*, 통신의 *전자파*, 금융의 *책임투자*)을 완전히 커버하지 못한다. → 다음 단계에서 fastText / KoBERT 확장이 필요한 이유.
3. **VI 비대칭성**. G 패시지가 ESG 패시지의 87%를 차지(이사회/감사 관련 정형 어휘 영향). E·S에 비해 G가 과대평가될 위험.
4. **시계열 정합성**. `fiscal_year` 와 `esg_year` 는 1년 차이가 있다. KCGS 평가는 다음 해에 공표되므로, 회귀에서는 "ESG 언어(t) → KCGS 등급(t+1)" 의 시간 방향을 일관되게 유지해야 한다.
5. **인과 추론은 불가능**. 이 데이터는 association만 말한다. *언어가 평가를 만든다*는 해석은 데이터로 검증할 수 없다.

---

## 10. 산출물 카탈로그

| 경로 | 단위 | 행 수 | 용도 |
|---|---|---:|---|
| `data/01_raw/collected_reports.csv` | rcept_no | 243 | 다운로드 성공 목록 |
| `data/01_raw/failed_logs.csv` | rcept_no | 0 | 다운로드 단계 실패 (현재 비어 있음) |
| `data/02_sections/extracted_sections.csv` | rcept_no × section | 729 (=243×3) | 섹션별 텍스트 (5,000자 미리보기 포함) |
| `data/02_sections/section_failed_logs.csv` | rcept_no × step | 74 | XML/섹션/패시지 실패 사유 로그 |
| `data/03_passages/esg_passages.csv` | passage | 30,658 | 문단 단위 ESG 패시지 |
| `data/03_passages/firm_year_documents.csv` | **firm-year** | **213** | **최종 분석 단위** |

> `firm_year_documents.csv` 가 다음 단계(03 전처리, 04 평가, 05 회귀)의 단일 입력원이다.

---

## 11. 이 단계가 답하지 *못하는* 질문

- "ESG 패시지가 많다"는 것이 ESG 성과가 좋다는 것이 아니다. → 회귀 단계에서 verbosity 통제 후 잔존하는 신호만 해석 가능.
- 추출된 ESG 표현이 *진실한* 약속인지 *수사적* 표현인지 텍스트만으로는 알 수 없다. → cheap-talk 가설 검증은 KCGS 등급과의 *연관성 부재* 또는 *역방향 패턴*으로만 간접적으로 평가된다.
- 산업별 ESG 어휘 차이를 단일 seed 사전이 흡수하지 못한다. → 향후 산업 분류(KSIC) 기반 정규화 또는 fastText 확장으로 보완.

---

*This document is the working record of the collection stage. 결과 수치는 데이터 재실행 시 갱신되므로, 표 아래 footnote에 실행 timestamp를 함께 적어두는 것을 권장한다.*

**Last updated**: 2026-05-19
