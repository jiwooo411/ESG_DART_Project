# =============================================================================
# config.example.py — 프로젝트 전역 설정 템플릿
# =============================================================================
# 실제 사용 시 이 파일을 config.py로 복사하고 OPENDART_API_KEY 환경변수를 설정한다.
# API 키를 이 파일에 직접 쓰지 말 것. config.py는 .gitignore에 포함되어 있다.

import os

# =============================================================================
# 1. DART API 키 — 환경변수에서만 읽음 (하드코딩 금지)
# =============================================================================
# https://opendart.fss.or.kr 에서 발급
DART_API_KEY = os.environ["OPENDART_API_KEY"]  # 미설정 시 즉시 에러 (조용한 실패 방지)

# =============================================================================
# 2. 수집 대상 설정
# =============================================================================
# fiscal_year: 분석 대상 사업연도 (최종 분석 = 2022, 2023, 2024)
# esg_year:    KCGS ESG 등급 기준 연도 (가이드 정의 = fiscal_year + 1)
# 참고: company_master.csv의 esg_year 컬럼은 현재 fiscal_year와 동일하게 라벨링되어
#       있어 가이드 정의와 한 해 어긋날 수 있음 — data/README.md 한계 항목 참조

FISCAL_YEARS = [2022, 2023, 2024]

BGN_MONTH = "01"
END_MONTH = "06"

# =============================================================================
# 3. 경로 설정
# =============================================================================
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")

RAW_DIR      = os.path.join(DATA_DIR, "01_raw")
SECTION_DIR  = os.path.join(DATA_DIR, "02_sections")
PASSAGE_DIR  = os.path.join(DATA_DIR, "03_passages")
PREPROC_DIR  = os.path.join(DATA_DIR, "04_preprocessed")
ZIP_CACHE    = os.path.join(DATA_DIR, "zip_cache")

CORP_CODE_MAP_PATH      = os.path.join(RAW_DIR, "corp_code_map.csv")
COLLECTED_PATH          = os.path.join(RAW_DIR, "collected_reports.csv")
FAILED_COLLECT_PATH     = os.path.join(RAW_DIR, "failed_logs.csv")
EXTRACTED_SECTION_PATH  = os.path.join(SECTION_DIR, "extracted_sections.csv")
SECTION_FAILED_PATH     = os.path.join(SECTION_DIR, "section_failed_logs.csv")
ESG_PASSAGES_PATH       = os.path.join(PASSAGE_DIR, "esg_passages.csv")
FIRM_YEAR_DOC_PATH      = os.path.join(PASSAGE_DIR, "firm_year_documents.csv")

# =============================================================================
# 4. 분석 대상 섹션
# =============================================================================
# 왜 II / IV / VI 인가:
#   II  - 사업의 내용: ESG 전략, 환경 리스크, 제품 안전 등 등장
#   IV  - 이사의 경영진단: 경영진이 직접 ESG 언어를 사용하는 핵심 구간
#   VI  - 이사회 기관: 지배구조(G) 정보의 주요 출처
TARGET_SECTIONS = ["II", "IV", "VI"]

# =============================================================================
# 5. ESG Seed 단어 (seed_dictionary.csv가 최종 출처 — 아래는 초기 버전 참고용)
# =============================================================================
ESG_SEED_WORDS = {
    "E": [
        "탄소", "온실가스", "환경", "기후변화", "기후", "에너지",
        "재생에너지", "탄소중립", "배출", "오염", "생태계", "녹색",
        "친환경", "탄소배출", "탄소발자국", "순환경제"
    ],
    "S": [
        "안전보건", "인권", "다양성", "지역사회", "임직원", "공급망",
        "사회적", "노동", "복지", "상생", "협력사", "산업재해",
        "사회공헌", "포용", "차별금지"
    ],
    "G": [
        "이사회", "지배구조", "투명성", "윤리", "준법", "내부통제",
        "감사", "주주", "공시", "ESG위원회", "이해관계자", "컴플라이언스"
    ]
}

ALL_SEEDS = [w for words in ESG_SEED_WORDS.values() for w in words]

# =============================================================================
# 6. API 요청 설정
# =============================================================================
REQUEST_DELAY   = 0.5
MAX_RETRIES     = 3
REQUEST_TIMEOUT = 30
