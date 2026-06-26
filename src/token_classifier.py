# =============================================================================
# src/token_classifier.py — Token 5-범주 자동 분류기
# =============================================================================
# 이 모듈이 하는 일:
#   token_audit CSV (TF/DF/IDF 포함)의 각 토큰을 5개 범주로 자동 분류하고,
#   분류 근거(rationale), 신뢰도(confidence), 경고(risk_warning)를 기록한다.
#
# 5개 범주:
#   BOILERPLATE  — 재무/법률 의무공시 맥락, ESG specificity 없음
#   ESG_SIGNAL   — E/S 도메인 고특이성 (탄소중립, 온실가스, 안전보건)
#   G_SIGNAL     — Governance 핵심 신호, 빈도 높아도 절대 유지 (이사회, 감사위원회)
#   GENERIC      — 사업보고서 일반어, ESG specificity 낮음 (사업, 기준, 관련)
#   AMBIGUOUS    — G-domain일 수도 BOILERPLATE일 수도 있음 → 수동 검토 필요
#
# 핵심 원칙:
#   (1) 분류는 분석 결과를 보기 전에 완료해야 한다 (p-hacking 방지)
#   (2) G-signal 오분류가 가장 치명적 → 보수적 기준 적용
#   (3) IDF 임계값은 탐색적 기준, 수동 검토로 최종 결정
#   (4) 모든 판단 근거를 로그에 기록 (재현 가능성)
#
# 사용법:
#   python -m src.token_classifier --exp exp_A --top_n 500
#   python -m src.token_classifier --exp exp_A --top_n 500 --generate_audit
#
# 출력:
#   data/04_preprocessed/token_taxonomy_{exp_id}.csv
#   data/04_preprocessed/PREPROCESSING_DECISIONS.md  (append)
#   data/04_preprocessed/ambiguous_review_{exp_id}.csv

import os
import sys
import math
import logging
import argparse
import re
from datetime import datetime
from collections import Counter

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessor import ESG_PRESERVE, BOILERPLATE_NOUNS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# =============================================================================
# 1. 분류 기준 사전 — 여기서 모든 판단 기준을 명시적으로 선언한다
# =============================================================================

# --- G-domain 핵심 신호 (확장) ---
# ESG_PRESERVE에 이미 있지만 G-signal 분류에 특히 중요한 것들을 명시
G_CORE_SIGNALS = {
    "이사회", "감사위원회", "사외이사", "독립이사", "이사", "대표이사",
    "감사", "내부감사", "감사보고",
    "지배구조", "준법", "컴플라이언스", "윤리", "윤리경영",
    "투명성", "독립성", "이해충돌", "이해관계자",
    "ESG위원회", "ESG", "내부통제", "리스크관리",
    "보수위원회", "추천위원회", "이사후보",
}

# --- E-domain 핵심 신호 ---
E_CORE_SIGNALS = {
    "탄소중립", "온실가스", "탄소배출", "재생에너지", "친환경", "기후변화",
    "탄소발자국", "순환경제", "생물다양성", "에너지전환", "탄소",
    "탄소감축", "저탄소", "TCFD", "RE100", "SBT", "넷제로",
    "폐기물", "용수", "대기오염", "화학물질", "환경경영",
    "에너지효율", "신재생", "태양광", "풍력",
}

# --- S-domain 핵심 신호 ---
S_CORE_SIGNALS = {
    "안전보건", "인권", "다양성", "포용", "공급망", "사회공헌",
    "산업재해", "임직원", "협력사", "상생", "차별금지",
    "안전", "보건", "직장", "고용", "근로", "복리후생",
    "지역사회", "CSV", "CSR", "교육훈련", "육아휴직",
    "여성임원", "장애인고용", "인재",
}

# --- 재무/법무 Boilerplate 패턴 (정규식) ---
# 이 패턴에 매칭되면 BOILERPLATE 점수 상승
BOILERPLATE_PATTERNS = [
    r"^(재무|연결|별도|통합)(제표|상태표|성과표|흐름표)",  # 재무제표류
    r"^(매출|영업|순|당기)(채권|이익|손실|비용)",          # 재무 항목
    r"^(차입|부채|자본|자산)(금|잉여금|비율)",              # 재무 구조
    r"^(이익|자본)잉여금$",
    r"^(특수|관계)(관계인|사)$",
    r"^(계약|약정|보증|담보)(서|금|부)",                   # 법무 계약
    r"^(주주|배당)(총회|금|수익률|명부)",                  # 주주 관련 (총회 제외)
    r"^(원리|이자|만기)(금|상환|지급)",                    # 채무 상환
    r"^(사채|전환사채|신주인수권)",
    r"^(감가|상각|손상)(상각|차손|비용)",
    r"^(회계|세무|세금)(처리|기준|부담)",
    r"^(공시|신고|제출|공고)(서|일|의무)",                 # 공시 행정
]

# --- 일반어 패턴 (GENERIC) ---
GENERIC_PATTERNS = [
    r"^(사업|영업|경영|운영)(계획|전략|방침|현황|실적)",
    r"^(시장|산업|업종)(현황|전망|동향|분석)",
    r"^(제품|서비스|솔루션)(개발|출시|판매)",
    r"^(연구|개발|투자)(개발|비|활동)",
    r"^[가-힣]{1}(하|되|있|없|된|한)(다|고|며|며|어|어서)?$",  # 단일 어절 용언
]

# --- AMBIGUOUS 키워드 (G와 BOILERPLATE 경계) ---
AMBIGUOUS_TOKENS = {
    "주주", "총회", "주주총회", "공시", "가치", "경영",
    "보고", "위원회", "위원", "결의", "승인", "선임",
    "임기", "보수", "보상", "성과", "평가", "기준",
    "정관", "내규", "규정", "절차", "원칙", "방침",
    "보험", "계열", "자회사", "관계회사", "지주",
}

# --- IDF 임계값 ---
# 해석 방법:
#   IDF 낮음 (< 0.3) → 거의 모든 문서에 등장 → noise 가능성
#   IDF 중간 (0.3~1.5) → 일부 문서에만 등장 → signal 가능성
#   IDF 높음 (> 1.5) → 희소 → 특이성 높은 signal 후보
IDF_BOILERPLATE_THRESHOLD = 0.15   # 이하: 전문서 등장, 거의 noise
IDF_GENERIC_THRESHOLD     = 0.50   # 이하: 일반어 가능성
IDF_SIGNAL_THRESHOLD      = 1.00   # 이상: signal 특이성 충분


# =============================================================================
# 2. 핵심 분류 함수
# =============================================================================

def score_token(token: str, tf: int, df: int, idf: float, n_docs: int) -> dict:
    """
    토큰 하나를 받아 5개 범주에 대한 점수 + 최종 분류를 반환한다.

    점수 구조:
        esg_score      : ESG(E+S) 도메인 관련도 (0.0 ~ 1.0)
        gov_score      : Governance 도메인 관련도 (0.0 ~ 1.0)
        boilerplate_score : 재무/법무 Boilerplate 관련도 (0.0 ~ 1.0)
        generic_score  : 사업보고서 일반어 관련도 (0.0 ~ 1.0)

    분류 규칙 (우선순위 순):
        1. ESG_PRESERVE 목록에 있으면서 G_CORE 토큰 → G_SIGNAL (최우선)
        2. ESG_PRESERVE 목록에 있으면서 E/S 도메인 → ESG_SIGNAL
        3. AMBIGUOUS 목록에 있음 → AMBIGUOUS
        4. BOILERPLATE_NOUNS 또는 패턴 점수 높음 → BOILERPLATE
        5. IDF 낮음 + generic 신호 → GENERIC
        6. IDF 높음 + ESG 연관어 → ESG_SIGNAL
        7. 나머지 → GENERIC

    반환: {
        "auto_class", "confidence", "esg_score", "gov_score",
        "boilerplate_score", "generic_score", "risk_warning", "rationale"
    }
    """
    rationale_parts = []
    risk_warning    = ""

    # ------------------------------------------------------------------
    # Step A: 사전 기반 점수 계산
    # ------------------------------------------------------------------
    esg_score  = 0.0
    gov_score  = 0.0
    bp_score   = 0.0
    gen_score  = 0.0

    # ESG_PRESERVE 목록 확인
    in_preserve = token in ESG_PRESERVE
    in_g_core   = token in G_CORE_SIGNALS
    in_e_core   = token in E_CORE_SIGNALS
    in_s_core   = token in S_CORE_SIGNALS
    in_bp_nouns = token in BOILERPLATE_NOUNS
    in_ambig    = token in AMBIGUOUS_TOKENS

    if in_g_core or in_preserve and any(g in token for g in ["이사", "감사", "지배", "준법", "윤리", "내부"]):
        gov_score += 0.9
        rationale_parts.append(f"G-domain 핵심 사전 포함 (G_CORE_SIGNALS 또는 ESG_PRESERVE)")

    if in_e_core:
        esg_score += 0.9
        rationale_parts.append("E-domain 핵심 사전 포함 (E_CORE_SIGNALS)")

    if in_s_core:
        esg_score += 0.8
        rationale_parts.append("S-domain 핵심 사전 포함 (S_CORE_SIGNALS)")

    if in_preserve and not in_g_core and not in_e_core and not in_s_core:
        # ESG_PRESERVE에는 있지만 세부 사전에는 없음 → ESG 관련 추정
        esg_score += 0.5
        rationale_parts.append("ESG_PRESERVE 포함 (세부 분류 필요)")

    if in_bp_nouns:
        bp_score += 0.9
        rationale_parts.append("BOILERPLATE_NOUNS 사전 포함 (재무/법무 공시 용어)")

    if in_ambig:
        rationale_parts.append("AMBIGUOUS 목록 포함 (G-domain vs. 일반어 경계 토큰)")

    # ------------------------------------------------------------------
    # Step B: 패턴 매칭 점수
    # ------------------------------------------------------------------
    for bp_pattern in BOILERPLATE_PATTERNS:
        if re.search(bp_pattern, token):
            bp_score = min(bp_score + 0.4, 1.0)
            rationale_parts.append(f"재무/법무 패턴 매칭: {bp_pattern}")
            break

    for gen_pattern in GENERIC_PATTERNS:
        if re.search(gen_pattern, token):
            gen_score = min(gen_score + 0.3, 1.0)
            rationale_parts.append(f"일반어 패턴 매칭: {gen_pattern}")
            break

    # ------------------------------------------------------------------
    # Step C: IDF 기반 점수 보정
    # ------------------------------------------------------------------
    df_ratio = df / n_docs if n_docs > 0 else 1.0  # 문서 등장 비율

    if idf < IDF_BOILERPLATE_THRESHOLD:
        # 거의 모든 문서에 등장 → noise 또는 general
        bp_score  = min(bp_score  + 0.2, 1.0)
        gen_score = min(gen_score + 0.2, 1.0)
        rationale_parts.append(
            f"IDF={idf:.3f} < {IDF_BOILERPLATE_THRESHOLD} → 전문서 등장 (boilerplate/일반어 가능성)"
        )
    elif idf < IDF_GENERIC_THRESHOLD:
        gen_score = min(gen_score + 0.1, 1.0)
        rationale_parts.append(
            f"IDF={idf:.3f} → 중상위 빈도 (일반어 가능성)"
        )
    elif idf >= IDF_SIGNAL_THRESHOLD:
        # 희소 등장 → signal 특이성
        esg_score = min(esg_score + 0.15, 1.0)
        rationale_parts.append(
            f"IDF={idf:.3f} ≥ {IDF_SIGNAL_THRESHOLD} → 희소 등장, signal 특이성 가능"
        )

    # df_ratio 보정
    if df_ratio > 0.9:
        rationale_parts.append(
            f"DF ratio={df_ratio:.2f} (전체의 {df_ratio*100:.0f}% 문서에 등장) — 전문서 신호"
        )

    # ------------------------------------------------------------------
    # Step D: 최종 분류 (우선순위 엄격 적용)
    # ------------------------------------------------------------------

    # ① G_SIGNAL — G_CORE에 있으면 IDF·빈도 무관하게 G_SIGNAL
    #    이유: 이사회·감사위원회는 모든 기업에 등장하므로 IDF가 낮아도 G-domain 핵심이다
    if in_g_core or (in_preserve and gov_score >= 0.8):
        auto_class  = "G_SIGNAL"
        confidence  = 0.95
        risk_warning = ""
        rationale_parts.insert(0, "[G_SIGNAL 최우선 규칙] G-domain 사전 매칭 → IDF/빈도 무관하게 G_SIGNAL")
        return _build_result(
            auto_class, confidence, esg_score, gov_score,
            bp_score, gen_score, risk_warning,
            " | ".join(rationale_parts)
        )

    # ② ESG_SIGNAL — E/S 도메인 사전 포함
    if in_e_core or in_s_core or (in_preserve and esg_score >= 0.7):
        auto_class = "ESG_SIGNAL"
        confidence = 0.90
        risk_warning = ""
        rationale_parts.insert(0, "[ESG_SIGNAL 규칙] E/S 도메인 사전 매칭")
        return _build_result(
            auto_class, confidence, esg_score, gov_score,
            bp_score, gen_score, risk_warning,
            " | ".join(rationale_parts)
        )

    # ③ AMBIGUOUS — 경계 토큰은 무조건 수동 검토
    if in_ambig:
        auto_class  = "AMBIGUOUS"
        confidence  = 0.40
        risk_warning = "G-domain vs. 일반어 경계 — 수동 검토 필수"
        rationale_parts.insert(0, "[AMBIGUOUS 규칙] 경계 토큰 목록 포함 → 수동 검토 필요")
        return _build_result(
            auto_class, confidence, esg_score, gov_score,
            bp_score, gen_score, risk_warning,
            " | ".join(rationale_parts)
        )

    # ④ BOILERPLATE — 사전 또는 패턴 점수가 지배적
    if bp_score >= 0.6 and gov_score < 0.5 and esg_score < 0.5:
        auto_class  = "BOILERPLATE"
        confidence  = round(bp_score, 2)
        # G-signal이 BOILERPLATE로 잘못 분류될 위험 경고
        if any(g in token for g in ["이사", "감사", "지배", "통제", "준법"]):
            risk_warning = "⚠️ G-domain 키워드 포함 — BOILERPLATE 분류가 G-signal 파괴 위험. 수동 확인 필요"
        return _build_result(
            auto_class, confidence, esg_score, gov_score,
            bp_score, gen_score, risk_warning,
            " | ".join(rationale_parts)
        )

    # ⑤ 점수 경합 → AMBIGUOUS
    max_score  = max(esg_score, gov_score, bp_score, gen_score)
    scores     = {"ESG": esg_score, "GOV": gov_score, "BP": bp_score, "GEN": gen_score}
    top_scores = [k for k, v in scores.items() if v >= max_score - 0.15]
    if len(top_scores) >= 2:
        auto_class  = "AMBIGUOUS"
        confidence  = round(max_score, 2)
        risk_warning = f"점수 경합: {top_scores} — 수동 검토 필요"
        rationale_parts.insert(0, f"[AMBIGUOUS] 복수 범주 점수 경합 ({top_scores})")
        return _build_result(
            auto_class, confidence, esg_score, gov_score,
            bp_score, gen_score, risk_warning,
            " | ".join(rationale_parts)
        )

    # ⑥ GENERIC — 기본값
    auto_class = "GENERIC"
    confidence = round(max(gen_score, 1.0 - max(esg_score, gov_score, bp_score)), 2)
    risk_warning = ""
    rationale_parts.insert(0, "[GENERIC] 어떤 domain에도 속하지 않는 일반어")
    return _build_result(
        auto_class, confidence, esg_score, gov_score,
        bp_score, gen_score, risk_warning,
        " | ".join(rationale_parts)
    )


def _build_result(auto_class, confidence, esg_score, gov_score,
                  bp_score, gen_score, risk_warning, rationale) -> dict:
    return {
        "auto_class":        auto_class,
        "confidence":        confidence,
        "esg_score":         round(esg_score, 3),
        "gov_score":         round(gov_score, 3),
        "boilerplate_score": round(bp_score, 3),
        "generic_score":     round(gen_score, 3),
        "risk_warning":      risk_warning,
        "rationale":         rationale,
    }


# =============================================================================
# 3. 전체 파이프라인
# =============================================================================

def run_classifier(exp_id: str = "exp_A", top_n: int = 500,
                   generate_audit: bool = False) -> pd.DataFrame:
    """
    token_audit CSV를 로드하여 자동 분류 후 결과를 저장한다.

    generate_audit=True이면 token_audit.py를 먼저 실행한다.
    """
    # ------------------------------------------------------------------
    # Step 1: token_audit CSV 로드 또는 생성
    # ------------------------------------------------------------------
    audit_path = os.path.join(config.PREPROC_DIR, f"token_audit_{exp_id}.csv")

    if not os.path.exists(audit_path) or generate_audit:
        logger.info(f"token_audit_{exp_id}.csv 없음 또는 갱신 요청 → 생성 중...")
        from src.token_audit import run_audit
        run_audit(exp_id=exp_id, top_n=top_n)

    if not os.path.exists(audit_path):
        logger.error(f"token_audit 생성 실패: {audit_path}")
        return pd.DataFrame()

    df = pd.read_csv(audit_path, dtype={"token": str, "tf": float,
                                         "df": float, "idf": float})
    df["token"] = df["token"].fillna("").astype(str)
    df["tf"]    = pd.to_numeric(df["tf"],  errors="coerce").fillna(0).astype(int)
    df["df"]    = pd.to_numeric(df["df"],  errors="coerce").fillna(0).astype(int)
    df["idf"]   = pd.to_numeric(df["idf"], errors="coerce").fillna(0.0)

    # 총 문서 수 역산 (IDF = log(N/df) → N = df * e^IDF)
    n_docs = _infer_n_docs(df)
    logger.info(f"총 문서 수 추정: {n_docs}개")

    # ------------------------------------------------------------------
    # Step 2: 토큰별 분류 실행
    # ------------------------------------------------------------------
    results = []
    for _, row in df.iterrows():
        token = str(row["token"])
        tf    = int(row["tf"])
        df_   = int(row["df"])
        idf   = float(row["idf"])

        result = score_token(token, tf, df_, idf, n_docs)

        results.append({
            "token":             token,
            "tf":                tf,
            "df":                df_,
            "idf":               idf,
            "tf_idf_avg":        row.get("tf_idf_avg", 0.0),
            "auto_hint":         row.get("auto_hint", ""),
            **result,
        })

    taxonomy_df = pd.DataFrame(results)

    # ------------------------------------------------------------------
    # Step 3: 저장
    # ------------------------------------------------------------------
    os.makedirs(config.PREPROC_DIR, exist_ok=True)

    # 전체 taxonomy
    taxonomy_path = os.path.join(config.PREPROC_DIR, f"token_taxonomy_{exp_id}.csv")
    taxonomy_df.to_csv(taxonomy_path, index=False, encoding="utf-8-sig")
    logger.info(f"저장: token_taxonomy_{exp_id}.csv ({len(taxonomy_df)}개 토큰)")

    # AMBIGUOUS 토큰만 별도 저장 (수동 검토용)
    ambig_df = taxonomy_df[taxonomy_df["auto_class"] == "AMBIGUOUS"].copy()
    ambig_path = os.path.join(config.PREPROC_DIR, f"ambiguous_review_{exp_id}.csv")
    ambig_df.to_csv(ambig_path, index=False, encoding="utf-8-sig")
    logger.info(f"저장: ambiguous_review_{exp_id}.csv ({len(ambig_df)}개 — 수동 검토 필요)")

    # ------------------------------------------------------------------
    # Step 4: 분류 요약 출력
    # ------------------------------------------------------------------
    _print_classification_summary(taxonomy_df)

    # ------------------------------------------------------------------
    # Step 5: 의사결정 로그 추가
    # ------------------------------------------------------------------
    _append_decision_log(taxonomy_df, exp_id, n_docs)

    return taxonomy_df


def _infer_n_docs(df: pd.DataFrame) -> int:
    """IDF = log(N/df) 공식을 역산하여 총 문서 수 추정."""
    # IDF > 0인 행 사용 (IDF=0이면 df=N이므로 역산 불가)
    valid = df[(df["idf"] > 0.01) & (df["df"] > 0)].copy()
    if valid.empty:
        return 30  # fallback
    # N = df * exp(IDF)
    n_estimates = (valid["df"] * valid["idf"].apply(math.exp)).round()
    return int(n_estimates.median())


def _print_classification_summary(df: pd.DataFrame):
    """분류 결과 요약을 로그로 출력한다."""
    counts = df["auto_class"].value_counts()

    logger.info("\n" + "=" * 60)
    logger.info("【토큰 자동 분류 결과 요약】")
    logger.info("=" * 60)
    for cls in ["G_SIGNAL", "ESG_SIGNAL", "AMBIGUOUS", "BOILERPLATE", "GENERIC"]:
        n = counts.get(cls, 0)
        pct = n / len(df) * 100 if len(df) > 0 else 0
        bar = "█" * int(pct / 5)
        logger.info(f"  {cls:<15} {n:>4}개  {pct:>5.1f}%  {bar}")

    logger.info("-" * 60)

    # G-signal 목록 출력 (절대 제거 금지 토큰)
    g_tokens = df[df["auto_class"] == "G_SIGNAL"]["token"].tolist()
    logger.info(f"\n[G_SIGNAL 보호 토큰 — 절대 제거 금지] ({len(g_tokens)}개)")
    logger.info("  " + ", ".join(g_tokens[:30]))
    if len(g_tokens) > 30:
        logger.info(f"  ... 외 {len(g_tokens)-30}개")

    # ESG_SIGNAL 목록
    esg_tokens = df[df["auto_class"] == "ESG_SIGNAL"]["token"].tolist()
    logger.info(f"\n[ESG_SIGNAL 보존 토큰] ({len(esg_tokens)}개)")
    logger.info("  " + ", ".join(esg_tokens[:30]))

    # BOILERPLATE 상위 TF 토큰
    bp_df = df[df["auto_class"] == "BOILERPLATE"].nlargest(20, "tf")
    logger.info(f"\n[BOILERPLATE 고빈도 TOP 20 — 제거 후보]")
    for _, row in bp_df.iterrows():
        logger.info(f"  {row['token']:<15} tf={row['tf']:>5}  idf={row['idf']:.3f}")

    # 위험 경고 토큰
    warned = df[df["risk_warning"] != ""]["token"].tolist()
    if warned:
        logger.warning(f"\n⚠️  위험 경고 {len(warned)}개 토큰 → 수동 확인 필요:")
        for t in warned:
            w = df[df["token"] == t]["risk_warning"].values[0]
            logger.warning(f"  {t}: {w}")

    # AMBIGUOUS 목록
    ambig_tokens = df[df["auto_class"] == "AMBIGUOUS"]["token"].tolist()
    logger.info(f"\n[AMBIGUOUS — 수동 검토 필요] ({len(ambig_tokens)}개)")
    logger.info("  " + ", ".join(ambig_tokens))

    logger.info("=" * 60)
    logger.info("다음 단계:")
    logger.info("  1. ambiguous_review_{exp_id}.csv를 열어 수동 분류 완료")
    logger.info("  2. risk_warning 토큰을 직접 확인")
    logger.info("  3. 분류 완료 후 불용어 리스트 업데이트")
    logger.info("  4. 분석 결과(상관계수 등)를 보기 전에 분류를 확정해야 함 (p-hacking 방지)")
    logger.info("=" * 60)


def _append_decision_log(df: pd.DataFrame, exp_id: str, n_docs: int):
    """
    의사결정 내용을 PREPROCESSING_DECISIONS.md에 추가 기록한다.
    append 방식이므로 이전 기록이 보존된다.
    """
    log_path = os.path.join(config.PREPROC_DIR, "PREPROCESSING_DECISIONS.md")
    counts   = df["auto_class"].value_counts()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    g_tokens   = df[df["auto_class"] == "G_SIGNAL"]["token"].tolist()
    esg_tokens = df[df["auto_class"] == "ESG_SIGNAL"]["token"].tolist()
    bp_tokens  = df[df["auto_class"] == "BOILERPLATE"].nlargest(30, "tf")["token"].tolist()
    ambig_list = df[df["auto_class"] == "AMBIGUOUS"]["token"].tolist()
    warned_df  = df[df["risk_warning"] != ""][["token", "auto_class", "risk_warning"]]

    lines = [
        "",
        "---",
        "",
        f"## Token 자동 분류 실행 기록 — {exp_id}",
        f"**실행 시각:** {timestamp}  ",
        f"**총 토큰 수:** {len(df)}개  ",
        f"**추정 문서 수:** {n_docs}개  ",
        "",
        "### 분류 결과 요약",
        "",
        "| 범주 | 토큰 수 | 비율 |",
        "|------|---------|------|",
    ]
    for cls in ["G_SIGNAL", "ESG_SIGNAL", "AMBIGUOUS", "BOILERPLATE", "GENERIC"]:
        n = counts.get(cls, 0)
        pct = n / len(df) * 100 if len(df) > 0 else 0
        lines.append(f"| {cls} | {n} | {pct:.1f}% |")

    lines += [
        "",
        "### 분류 기준 (Decision Box)",
        "",
        "**Alternative:** 수동 분류 vs. 규칙 기반 자동 분류  ",
        "**Choice:** 규칙 기반 자동 분류 + AMBIGUOUS 수동 검토  ",
        "**Justification:** 500개 토큰 전체를 수동 분류하기에는 시간 비용이 크다.",
        "  G_SIGNAL/ESG_SIGNAL은 사전 기반으로 고신뢰도 자동 분류하고,",
        "  경계 토큰(AMBIGUOUS)만 수동으로 확인하는 하이브리드 방식을 선택한다.  ",
        "**Limitation:** 자동 분류가 놓치는 도메인 특이 용어가 있을 수 있다.",
        "  특히 신조어(넷제로, TCFD 등)는 사전에 없으면 GENERIC으로 오분류된다.  ",
        "",
        "### G_SIGNAL 보호 토큰 (절대 제거 금지)",
        "",
        f"총 {len(g_tokens)}개:",
        "",
        "```",
        ", ".join(g_tokens),
        "```",
        "",
        "**보호 근거:** 이사회·감사위원회·사외이사 등은 KCGS G등급 핵심 평가 항목이다.",
        "IDF가 낮아도(전문서 등장) G-domain 핵심 신호이므로 절대 제거하지 않는다.",
        "이 단어들을 불용어로 처리하면 G 피처가 완전히 소실된다.",
        "",
        "### ESG_SIGNAL 보존 토큰",
        "",
        f"총 {len(esg_tokens)}개:",
        "",
        "```",
        ", ".join(esg_tokens),
        "```",
        "",
        "### BOILERPLATE 제거 후보 (TF 상위 30개)",
        "",
        f"총 {counts.get('BOILERPLATE', 0)}개 분류, 상위 30개:",
        "",
        "```",
        ", ".join(bp_tokens),
        "```",
        "",
        "**제거 정당성:** 재무제표·원리금·특수관계인 등은 사업보고서의 의무 공시 사항으로",
        "ESG 언어와 무관한 boilerplate다. 이를 포함하면 TF-IDF 피처가 ESG 신호가 아니라",
        "재무 공시 규모를 반영할 위험이 있다.",
        "",
        "### AMBIGUOUS 토큰 — 수동 검토 필요",
        "",
        f"총 {len(ambig_list)}개:",
        "",
        "```",
        ", ".join(ambig_list),
        "```",
        "",
        "**수동 분류 기준 (아래 컬럼을 채울 것):**",
        "- `manual_class`: G_SIGNAL / ESG_SIGNAL / BOILERPLATE / GENERIC",
        "- `keep_note`: 판단 근거 (한 줄로)",
        "",
        "**예시 판단:**",
        "- 주주: G-domain 이해관계자이지만 '주주총회 소집'은 의무공시 → AMBIGUOUS",
        "- 경영: '경영진단'(IV섹션 제목)이면 GENERIC, '지속가능경영'이면 ESG_SIGNAL",
        "- 총회: '주주총회' 맥락이면 BOILERPLATE, 단독 사용이면 GENERIC",
        "",
    ]

    if not warned_df.empty:
        lines += [
            "### ⚠️ 위험 경고 토큰",
            "",
            "| 토큰 | 분류 | 경고 |",
            "|------|------|------|",
        ]
        for _, row in warned_df.iterrows():
            lines.append(f"| {row['token']} | {row['auto_class']} | {row['risk_warning']} |")
        lines.append("")

    lines += [
        "### 다음 단계",
        "",
        "1. `ambiguous_review_{exp_id}.csv` 열어 `manual_class` 컬럼 채우기",
        "2. 위험 경고 토큰 직접 확인 및 재분류",
        "3. 분류 확정 → `token_audit.py`의 `validate_audit()` 실행",
        "4. **중요:** 아래 단계는 반드시 분류 확정 후 실행",
        "   - exp_E, exp_F 재전처리",
        "   - Spearman 상관 분석",
        "   - 회귀 모형 추정",
        "",
        f"*이 기록은 {timestamp}에 자동 생성되었습니다.*",
        "",
    ]

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"의사결정 로그 추가: {log_path}")


# =============================================================================
# 4. 분류 결과 → 불용어 리스트 내보내기
# =============================================================================

def export_stopword_update(exp_id: str = "exp_A", manual_reviewed: bool = False):
    """
    분류 결과를 바탕으로 불용어 리스트 업데이트 제안을 생성한다.

    manual_reviewed=True이면 AMBIGUOUS에서 수동 분류된 토큰도 포함한다.

    이 함수는 분류가 확정된 후에만 실행해야 한다.
    분석 결과를 본 이후에는 이 함수를 실행하더라도 불용어를 바꾸지 않는다.
    """
    taxonomy_path = os.path.join(config.PREPROC_DIR, f"token_taxonomy_{exp_id}.csv")
    if not os.path.exists(taxonomy_path):
        logger.error("token_taxonomy CSV 없음. run_classifier()를 먼저 실행하세요.")
        return

    df = pd.read_csv(taxonomy_path, dtype=str)

    new_boilerplate = df[df["auto_class"] == "BOILERPLATE"]["token"].tolist()
    keep_g_signal   = df[df["auto_class"] == "G_SIGNAL"]["token"].tolist()
    keep_esg_signal = df[df["auto_class"] == "ESG_SIGNAL"]["token"].tolist()

    if manual_reviewed:
        # AMBIGUOUS에서 수동 분류 반영 (manual_class 컬럼 필요)
        audit_path = os.path.join(config.PREPROC_DIR, f"token_audit_{exp_id}.csv")
        if os.path.exists(audit_path):
            audit_df = pd.read_csv(audit_path, dtype=str)
            manual_bp = audit_df[
                audit_df["manual_class"].str.upper() == "BOILERPLATE"
            ]["token"].tolist()
            new_boilerplate = list(set(new_boilerplate + manual_bp))

    update_path = os.path.join(config.PREPROC_DIR, f"stopword_update_{exp_id}.py")
    lines = [
        "# ============================================================",
        f"# 자동 생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# 실험: {exp_id}",
        "# 이 파일을 preprocessor.py에 반영하기 전에 반드시 내용을 확인하라.",
        "# 분석 결과를 본 이후에는 수정하지 않는다 (p-hacking 방지).",
        "# ============================================================",
        "",
        "# BOILERPLATE_NOUNS에 추가할 토큰",
        "NEW_BOILERPLATE_NOUNS = {",
    ]
    for t in sorted(new_boilerplate):
        lines.append(f'    "{t}",')
    lines += [
        "}",
        "",
        "# G_SIGNAL — 절대 제거 금지 (ESG_PRESERVE에 포함 확인 요망)",
        "CONFIRMED_G_SIGNALS = {",
    ]
    for t in sorted(keep_g_signal):
        lines.append(f'    "{t}",')
    lines += [
        "}",
        "",
        "# ESG_SIGNAL — 보존 확정",
        "CONFIRMED_ESG_SIGNALS = {",
    ]
    for t in sorted(keep_esg_signal):
        lines.append(f'    "{t}",')
    lines += [
        "}",
    ]

    with open(update_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"불용어 업데이트 파일 저장: {update_path}")
    logger.info(f"  → 추가 BOILERPLATE: {len(new_boilerplate)}개")
    logger.info(f"  → 확정 G_SIGNAL: {len(keep_g_signal)}개")
    logger.info(f"  → 확정 ESG_SIGNAL: {len(keep_esg_signal)}개")
    logger.info("  → preprocessor.py 수동 반영 후 exp_E/F 재실행")


# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Token 5-범주 자동 분류기"
    )
    parser.add_argument("--exp",     default="exp_A",
                        help="분류할 실험 ID (기본: exp_A)")
    parser.add_argument("--top_n",   type=int, default=500,
                        help="분류할 상위 토큰 수 (기본: 500)")
    parser.add_argument("--generate_audit", action="store_true",
                        help="token_audit CSV가 없으면 자동 생성")
    parser.add_argument("--export_stopwords", action="store_true",
                        help="분류 완료 후 불용어 업데이트 파일 내보내기")
    parser.add_argument("--manual_reviewed", action="store_true",
                        help="AMBIGUOUS 수동 분류 완료된 경우 반영")
    args = parser.parse_args()

    run_classifier(
        exp_id=args.exp,
        top_n=args.top_n,
        generate_audit=args.generate_audit,
    )

    if args.export_stopwords:
        export_stopword_update(args.exp, manual_reviewed=args.manual_reviewed)
