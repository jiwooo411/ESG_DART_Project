# =============================================================================
# src/passage_filter.py — ESG 패시지 추출 모듈
# =============================================================================
# 이 모듈이 하는 일:
#   섹션 텍스트를 문단 단위로 분리한 뒤,
#   ESG seed 단어가 포함된 문단만 골라 "ESG 패시지"로 반환한다.
#
# 왜 문단(paragraph) 단위인가:
#   단어 단위 추출은 문맥을 잃는다.
#   예) "환경"이 "영업환경" vs. "환경오염" 맥락에서 쓰이는 것을
#       문단 단위로 봐야 구분할 수 있다.
#   문단 단위는 TF-IDF / BERT 입력에도 더 적합한 크기다.

import re
import logging
from typing import Optional

# ============================================================
# PATCH: Sentence-level ESG density filter
# 추가 위치: split_into_paragraphs() 함수 바로 위
# ============================================================

# G-signal 문장 보호 목록 (sentence filter에서 절대 제거 금지)
_G_SENTENCE_SIGNALS = {
    "이사", "감사", "이사회", "준법", "이해관계자",
    "사외이사", "감사위원회", "위원회", "지배구조",
    "내부통제", "컴플라이언스",
}

def _split_korean_sentences(text: str) -> list[str]:
    """
    한국어 사업보고서 문장 분리 (근사치).
    완벽한 분리보다 보수적 분리가 목표:
    분리 실패 시 문장 전체가 보존되므로 false negative 위험이 낮음.
    """
    # 한국어 종결어미 패턴: "~습니다.", "~합니다.", "~다." 등
    parts = re.split(r'(?<=[다]\.)\s+(?=[가-힣A-Za-z(])', text)
    return [s.strip() for s in parts if len(s.strip()) >= 15]


def sentence_density_filter(paragraph: str,
                              seed_words: list[str],
                              context_window: int = 1) -> str:
    """
    문단 내에서 ESG/G seed가 있는 문장과 그 ±context_window 문장만 유지.

    보존 규칙 (보수적):
        Rule 1: G_SIGNAL 포함 문장 → 절대 보존 (false negative 방지)
        Rule 2: ESG seed 포함 문장 → 보존
        Rule 3: 보존된 문장의 ±context_window 문장 → 맥락 보존
        Rule 4: 아무것도 보존 안 되면 → 원본 문단 전체 반환

    왜 context_window=1인가:
        "지속가능경영을 위해 이사회가 다음을 결의하였습니다."
        "[결의 내용 문장]"  ← seed 없지만 맥락상 ESG 내용
        위 패턴에서 결의 내용이 잘리는 것을 방지.

    왜 generic threshold를 쓰지 않는가:
        threshold 파라미터는 또 다른 tuneable variable이 된다.
        현재 단계에서는 "ESG/G 있으면 보존"이 더 안전하고 단순하다.
    """
    sentences = _split_korean_sentences(paragraph)

    # 문장이 1개 이하면 분리 실패로 간주 → 원본 반환
    if len(sentences) <= 1:
        return paragraph

    keep = [False] * len(sentences)

    for i, sent in enumerate(sentences):
        has_g   = any(g in sent for g in _G_SENTENCE_SIGNALS)
        has_esg = any(seed in sent for seed in seed_words)

        if has_g or has_esg:
            # 해당 문장 + context_window 범위 보존
            for j in range(max(0, i - context_window),
                           min(len(sentences), i + context_window + 1)):
                keep[j] = True

    # 아무것도 보존 안 됐으면 원본 반환 (안전장치)
    if not any(keep):
        return paragraph

    kept_sentences = [s for s, k in zip(sentences, keep) if k]
    removed_n = sum(1 for k in keep if not k)

    if removed_n > 0:
        logger.debug(
            f"[sentence filter] {len(sentences)}문장 → {len(kept_sentences)}문장 "
            f"(제거 {removed_n}개)"
        )
    return " ".join(kept_sentences)

logger = logging.getLogger(__name__)

# PATCH: Boilerplate density filter용 분류 상수
# G-signal이 있으면 무조건 통과 (false negative 방지 최우선)
_G_SIGNAL_WORDS = {
    "이사", "감사", "이사회", "준법", "이해관계자",
    "사외이사", "감사위원회", "위원회", "지배구조",
    "내부통제", "컴플라이언스",
}
_BOILERPLATE_WORDS = {
    "재무제표", "부채", "차입금", "자본금", "사채", "배당금",
    "원리금", "특수관계인", "당기순이익", "이자비용", "충당금",
    "연결재무제표", "주석", "정관", "의결권", "결의",
    "법인세", "회사채", "장부",
}
_ESG_SIGNAL_WORDS = {
    "온실가스", "탄소중립", "탄소", "안전보건", "임직원",
    "재생에너지", "태양광", "풍력", "폐기물", "공급망",
    "배출량", "감축", "저감", "기후변화",
}

# =============================================================================
# 1. 텍스트 → 문단 분리
# =============================================================================

def split_into_paragraphs(text: str,
                           min_length: int = 30,
                           max_length: int = 2000) -> list[str]:
    """
    텍스트를 문단 단위로 분리한다.

    왜 줄바꿈 기준으로 분리하는가:
        DART 보고서는 XML에서 추출 후 이미 줄바꿈으로 문단이 구분된다.
        문장 단위(sentence tokenization)는 너무 세밀해 문맥이 손실됨.

    min_length: 너무 짧은 단편 텍스트(표 제목, 숫자만 있는 행 등) 제거
    max_length: 하나의 거대 문단이 되는 것을 방지 (필요시 분할)

    Decision — 줄바꿈 기준 vs. 마침표 기준:
        → 줄바꿈 기준 선택.
        → 한계: 줄바꿈 없이 이어진 문장들은 하나의 거대 문단이 됨.
              이 경우 max_length로 잘라내는 것이 현실적 대안.
    """
    paragraphs = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) < min_length:
            continue  # 너무 짧은 줄 제거
        if len(line) > max_length:
            # 너무 긴 경우: 200자씩 분할
            for i in range(0, len(line), max_length):
                chunk = line[i:i + max_length].strip()
                if len(chunk) >= min_length:
                    paragraphs.append(chunk)
        else:
            paragraphs.append(line)
    return paragraphs


# =============================================================================
# 2. ESG 패시지 필터링
# =============================================================================

def filter_esg_passages(paragraphs: list[str],
                         seed_words: list[str],
                         min_seed_count: int = 1) -> list[dict]:
    """
    ESG seed 단어가 min_seed_count개 이상 포함된 문단만 반환.

    왜 min_seed_count 파라미터가 있는가:
        팀 비교 실험의 핵심 변수 중 하나.
        - min_seed_count=1: 느슨한 필터 → coverage 높지만 noise 위험
        - min_seed_count=2: 엄격한 필터 → precision 높지만 일부 firm-year에서 패시지 0

        두 설정 모두 저장해 sensitivity analysis를 가능하게 한다.

    반환 형식:
        [{"paragraph_id": int, "text": str, "seed_count": int,
          "matched_seeds": list[str], "esg_category": str}, ...]
    """
    results = []
    for i, para in enumerate(paragraphs):
        matched = [seed for seed in seed_words if seed in para]
        if len(matched) >= min_seed_count:
            # ESG 카테고리 판별 (E/S/G 중 가장 많이 매칭된 카테고리)
            category = _identify_esg_category(matched)
            results.append({
                "paragraph_id": i,
                "text": para,
                "seed_count": len(matched),
                "matched_seeds": matched,
                "esg_category": category,
            })
    return results


def _identify_esg_category(matched_seeds: list[str]) -> str:
    """
    매칭된 seed 단어들이 E/S/G 중 어느 카테고리에 해당하는지 판별.
    복수 카테고리에 걸치면 "ESG"로 표기.

    이 함수의 목적:
        나중에 E/S/G 각 카테고리별 TF-IDF 피처를 분리하거나,
        어떤 카테고리의 언어가 KCGS 등급과 더 상관되는지 분석할 수 있게 한다.
    """
    from config import ESG_SEED_WORDS
    categories = set()
    for seed in matched_seeds:
        for cat, words in ESG_SEED_WORDS.items():
            if seed in words:
                categories.add(cat)
    if len(categories) == 1:
        return list(categories)[0]
    return "ESG"  # 복수 카테고리


# =============================================================================
# 3. firm-year document 생성
# =============================================================================

# PATCH: Boilerplate density filter
def _has_g_signal(text: str) -> bool:
    return any(w in text for w in _G_SIGNAL_WORDS)

def _boilerplate_ratio(text: str) -> float:
    """문단 내 boilerplate 단어 비율 (어절 기준 근사치)."""
    words = text.split()
    if not words:
        return 0.0
    bp_count = sum(1 for w in words if any(b in w for b in _BOILERPLATE_WORDS))
    return bp_count / len(words)

def density_filter_passages(passages: list[dict],
                             bp_ratio_threshold: float = 0.25) -> list[dict]:
    """
    Boilerplate-heavy 문단을 제거한다. G_SIGNAL 문단은 절대 제거하지 않는다.

    보수적 설계 원칙:
        1. G_SIGNAL이 있으면 무조건 통과 — false negative 방지 최우선
        2. bp_ratio_threshold = 0.25 (보수적): 문단 어절의 25% 이상이
           boilerplate 단어일 때만 제거
        3. ESG_SIGNAL이 있으면 통과 — 재무 boilerplate와 ESG 언어가 공존하면 보존

    Decision Box:
        Alternative: 더 낮은 임계값(0.15) → 더 많이 제거, G-signal 위험 증가
        Choice: 0.25 (보수적) — G-signal 포함 문단을 false negative로 잃는 것이
                boilerplate retention보다 훨씬 위험하다.
        Limitation: 재무 boilerplate와 ESG 언어가 같은 문단에 있으면 보존됨.
                    (이것은 의도적 설계 — 억측보다 보존이 낫다.)
    """
    kept = []
    removed_count = 0
    for p in passages:
        text = p["text"]
        # Rule 1: G_SIGNAL 있으면 무조건 통과
        if _has_g_signal(text):
            kept.append(p)
            continue
        # Rule 2: ESG_SIGNAL 있으면 통과
        if any(w in text for w in _ESG_SIGNAL_WORDS):
            kept.append(p)
            continue
        # Rule 3: boilerplate ratio가 임계값 이하면 통과
        if _boilerplate_ratio(text) <= bp_ratio_threshold:
            kept.append(p)
        else:
            removed_count += 1
            logger.debug(f"[BP 제거] {text[:60]}...")

    logger.info(f"  density filter: {len(passages)}개 → {len(kept)}개 "
                f"(제거 {removed_count}개)")
    return kept

def build_firm_year_document(passages: list[dict]) -> str:
    """
    한 기업의 한 연도 ESG 패시지들을 하나의 텍스트로 병합.

    이것이 최종 분석 단위다:
        stock_code × fiscal_year → 하나의 텍스트 덩어리
        이 텍스트에서 TF-IDF 피처를 계산한다.

    왜 단순 이어붙이기인가:
        순서 정보(문단 순서)를 TF-IDF는 사용하지 않으므로
        단순 concatenation으로 충분하다.
        BERT를 쓴다면 [SEP] 토큰으로 구분하거나 독립 입력을 고려.
    """
    return "\n\n".join(p["text"] for p in passages)


# =============================================================================
# 4. 편의 함수: 섹션 텍스트 → ESG 패시지 (원스텝)
# =============================================================================

def section_to_passages(
    section_text: str,
    seed_words: list[str],
    min_seed_count: int = 1,
    section_name: str = "",
    use_density_filter: bool = False,    # exp_E/F: paragraph-level boilerplate filter
    use_sentence_filter: bool = False,   # exp_E/F: sentence-level density filter
    bp_ratio_threshold: float = 0.25,
    collect_sentence_scores: bool = False,  # True면 scored_sentences도 반환
) -> list[dict]:
    """
    섹션 텍스트 → 문단 분리 → (선택) 문장 필터 → ESG 패시지 추출.

    collect_sentence_scores=True이면 각 passage dict에
    "scored_sentences" 키가 추가됨 (aggregate_passage_features() 입력용).
    """
    # 1. 문단 분리
    paragraphs = split_into_paragraphs(section_text)

    # 2. 문장 단위 density filter (exp_E/F 전용)
    all_scored: list[list[dict]] = []  # paragraph별 scored sentences
    if use_sentence_filter:
        filtered_paragraphs = []
        for para in paragraphs:
            filtered_text, scored = sentence_density_filter(para, seed_words)
            filtered_paragraphs.append(filtered_text)
            all_scored.append(scored)
        paragraphs = [p for p in filtered_paragraphs if len(p) >= 20]

    # 3. ESG seed 기반 패시지 추출
    passages = filter_esg_passages(paragraphs, seed_words, min_seed_count)

    # 4. paragraph-level boilerplate filter (exp_E/F 선택)
    if use_density_filter and passages:
        passages = density_filter_passages(passages, bp_ratio_threshold)

    # 5. sentence scores를 passage에 첨부 (피처 계산용)
    if collect_sentence_scores and all_scored:
        for p in passages:
            pid = p["paragraph_id"]
            if pid < len(all_scored):
                p["scored_sentences"] = all_scored[pid]

    # 6. 섹션 정보 추가 + 로깅
    for p in passages:
        p["section"] = section_name

    logger.info(
        f"  섹션 {section_name}: 문단 {len(paragraphs)}개 → "
        f"ESG 패시지 {len(passages)}개 (min_seed={min_seed_count})"
    )
    return passages

# =============================================================================
# 5. 문장 단위 Semantic Density Scoring
# =============================================================================
# 목적: 문단을 문장으로 쪼개 각 문장의 ESG/G/generic/finance 밀도를 점수화.
#
# 왜 single score가 아닌 dict인가:
#   - esg_density → 보존/제거 기준 (filtering)
#   - generic_density → cheap-talk proxy (피처 생성)
#   - is_g_protected → 절대 보존 플래그 (삭제 금지)
#   세 차원을 하나의 숫자로 압축하면 해석 불가능해진다.
#
# 왜 hard threshold 제거가 아닌 scoring인가:
#   generic 문장은 noise가 아닐 수 있다.
#   "ESG 표현 옆에 붙은 일반 경영 언어" 자체가 cheap-talk의 언어적 패턴.
#   score를 보존해두어야 나중에 cheap-talk 피처로 활용 가능.

# Generic rhetoric tokens — 이것들은 stopword/BOILERPLATE로 처리하지 말 것.
# 주주/가치/경영은 context에 따라 G-domain이 될 수 있음.
# 여기서는 "ESG seed 없이 이것만 있을 때" generic으로 분류하는 용도로만 사용.
# _GENERIC_RHETORIC_SIGNALS 전체 삭제.
# 이유: 자의적 선험 분류는 measurement validity 취약점.
#       generic rhetoric 측정은 feature_builder.py에서
#       TF-IDF concentration으로 처리한다.


def _split_korean_sentences(text: str) -> list[str]:
    """
    한국어 문장 분리 (경량 버전).

    분리 기준:
        1. [다/요/임/음/함/됨/됩니다/습니다] + 마침표 + 공백
        2. 단, 너무 짧은 조각(< 15자)은 앞 문장에 병합

    한계:
        - 열거형("첫째, ..., 둘째, ...") 구조는 잘못 분리될 수 있음
        - 숫자+단위("3.5%") 패턴에서 오분리 가능
        → 이 경우 문장이 원래보다 짧아지므로 scoring에서 낮게 평가될 뿐,
          G_SIGNAL이 있으면 어차피 보존됨.
    """
    # 마침표/물음표/느낌표 뒤 공백+대문자(한글 또는 영문) 기준 분리
    pattern = r'(?<=[다요임음함됨])\.\s+(?=[가-힣A-Za-z(①②③])'
    parts = re.split(pattern, text)

    result = []
    buffer = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if buffer and len(part) < 15:
            buffer = buffer + " " + part  # 짧은 조각 병합
        else:
            if buffer:
                result.append(buffer)
            buffer = part
    if buffer:
        result.append(buffer)

    return result if result else [text]


def sentence_density_filter(
    paragraph: str,
    seed_words: list[str],
    context_window: int = 1,
    min_signal_density: float = 0.0,
) -> tuple[str, list[dict]]:
    """
    문단을 문장으로 분리해 ESG/G density가 낮은 문장을 보수적으로 제거.
    모든 sentence_score dict를 함께 반환해 cheap-talk 피처 계산에 활용.

    Parameters
    ----------
    min_signal_density:
        0.0 = binary mode (esg_hit > 0 or g_hit > 0이면 보존)
        0.0 초과 = 최소 density 임계값 (권장: 0.5 이하, 보수적으로)

    반환: (필터링된_문단_텍스트, [sentence_score dict 리스트])
        → 텍스트는 파이프라인에 사용, score list는 피처 계산에 사용

    보수적 설계 원칙:
        1. is_g_protected == True → 무조건 보존 (절대 룰)
        2. esg_hit > 0 or g_hit > 0 → 보존
        3. context_window: 보존 문장의 ±1 문장도 보존 (맥락 유지)
        4. 아무것도 보존되지 않으면 → 원본 반환 (safety net)
    """
    sentences = _split_korean_sentences(paragraph)
    if len(sentences) <= 1:
        # 분리 불가 → 원본 반환, score는 전체 문단에 대해 계산
        score = sentence_score(paragraph, seed_words)
        return paragraph, [score]

    scores = [sentence_score(s, seed_words) for s in sentences]

    # 보존 대상 플래그
    keep = [False] * len(sentences)
    for i, sc in enumerate(scores):
        # Rule 1: G_SIGNAL absolute protection
        if sc["is_g_protected"]:
            keep[i] = True
        # Rule 2: ESG 신호 있음
        elif sc["esg_hit"] > 0 or sc["g_hit"] > 0:
            if sc["signal_density"] >= min_signal_density:
                keep[i] = True

    # context_window 확장
    base_keep = keep[:]
    for i, k in enumerate(base_keep):
        if k:
            for j in range(max(0, i - context_window),
                           min(len(sentences), i + context_window + 1)):
                keep[j] = True

    # safety net: 아무것도 안 남으면 원본 반환
    if not any(keep):
        return paragraph, scores

    filtered_text = " ".join(s for s, k in zip(sentences, keep) if k)
    kept_scores   = [sc for sc, k in zip(scores, keep) if k]
    return filtered_text, kept_scores

# =============================================================================
# 6. Passage → firm-year 피처 집계 (cheap-talk proxy 포함)
# =============================================================================

def aggregate_passage_features(
    scored_sentences: list[dict],
) -> dict:
    """
    sentence_score dict 리스트에서 firm-year level scalar 피처를 계산.

    이 함수의 연구적 의미:
        단순 token count 피처(exp_B TF-IDF)와 달리,
        이 피처들은 "ESG 언어가 얼마나 밀도 있게, 일관되게 사용되는가"를 측정.

        cheap-talk 가설 하에서:
            mean_esg_density 낮음 + mean_generic_density 높음
            = ESG 표현이 일반 경영 언어로 희석되어 있음 = cheap-talk 패턴

    반환 피처:
        n_sentences          : 전체 문장 수
        n_g_protected        : G_SIGNAL 포함 문장 수
        n_esg_hit            : ESG seed 포함 문장 수
        mean_esg_density     : ESG seed per-100자 평균 (핵심 피처)
        mean_signal_density  : (ESG+G) per-100자 평균
        mean_generic_density : generic rhetoric per-100자 평균 (cheap-talk proxy)
        mean_finance_density : finance boilerplate per-100자 평균
        esg_to_generic_ratio : mean_esg_density / max(mean_generic_density, 0.001)
                               → 높을수록 generic 대비 ESG가 밀도 있음
        generic_rhetoric_ratio: n_generic_dominant / n_sentences
                               → generic만 있고 ESG 없는 문장 비율 (cheap-talk proxy)
    """
    if not scored_sentences:
        return {k: None for k in [
            "n_sentences", "n_g_protected", "n_esg_hit",
            "mean_esg_density", "mean_signal_density",
            "mean_generic_density", "mean_finance_density",
            "esg_to_generic_ratio", "generic_rhetoric_ratio",
        ]}

    n = len(scored_sentences)
    n_g  = sum(1 for sc in scored_sentences if sc["is_g_protected"])
    n_esg = sum(1 for sc in scored_sentences if sc["esg_hit"] > 0)

    mean_esg = sum(sc["esg_density"]     for sc in scored_sentences) / n
    mean_sig = sum(sc["signal_density"]  for sc in scored_sentences) / n
    mean_gen = sum(sc["generic_density"] for sc in scored_sentences) / n
    mean_fin = sum(sc["finance_density"] for sc in scored_sentences) / n

    # generic_dominant: ESG/G 신호 없이 generic만 있는 문장
    n_gen_dom = sum(
        1 for sc in scored_sentences
        if sc["esg_hit"] == 0 and sc["g_hit"] == 0 and sc["generic_hit"] > 0
    )

    return {
        "n_sentences"           : n,
        "n_g_protected"         : n_g,
        "n_esg_hit"             : n_esg,
        "mean_esg_density"      : round(mean_esg, 4),
        "mean_signal_density"   : round(mean_sig, 4),
        "mean_generic_density"  : round(mean_gen, 4),
        "mean_finance_density"  : round(mean_fin, 4),
        "esg_to_generic_ratio"  : round(mean_esg / max(mean_gen, 0.001), 4),
        "generic_rhetoric_ratio": round(n_gen_dom / n, 4),
    }