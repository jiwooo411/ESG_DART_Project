# =============================================================================
# src/token_audit.py — Token Audit 모듈
# =============================================================================
# 이 모듈이 하는 일:
#   1. tokenized CSV(exp_A 권장)에서 전체 corpus의 top-N 토큰을 추출
#   2. 각 토큰의 TF(전체 빈도), DF(문서 빈도), IDF 값 계산
#   3. 수동 분류를 위한 스프레드시트 출력
#   4. 분류 결과를 로드하여 PRESERVE/BOILERPLATE 리스트 검증
#
# 왜 Token Audit이 필요한가:
#   "frequency 높다 = 제거"가 아니라 ESG relevance 기준으로 판단해야 하는데,
#   그 판단은 기계가 할 수 없다. 연구자가 직접 상위 토큰을 읽고 분류해야 한다.
#   이 과정은 분석 결과를 보기 전에 완료해야 한다.
#   분석 결과를 본 이후에 token 분류를 바꾸면 p-hacking이다.
#
# 사용법:
#   python -c "from src.token_audit import run_audit; run_audit('exp_A')"

import os
import sys
import math
import logging
import pandas as pd
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.preprocessor import ESG_PRESERVE, BOILERPLATE_NOUNS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_audit(exp_id: str = "exp_A", top_n: int = 500) -> pd.DataFrame:
    """
    tokenized CSV에서 top-N 토큰의 TF/DF/IDF를 계산하고 감사 파일을 저장한다.

    exp_A를 기준점으로 쓰는 이유:
        최소 불용어 설정이라 무엇이 corpus에 있는지 가장 투명하게 보여준다.
        이 결과에서 BOILERPLATE를 골라내면 다른 실험의 불용어 리스트가 만들어진다.

    반환: token audit DataFrame (저장 후 반환)
    """
    csv_path = os.path.join(config.PREPROC_DIR, f"tokenized_{exp_id}.csv")
    if not os.path.exists(csv_path):
        logger.error(f"파일 없음: {csv_path}")
        return pd.DataFrame()

    df = pd.read_csv(csv_path, dtype=str)
    df["joined_text"] = df["joined_text"].fillna("")

    n_docs = len(df)
    logger.info(f"문서 수: {n_docs}개")

    # ===========================================================================
    # Step 1: TF (전체 corpus 빈도) 계산
    # ===========================================================================
    all_tokens = []
    doc_token_sets = []

    for _, row in df.iterrows():
        tokens = row["joined_text"].split()
        all_tokens.extend(tokens)
        doc_token_sets.append(set(tokens))

    tf_counter = Counter(all_tokens)
    top_tokens = [tok for tok, _ in tf_counter.most_common(top_n)]
    logger.info(f"전체 어휘 크기: {len(tf_counter)}개 | Top-{top_n} 추출")

    # ===========================================================================
    # Step 2: DF (문서 빈도) + IDF 계산
    # ===========================================================================
    rows = []
    for token in top_tokens:
        tf  = tf_counter[token]
        df_ = sum(1 for s in doc_token_sets if token in s)
        idf = math.log(n_docs / df_) if df_ > 0 else 0.0

        # 사전 분류 힌트 (자동 — 수동 분류의 참고용)
        auto_hint = _auto_classify(token)

        rows.append({
            "token":      token,
            "tf":         tf,
            "df":         df_,
            "idf":        round(idf, 3),
            "tf_idf_avg": round((tf / n_docs) * idf, 3),
            "auto_hint":  auto_hint,
            # 수동 분류 컬럼 (연구자가 직접 채워야 함)
            "manual_class": "",  # ESG_SIGNAL / G_SIGNAL / AMBIGUOUS / BOILERPLATE / GENERAL
            "keep_note":    "",  # 판단 이유
        })

    audit_df = pd.DataFrame(rows)

    # ===========================================================================
    # Step 3: 저장
    # ===========================================================================
    audit_path = os.path.join(config.PREPROC_DIR, f"token_audit_{exp_id}.csv")
    audit_df.to_csv(audit_path, index=False, encoding="utf-8-sig")
    logger.info(f"Token Audit 저장: {audit_path}")

    # ===========================================================================
    # Step 4: 요약 출력
    # ===========================================================================
    _print_summary(audit_df)

    logger.info("\n" + "=" * 60)
    logger.info("다음 단계: token_audit CSV를 Excel로 열어")
    logger.info("  manual_class 컬럼을 직접 채워라.")
    logger.info("  분류 기준:")
    logger.info("    ESG_SIGNAL  — 탄소중립, 온실가스, 안전보건 등")
    logger.info("    G_SIGNAL    — 이사회, 감사위원회, 지배구조 등")
    logger.info("    AMBIGUOUS   — 주주, 경영, 시장 등 (일단 보존)")
    logger.info("    BOILERPLATE — 재무제표, 원리금, 특수관계인 등")
    logger.info("    GENERAL     — 조사, 접속사, 일반어")
    logger.info("  분류 완료 후: validate_audit() 실행")
    logger.info("=" * 60)

    return audit_df


def validate_audit(exp_id: str = "exp_A") -> dict:
    """
    수동 분류 완료된 token_audit CSV를 로드하여
    현재 PRESERVE/BOILERPLATE 리스트와 충돌을 검사한다.

    이 검사가 필요한 이유:
        사람이 BOILERPLATE로 분류했는데 현재 코드가 PRESERVE로 지정하고 있다면,
        또는 반대로 ESG_SIGNAL인데 BOILERPLATE_NOUNS에 들어가 있다면,
        설계 충돌이다. 분석 전에 반드시 해결해야 한다.
    """
    audit_path = os.path.join(config.PREPROC_DIR, f"token_audit_{exp_id}.csv")
    if not os.path.exists(audit_path):
        logger.error(f"Audit 파일 없음: {audit_path}")
        return {}

    df = pd.read_csv(audit_path, dtype=str)
    classified = df[df["manual_class"].notna() & (df["manual_class"] != "")]

    issues = {
        "preserve_vs_boilerplate": [],  # PRESERVE인데 사람이 BOILERPLATE로 분류
        "signal_in_stopwords":     [],  # ESG/G_SIGNAL인데 불용어 목록에 있음
        "boilerplate_not_removed": [],  # BOILERPLATE인데 어디서도 처리 안 됨
    }

    for _, row in classified.iterrows():
        token = row["token"]
        cls   = row["manual_class"].strip().upper()

        if cls == "BOILERPLATE" and token in ESG_PRESERVE:
            issues["preserve_vs_boilerplate"].append(token)

        if cls in ("ESG_SIGNAL", "G_SIGNAL") and token in BOILERPLATE_NOUNS:
            issues["signal_in_stopwords"].append(token)

        if cls == "BOILERPLATE" and token not in BOILERPLATE_NOUNS:
            issues["boilerplate_not_removed"].append(token)

    logger.info("=" * 60)
    logger.info("Token Audit 검증 결과")
    for issue_type, tokens in issues.items():
        if tokens:
            logger.warning(f"  [{issue_type}]: {tokens}")
        else:
            logger.info(f"  [{issue_type}]: 이상 없음")
    logger.info("=" * 60)

    return issues


def _auto_classify(token: str) -> str:
    """
    규칙 기반 자동 분류 힌트 (수동 분류의 참고용 — 최종 결정은 사람이 함).
    """
    if token in ESG_PRESERVE:
        return "ESG/G_SIGNAL(preserve)"
    if token in BOILERPLATE_NOUNS:
        return "BOILERPLATE(현재 제거대상)"
    return ""


def _print_summary(audit_df: pd.DataFrame):
    """IDF 분포 기반 요약 출력"""
    logger.info("\n[IDF 분포 요약]")
    logger.info(f"  IDF 0.0~0.1 (전문서 등장, 사실상 noise): "
                f"{(audit_df['idf'] < 0.1).sum()}개")
    logger.info(f"  IDF 0.1~0.5 (고빈도): "
                f"{((audit_df['idf'] >= 0.1) & (audit_df['idf'] < 0.5)).sum()}개")
    logger.info(f"  IDF 0.5~1.0 (중빈도): "
                f"{((audit_df['idf'] >= 0.5) & (audit_df['idf'] < 1.0)).sum()}개")
    logger.info(f"  IDF 1.0+   (희소, signal 후보): "
                f"{(audit_df['idf'] >= 1.0).sum()}개")

    logger.info("\n[IDF 최하위 20개 — boilerplate 후보]")
    bottom = audit_df.nsmallest(20, "idf")[["token", "tf", "df", "idf", "auto_hint"]]
    logger.info("\n" + bottom.to_string(index=False))

    logger.info("\n[IDF 최상위 20개 — ESG signal 후보]")
    top = audit_df.nlargest(20, "idf")[["token", "tf", "df", "idf", "auto_hint"]]
    logger.info("\n" + top.to_string(index=False))


# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp",      default="exp_A", help="감사할 실험 ID")
    parser.add_argument("--top_n",    type=int, default=500, help="상위 N개 토큰")
    parser.add_argument("--validate", action="store_true", help="수동 분류 검증 실행")
    args = parser.parse_args()

    if args.validate:
        validate_audit(args.exp)
    else:
        run_audit(args.exp, top_n=args.top_n)
