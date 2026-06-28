# scripts — 파이프라인 실행 단계

[`src/`](../src) 모듈을 순서대로 호출하는 실행 스크립트. 01→05 단계로 진행하며, 최종 통합 분석은 [`notebook/3조_분석노트북.ipynb`](../notebook/3조_분석노트북.ipynb).

| 스크립트 | 단계 |
|---|---|
| `01_collect.py` | DART 사업보고서 수집 |
| `02_extract_sections.py` | II / IV / VI 섹션 추출 |
| `03_preprocess_experiment.py` | 전처리 실험 (형태소·정규화 비교) |
| `04_evaluate_preprocessing.py` | 전처리 결과 평가 |
| `05_full_analysis.py` | feature 빌드 → 검증 → 회귀 전체 분석 |
| `collect_expanded.py` | 확장 표본(381 firm-year) 재수집 |

## 실행 전 준비

```bash
pip install -r ../requirements.txt
cp ../config.example.py ../config.py
export OPENDART_API_KEY=<발급받은 키>
```

> 원본 데이터·API 키는 저장소 미포함. 전수(381) 수집 검증 기록: [`research_log/recovery_N381/`](../research_log/recovery_N381).
