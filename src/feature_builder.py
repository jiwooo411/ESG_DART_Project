# =============================================================================
# src/feature_builder.py — firm-year 수준 scalar feature 계산
# =============================================================================
# 입력: tokenized_exp_{id}.csv (joined_text 컬럼)
# 출력: features_exp_{id}.csv  (firm-year × scalar features)
#
# 실행:
#   from src.feature_builder import build_features
#   df = build_features("exp_E")
# =============================================================================

import os
import logging
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# taxonomy 결과 기반 분류 사전 (preprocessor.py와 동일해야 함)
_G_SIGNAL = {
    "이사", "감사", "이사회", "준법", "이해관계자",
    "사외이사", "감사위원회", "위원회", "지배구조",
    "내부통제", "컴플라이언스", "투명성",
}
_ESG_SIGNAL = {
    "온실가스", "탄소중립", "탄소", "탄소배출",
    "안전보건", "안전", "보건", "임직원", "고용", "다양성", "인권",
    "재생에너지", "태양광", "풍력", "수소", "폐기물",
    "공급망", "협력사", "사회공헌", "지역사회",
    "배출량", "감축", "저감", "친환경", "기후변화", "기후",
}
_BOILERPLATE = {
    "재무제표", "부채", "차입금", "자본금", "사채", "배당금",
    "원리금", "특수관계인", "당기순이익", "이자비용", "충당금",
    "연결재무제표", "연결", "주석", "장부", "회계",
    "정관", "의결권", "의결", "결의", "등기", "법인세",
}


def _compute_row(joined_text: str) -> dict:
    """
    joined_text(공백 분리 토큰 문자열)에서 scalar feature를 계산.

    왜 비율(ratio)인가:
        보고서 길이가 기업마다 다르다. 단순 카운트는 긴 보고서를 쓰는
        기업이 항상 높은 값을 갖게 만든다. 비율은 이 길이 편향을 완화한다.
        그러나 total_word_count를 회귀의 통제 변수로 여전히 포함해야 한다.
        (비율이 완전히 길이 편향을 제거하지는 않는다.)
    """
    tokens = joined_text.split() if isinstance(joined_text, str) else []
    total = len(tokens)

    if total == 0:
        return {
            "total_tokens": 0,
            "esg_signal_count": 0,
            "g_signal_count": 0,
            "bp_count": 0,
            "esg_signal_ratio": None,
            "g_signal_ratio": None,
            "bp_contamination_rate": None,
            "esg_g_relative": None,
        }

    esg_n = sum(1 for t in tokens if t in _ESG_SIGNAL)
    g_n   = sum(1 for t in tokens if t in _G_SIGNAL)
    bp_n  = sum(1 for t in tokens if t in _BOILERPLATE)
    denom = esg_n + g_n + bp_n

    return {
        "total_tokens":          total,
        "esg_signal_count":      esg_n,
        "g_signal_count":        g_n,
        "bp_count":              bp_n,
        "esg_signal_ratio":      round(esg_n / total, 4),
        "g_signal_ratio":        round(g_n  / total, 4),
        "bp_contamination_rate": round(bp_n  / total, 4),
        # ESG+G 대비 상대적 신호 강도 (보일러플레이트 제외 기준)
        # cheap-talk 분석에서 핵심 피처: 같은 ESG 단어 비율이라도
        # boilerplate가 적은 보고서에서 더 높은 의미를 가짐
        "esg_g_relative":        round((esg_n + g_n) / denom, 4) if denom > 0 else None,
    }
# src/feature_builder.py
# _compute_tfidf_concentration() 추가 — 기존 _compute_row() 다음에 삽입


def compute_tfidf_concentration(
    documents: list[str],
    seed_words: list[str],
    top_k: int = 200,
) -> list[float]:
    """
    각 firm-year document에서 ESG seed 어휘의 TF-IDF concentration 계산.

    esg_tfidf_concentration = Σ TF-IDF(t) [t ∈ seed_words] / Σ TF-IDF(t) [top-K]

    해석:
        높음 → ESG 어휘가 해당 document의 TF-IDF 공간에서 변별적으로 분포
               = 실질적 ESG 공시에 가까움
        낮음 → ESG 어휘가 generic 언어 속에 희석
               = cheap-talk 패턴에 가까움

    왜 top_k를 쓰는가:
        전체 vocabulary TF-IDF 합산은 문서 길이에 비례해 커짐.
        top-K로 제한하면 문서 길이(verbosity) bias를 통제할 수 있음.
        단, K 선택이 결과에 영향을 미칠 수 있으므로 sensitivity check 필요.

    Decision Box:
        Alternative: 전체 vocabulary TF-IDF 합산 → verbosity bias 발생
        Choice: top-K (K=200) → verbosity 부분 통제
        Limitation: K 값이 자의적. sensitivity: K=100/200/500 비교 권장.
    """
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",  # 한국어: 문자 n-gram 또는 공백 기반
        ngram_range=(2, 4),  # 형태소 분석 없이 서브워드 근사
        min_df=2,
        max_features=5000,
    )
    # 주의: 여기서는 단어 단위로 하는 게 맞음 (형태소 분석 이후 tokenized text 기준)
    # → tokenized_documents (공백 분리된 형태소 시퀀스)를 입력으로 받아야 함
    
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = np.array(vectorizer.get_feature_names_out())
    
    seed_mask = np.array([any(seed in fn for seed in seed_words) 
                          for fn in feature_names])
    
    concentrations = []
    for i in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix[i].toarray().flatten()
        top_k_idx = np.argsort(row)[-top_k:]
        top_k_mass = row[top_k_idx].sum()
        esg_mass = row[top_k_idx][seed_mask[top_k_idx]].sum()
        
        if top_k_mass > 0:
            concentrations.append(round(esg_mass / top_k_mass, 4))
        else:
            concentrations.append(None)
    
    return concentrations

def build_features(exp_id: str, preproc_dir: str) -> pd.DataFrame:
    """
    tokenized_{exp_id}.csv → features_{exp_id}.csv

    반환: 식별자 컬럼 + scalar feature 컬럼이 붙은 DataFrame
    """
    csv_path = os.path.join(preproc_dir, f"tokenized_{exp_id}.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"{csv_path} 없음. 먼저 03_preprocess_experiment.py 실행 필요."
        )

    df = pd.read_csv(csv_path, dtype=str)
    df["token_count"] = pd.to_numeric(df["token_count"], errors="coerce").fillna(0)

    feature_rows = []
    for _, row in df.iterrows():
        feat = _compute_row(str(row.get("joined_text", "")))
        feature_rows.append(feat)

    feat_df = pd.DataFrame(feature_rows)
# ==========================================================
# ESG TF-IDF concentration
# ==========================================================

    documents = df["joined_text"].fillna("").astype(str).tolist()

    seed_words = list(_ESG_SIGNAL | _G_SIGNAL)

    feat_df["esg_tfidf_concentration"] = compute_tfidf_concentration(
        documents=documents,
        seed_words=seed_words,
        top_k=200,
    ) 
    # 식별자 컬럼 보존
    id_cols = ["stock_code", "corp_code", "fiscal_year", "esg_year", "rcept_no"]
    for col in id_cols:
        if col in df.columns:
            feat_df.insert(0, col, df[col].values)

    out_path = os.path.join(preproc_dir, f"features_{exp_id}.csv")
    feat_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"feature 저장: {out_path}  ({feat_df.shape})")

    return feat_df


# CLI 실행
if __name__ == "__main__":
    import sys
    import config
    exp_ids = sys.argv[1:] or ["exp_B", "exp_E", "exp_F"]
    for exp_id in exp_ids:
        try:
            build_features(exp_id, config.PREPROC_DIR)
        except FileNotFoundError as e:
            print(f"[SKIP] {e}")