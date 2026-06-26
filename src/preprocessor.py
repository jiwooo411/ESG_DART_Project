# =============================================================================
# src/preprocessor.py — 전처리 실험 설정 모듈
# =============================================================================
#
# 설계 원칙:
#   1. G_SIGNAL 절대 보호  — KCGS G등급 핵심 신호는 어떤 설정에서도 제거 금지
#   2. Taxonomy 기반 BOILERPLATE_NOUNS — token_classifier.py 결과로 확정
#   3. 문장 수준 boilerplate 필터 (exp_E/F) — 토큰화 이전에 문단 단위 제거
#   4. 분석 baseline: exp_B (pre-registered, 2026-05-18)
#
# 실험 설계 요약:
#   exp_A: minimal stopwords  | remove_all  | no filter   — 투명성 기준선
#   exp_B: standard           | remove_all  | no filter   — pre-reg baseline ★
#   exp_C: minimal            | keep_qty    | no filter   — 수치 보존 효과
#   exp_D: extended           | remove_all  | no filter   — 과잉 제거 위험 실험
#   exp_E: extended           | remove_all  | sent-filter — boilerplate 감소 실험
#   exp_F: extended           | keep_qty    | sent-filter — 최적 설정 탐색
#
# → C:\projects\esg_dart\src\preprocessor.py 에 복사하여 사용
# =============================================================================

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# =============================================================================
# 1. SIGNAL/NOISE 분류 사전 (token_classifier.py 결과 반영)
# =============================================================================

# G_SIGNAL: KCGS G등급 핵심 평가 항목 — 어떤 설정에서도 제거 금지
# 근거: 이사회 독립성, 감사위원회 활동, 이해관계자 관리는 G 점수 직결
G_SIGNAL_PROTECT = {
    "이사", "감사", "이사회", "준법", "이해관계자",
    "사외이사", "감사위원회", "ESG위원회", "컴플라이언스",
    "위원회",          # G-domain 의결기구
    "지배구조",        # G 도메인 핵심 개념
    "투명성",          # G 평가 항목
    "내부통제",        # G 평가 항목
    "주주",            # G-domain 이해관계자
}

# ESG_SIGNAL: E/S 도메인 고특이성 토큰 — taxonomy에서 확정
ESG_SIGNAL_PRESERVE = {
    "온실가스", "탄소중립", "탄소", "탄소배출", "탄소발자국",
    "안전보건", "안전", "보건",
    "임직원", "고용", "다양성", "인권", "노동",
    "재생에너지", "태양광", "풍력", "수소",
    "폐기물", "오염", "생태계", "순환경제",
    "공급망", "협력사", "사회공헌", "지역사회",
    "배출량", "감축", "저감", "친환경",
    "기후변화", "기후",
}

# BOILERPLATE_NOUNS: taxonomy 자동 분류 + 수동 확정 결과
# 이 토큰들은 재무/법무 의무공시에 의해 구조적으로 나타남
# ESG 의사표현 의지와 무관 → 불용어 처리 (exp_E, exp_F)
BOILERPLATE_NOUNS = {
    # taxonomy BOILERPLATE 확정 (token_classifier.py 결과)
    "재무제표", "부채", "차입금", "자본금", "사채", "배당금",
    # 추가 재무 boilerplate (사업보고서 의무 기재 사항)
    "원리금", "특수관계인", "당기순이익", "이자비용", "충당금",
    "매출액", "손익", "부채비율", "회사채", "원가",
    "연결재무제표", "연결", "주석", "장부", "회계",
    # 법무/공시 boilerplate
    "정관", "의결권", "의결", "결의", "등기",
    "법인세", "상법", "공고", "위임",
}

# =============================================================================
# 2. 불용어 사전 (강도별)
# =============================================================================

STOPWORDS_MINIMAL = {
    "및", "또한", "이를", "통해", "위해", "관련", "대한", "등",
    "있다", "하다", "되다", "이다", "것", "수", "그",
}

STOPWORDS_STANDARD = STOPWORDS_MINIMAL | {
    "당사", "회사", "기업", "사업", "관련하여", "바탕으로",
    "해당", "경우", "현재", "기타", "다음", "이후", "이전",
    "아래", "위", "각각", "방법", "방식", "절차",
    "내용", "사항", "보고서", "기재", "작성",
}

# ⚠️ G_SIGNAL_PROTECT 토큰은 이 목록에 절대 포함 금지
STOPWORDS_EXTENDED = STOPWORDS_STANDARD | {
    "기준", "기간", "항목", "결과", "과정", "단계",
    "수준", "규모", "범위", "목적", "대상",
    "주요", "전반", "향후", "기존", "신규",
    "상황", "조건",
    "운영", "관리", "수행", "활용", "진행",
    "비용", "금액", "자산", "이익", "투자",
    "연도", "분기", "전기", "당기",
}


def _validate_no_gsignal_in_stopwords():
    """G_SIGNAL 보호 토큰이 불용어에 포함되지 않았는지 런타임 검증"""
    overlap = G_SIGNAL_PROTECT & STOPWORDS_EXTENDED
    if overlap:
        logger.warning(
            f"⚠️ G_SIGNAL 보호 토큰이 STOPWORDS_EXTENDED에 있음: {overlap}\n"
            "이 토큰들을 STOPWORDS_EXTENDED에서 즉시 제거하세요."
        )
    return overlap


# =============================================================================
# 2b. 공식 의존성 — data/stopwords_ko_esg.txt
# -----------------------------------------------------------------------------
# 03_minimal_analysis_example.md 에 다음과 같이 명시되어 있음:
#   "data/stopwords_ko_esg.txt 에 불용어 초안이 있습니다."
# 기존 파이프라인은 이 파일을 로드하지 않고 inline set 만 사용했음 (lineage gap).
# 이 함수는 파일이 있을 경우 명시적으로 합치고, 없을 경우 explicit warning 처리.
# Silent fix 금지 원칙에 따라 STOPWORDS_OFFICIAL 은 별도 set 으로 유지하고
# exp_F_official 에서만 활성화한다 (기존 exp_B/E/F lineage 보존).
# =============================================================================
from pathlib import Path

def load_official_stopwords(path: Optional[Path] = None) -> set:
    """공식 의존성 stopwords_ko_esg.txt 를 로드.
    - 파일 부재 시: warning + empty set (G_SIGNAL 충돌 차단)
    - 로드 후 G_SIGNAL_PROTECT / ESG_SIGNAL_PRESERVE 와 충돌하는 토큰 자동 제거
    """
    if path is None:
        # repo-relative default: <repo_root>/data/stopwords_ko_esg.txt
        path = Path(__file__).resolve().parents[1] / "data" / "stopwords_ko_esg.txt"
    path = Path(path)
    if not path.exists():
        logger.warning(
            f"⚠️ 공식 의존성 누락: {path} 가 존재하지 않습니다. "
            "STOPWORDS_OFFICIAL = ∅ 로 처리합니다. (preprocessing reproducibility risk)"
        )
        return set()
    raw = {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}
    # G_SIGNAL / ESG_SIGNAL 보호 토큰과 충돌 방지
    conflicts = (G_SIGNAL_PROTECT | ESG_SIGNAL_PRESERVE) & raw
    if conflicts:
        logger.warning(
            f"⚠️ 공식 stopwords 와 SIGNAL 보호 토큰이 충돌 — 제거합니다: {conflicts}"
        )
    cleaned = raw - G_SIGNAL_PROTECT - ESG_SIGNAL_PRESERVE
    logger.info(f"공식 stopwords 로드: {len(cleaned)} tokens (원본 {len(raw)}, 충돌 {len(conflicts)})")
    return cleaned

# 모듈 로드 시 한 번 캐싱 (재로드 비용 회피)
try:
    STOPWORDS_OFFICIAL = load_official_stopwords()
except Exception as _e:  # pragma: no cover
    logger.error(f"공식 stopwords 로드 실패: {_e}")
    STOPWORDS_OFFICIAL = set()

# 공식 합본 — exp_F_official 전용 (silent merge 금지: 별도 변종으로만 노출)
STOPWORDS_EXTENDED_PLUS_OFFICIAL = STOPWORDS_EXTENDED | STOPWORDS_OFFICIAL


# =============================================================================
# 3. Boilerplate 문장 필터 (exp_E, exp_F — 토큰화 이전 적용)
# =============================================================================

BOILERPLATE_SENTENCE_PATTERNS = [
    # 재무제표 관련 공시
    r"연결재무제표.*주석",
    r"재무제표.*주석",
    r"당기순이익.*전기.*비교",
    r"부채비율.*산출",
    r"자본금.*납입",
    # 주주총회/의결 관련 의무공시
    r"정기주주총회.*결의에.*의거",
    r"주주총회.*결의",
    r"원리금.*지급",
    r"이자.*지급",
    # 특수관계인 거래 공시
    r"특수관계인.*거래",
    r"특수관계인.*내역",
    # 감사 관련 의무공시 (ESG 감사와 구분)
    r"감사보고서.*첨부",
    r"외부감사인.*의견",
    # 법적 공시 boilerplate
    r"법인세.*납부",
    r"공시.*의무",
    r"기재.*사항.*없음",
    r"해당사항.*없음",
    r"별도의.*공시",
]

_compiled_patterns = [re.compile(p) for p in BOILERPLATE_SENTENCE_PATTERNS]


def filter_boilerplate_sentences(text: str,
                                  log_removed: bool = True) -> tuple:
    """
    토큰화 이전에 재무/법무 boilerplate 문단을 제거한다.

    Returns: (cleaned_text, removed_lines)

    중요: 제거된 줄 목록을 반드시 육안 검증할 것.
          "ESG 감사" vs "회계감사보고서 첨부" 구분이 패턴에 따라 달라진다.
    """
    lines = text.split("\n")
    kept = []
    removed = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue

        is_boilerplate = any(p.search(stripped) for p in _compiled_patterns)
        if is_boilerplate:
            removed.append(stripped)
            if log_removed:
                logger.debug(f"[BOILERPLATE 제거] {stripped[:80]}")
        else:
            kept.append(line)

    return "\n".join(kept), removed


# =============================================================================
# 4. 숫자 처리 모드
# =============================================================================

def apply_number_mode(text: str, mode: str) -> str:
    """
    mode 옵션:
        "remove_all"    : 모든 숫자 제거
        "keep_quantity" : "[NUM]단위" 패턴 보존 (ESG 정량 표현 유지)
    """
    if mode == "remove_all":
        return re.sub(r"\d+", " ", text)
    elif mode == "keep_quantity":
        text = re.sub(r"\d+(\.\d+)?\s*(억원|만원|원|%|퍼센트|톤|tCO2|GWh|MW|kWh)",
                      r"[NUM]\2", text)
        text = re.sub(r"\d+", " ", text)
        return text
    else:
        return text


# =============================================================================
# 5. 회사명 제거
# =============================================================================

def remove_company_names(text: str, company_names: list) -> str:
    for name in company_names:
        variants = [name, f"(주){name}", f"{name}(주)", f"㈜{name}", f"주식회사 {name}"]
        for v in variants:
            text = text.replace(v, "")
    return text


# =============================================================================
# 6. 형태소 분석기 초기화
# =============================================================================

def get_tagger(name: str):
    """
    Decision: Kiwi (기본) → Okt (fallback)
    Kiwi는 복합어 분리가 정확하고 속도가 빠름.
    """
    name_lower = name.lower()
    if name_lower == "kiwi":
        try:
            from kiwipiepy import Kiwi
            tagger = Kiwi()
            logger.info("Kiwi 초기화 완료")
            return tagger
        except ImportError:
            logger.warning("Kiwi 없음 → Okt fallback")
    if name_lower in ("okt", "kiwi"):
        try:
            from konlpy.tag import Okt
            tagger = Okt()
            logger.info("Okt 초기화 완료")
            return tagger
        except ImportError:
            raise ImportError("pip install konlpy 또는 pip install kiwipiepy 필요")
    raise ValueError(f"지원하지 않는 분석기: {name}")


# =============================================================================
# 7. 토큰화
# =============================================================================

def tokenize(text: str,
             tagger,
             pos_filter: list = None,
             stopwords: set = None,
             extra_stopword_nouns: set = None) -> list:
    """
    형태소 분석 후 명사 토큰 리스트 반환.
    G_SIGNAL_PROTECT는 extra_stopword_nouns에 있어도 제거하지 않음.
    """
    if pos_filter is None:
        pos_filter = ['Noun', 'NNG', 'NNP']
    if stopwords is None:
        stopwords = set()
    if extra_stopword_nouns is None:
        extra_stopword_nouns = set()

    # G_SIGNAL 보호: 어떤 불용어 집합에서도 제외
    all_stopwords = (stopwords | extra_stopword_nouns) - G_SIGNAL_PROTECT

    try:
        if hasattr(tagger, "tokenize"):  # Kiwi
            tokens_raw = tagger.tokenize(text)
            tokens = [
                t.form for t in tokens_raw
                if t.tag.startswith("NN")
                and t.form not in all_stopwords
                and len(t.form) > 1
            ]
        else:  # Okt
            tagged = tagger.pos(text)
            tokens = [
                word for word, pos in tagged
                if pos in pos_filter
                and word not in all_stopwords
                and len(word) > 1
            ]
    except Exception as e:
        logger.error(f"토큰화 오류: {e}")
        tokens = []

    return tokens


# =============================================================================
# 8. 문서 전처리 메인 함수
# =============================================================================

def preprocess_document(text: str,
                         config: dict,
                         tagger,
                         company_names: list = None) -> dict:
    """
    단일 firm-year 문서에 전처리 파이프라인 적용.

    파이프라인 순서:
        1. 회사명 제거
        2. 숫자 처리
        3. [exp_E/F] Boilerplate 문장 필터 (사전 토큰화)
        4. 형태소 분석 + 불용어 제거
        5. [exp_E/F] BOILERPLATE_NOUNS 추가 불용어

    Returns:
        { "tokens", "token_count", "joined_text", "removed_sentences" }
    """
    if company_names and config.get("remove_company_names", False):
        text = remove_company_names(text, company_names)

    text = apply_number_mode(text, config.get("number_mode", "remove_all"))

    removed_sentences = []
    if config.get("boilerplate_sentence_filter", False):
        text, removed_sentences = filter_boilerplate_sentences(
            text, log_removed=config.get("log_removed_sentences", False)
        )

    strength = config.get("stopword_strength", "standard")
    sw = get_stopword_set(strength)

    extra = BOILERPLATE_NOUNS if config.get("use_boilerplate_nouns", False) else set()

    tokens = tokenize(text, tagger=tagger, stopwords=sw, extra_stopword_nouns=extra)

    return {
        "tokens":              tokens,
        "token_count":         len(tokens),
        "joined_text":         " ".join(tokens),
        "removed_sentences":   removed_sentences,
    }


# =============================================================================
# 9. 실험 설정 사전
# =============================================================================

EXPERIMENT_CONFIGS = {

    "exp_A": {
        "description":              "minimal stopwords | remove_all | no filter | 투명성 기준선",
        "tagger_name":              "kiwi",
        "stopword_strength":        "minimal",
        "number_mode":              "remove_all",
        "remove_company_names":     False,
        "boilerplate_sentence_filter": False,
        "use_boilerplate_nouns":    False,
        "passage_min_seeds":        1,
        "log_removed_sentences":    False,
    },


    "exp_B": {
        "description":              "standard stopwords | remove_all | no filter | PRE-REG BASELINE ★",
        "tagger_name":              "kiwi",
        "stopword_strength":        "standard",
        "number_mode":              "remove_all",
        "remove_company_names":     False,
        "boilerplate_sentence_filter": False,
        "use_boilerplate_nouns":    False,
        "passage_min_seeds":        1,
        "log_removed_sentences":    False,
    },

    "exp_C": {
        "description":              "minimal stopwords | keep_quantity | no filter | 수치보존",
        "tagger_name":              "kiwi",
        "stopword_strength":        "minimal",
        "number_mode":              "keep_quantity",
        "remove_company_names":     True,
        "boilerplate_sentence_filter": False,
        "use_boilerplate_nouns":    False,
        "passage_min_seeds":        1,
        "log_removed_sentences":    False,
    },

    "exp_D": {
        "description":              "extended stopwords | remove_all | no filter | G-signal 위험",
        "tagger_name":              "kiwi",
        "stopword_strength":        "extended",
        "number_mode":              "remove_all",
        "remove_company_names":     True,
        "boilerplate_sentence_filter": False,
        "use_boilerplate_nouns":    False,
        "passage_min_seeds":        1,
        "log_removed_sentences":    False,
    },

    "exp_E": {
        "description":              "extended stopwords | remove_all | sentence filter | BOILERPLATE 감소",
        "tagger_name":              "kiwi",
        "stopword_strength":        "extended",
        "number_mode":              "remove_all",
        "remove_company_names":     True,
        "boilerplate_sentence_filter": True,
        "use_boilerplate_nouns":    True,
        "passage_min_seeds":        1,
        "log_removed_sentences":    True,
    },

    "exp_F": {
        "description":              "extended stopwords | keep_quantity | sentence filter | 최적설정탐색",
        "tagger_name":              "kiwi",
        "stopword_strength":        "extended",
        "number_mode":              "keep_quantity",
        "remove_company_names":     True,
        "boilerplate_sentence_filter": True,
        "use_boilerplate_nouns":    True,
        "passage_min_seeds":        1,
        "log_removed_sentences":    True,
    },

    # exp_F_official: exp_F + 공식 stopwords_ko_esg.txt 합본 (lineage recovery, 2026-05-24)
    "exp_F_official": {
        "description":              "exp_F + official stopwords_ko_esg.txt | preprocessing recovery",
        "tagger_name":              "kiwi",
        "stopword_strength":        "extended_plus_official",
        "number_mode":              "keep_quantity",
        "remove_company_names":     True,
        "boilerplate_sentence_filter": True,
        "use_boilerplate_nouns":    True,
        "passage_min_seeds":        1,
        "log_removed_sentences":    True,
    },
}


# stopword_strength → set 매핑 헬퍼 (exp_F_official 지원)
def get_stopword_set(strength: str) -> set:
    """strength 문자열을 stopword set 으로 매핑.
    - 'minimal' / 'standard' / 'extended': inline set
    - 'extended_plus_official': inline extended ∪ 공식 stopwords_ko_esg.txt
    """
    mapping = {
        "minimal": STOPWORDS_MINIMAL,
        "standard": STOPWORDS_STANDARD,
        "extended": STOPWORDS_EXTENDED,
        "extended_plus_official": STOPWORDS_EXTENDED_PLUS_OFFICIAL,
    }
    if strength not in mapping:
        raise ValueError(f"Unknown stopword_strength={strength!r}")
    return mapping[strength]


# 모듈 임포트 시 G_SIGNAL 안전 검증
_validate_no_gsignal_in_stopwords()
