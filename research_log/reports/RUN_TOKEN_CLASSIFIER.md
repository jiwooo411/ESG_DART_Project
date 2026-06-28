# Token 자동 분류기 실행 가이드

## 개요

`src/token_classifier.py`는 tokenized CSV의 상위 토큰을 5개 범주로 자동 분류한다.

```
G_SIGNAL → ESG_SIGNAL → AMBIGUOUS → BOILERPLATE → GENERIC
```

## 실행 순서

### Step 1: token_audit CSV 생성 (없는 경우)

```bash
cd C:\projects\esg_dart
python -m src.token_audit --exp exp_A --top_n 500
```

출력: `data/04_preprocessed/token_audit_exp_A.csv`

### Step 2: 자동 분류 실행

```bash
python -m src.token_classifier --exp exp_A --top_n 500
```

또는 token_audit을 함께 생성하려면:

```bash
python -m src.token_classifier --exp exp_A --top_n 500 --generate_audit
```

출력:
- `data/04_preprocessed/token_taxonomy_exp_A.csv`  — 전체 분류 결과
- `data/04_preprocessed/ambiguous_review_exp_A.csv` — 수동 검토 대상
- `data/04_preprocessed/PREPROCESSING_DECISIONS.md` — 의사결정 로그 (append)

### Step 3: AMBIGUOUS 수동 검토

`ambiguous_review_exp_A.csv`를 Excel로 열어서
`manual_class` 컬럼에 분류를 채운다.

```
manual_class 값: G_SIGNAL / ESG_SIGNAL / BOILERPLATE / GENERIC
keep_note: 판단 근거 (한 줄)
```

**예시 판단:**
- `주주` → 맥락에 따라. "주주가치"면 G_SIGNAL, "주주총회 소집 공고"면 BOILERPLATE
- `경영` → "지속가능경영"이면 ESG_SIGNAL, "경영성과"면 GENERIC
- `위원회` → ESG·감사위원회 맥락이면 G_SIGNAL, 단순 의결기구면 AMBIGUOUS 유지

### Step 4: 검증

```bash
python -m src.token_audit --validate --exp exp_A
```

ESG_PRESERVE ↔ BOILERPLATE 충돌 검사, G_SIGNAL 오분류 경고 확인

### Step 5: 불용어 업데이트 파일 내보내기 (수동 검토 완료 후)

```bash
python -m src.token_classifier --exp exp_A --export_stopwords --manual_reviewed
```

출력: `data/04_preprocessed/stopword_update_exp_A.py`
→ 이 파일을 보고 `src/preprocessor.py`의 `BOILERPLATE_NOUNS`를 업데이트

### Step 6: exp_E / exp_F 재실행

```bash
python 03_preprocess_experiment.py
```

---

## 핵심 원칙

### G-signal 절대 보호

이사회, 감사위원회, 사외이사 등은 **IDF가 0에 가까워도** G_SIGNAL로 분류된다.
전문서(全文書)에 등장하기 때문에 IDF가 낮지만, 그것이 제거 근거가 되어서는 안 된다.

### 분류는 분석 전에 확정

token 분류를 완료한 후에야 Spearman 상관 분석을 실행한다.
상관계수를 보고 나서 분류를 바꾸면 결과를 사후에 정당화하는 것이다.

### AMBIGUOUS 처리 원칙

"제거보다 보존"이 원칙이다.
분류가 불확실하면 GENERIC이 아닌 AMBIGUOUS를 유지하고 수동 검토한다.

---

## 출력 파일 구조

```
data/04_preprocessed/
├── tokenized_exp_A.csv          (03_preprocess_experiment.py 생성)
├── tokenized_exp_B.csv
├── ...
├── token_audit_exp_A.csv        (token_audit.py 생성 — TF/DF/IDF)
├── token_taxonomy_exp_A.csv     (token_classifier.py 생성 — 5범주 분류)
├── ambiguous_review_exp_A.csv   (수동 검토 대상)
├── stopword_update_exp_A.py     (불용어 업데이트 제안)
└── PREPROCESSING_DECISIONS.md   (의사결정 기록 — 누적 append)
```
