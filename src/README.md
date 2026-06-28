# src — 수집·전처리·feature 모듈

파이프라인 각 단계를 구성하는 재사용 모듈. 실행 진입점은 [`scripts/`](../scripts), 최종 분석은 [`notebook/`](../notebook).

| 모듈 | 역할 |
|---|---|
| `dart_api.py` | DART OpenAPI 호출 (사업보고서 원문 수집) |
| `section_extractor.py` | 보고서 II / IV / VI 섹션 추출 |
| `passage_filter.py` | ESG 관련 패시지(단락) 추출 |
| `preprocessor.py` | 전처리 실험 설정 (형태소·정규화 옵션) |
| `chunked_tokenize.py` | 배치 토크나이저 (타임아웃 우회) |
| `token_classifier.py` | 토큰 5범주 자동 분류기 |
| `token_audit.py` · `apply_manual_taxonomy.py` | 토큰 분류 감사·수동 taxonomy 보정 |
| `feature_builder.py` | firm-year 단위 scalar feature 계산 (E/S/G 점수, 분량 등) |
| `kcgs_merge.py` | feature × KCGS 등급 병합 (식별자 체인 기준) |

> 회사명이 아니라 `stock_code → corp_code → rcept_no → fiscal_year` 식별자 체인으로 병합 ([`kcgs_merge.py`](kcgs_merge.py)).
