# =============================================================================
# 03_preprocess_experiment.py — 전처리 비교 실험 스크립트
# =============================================================================
# 실행: python 03_preprocess_experiment.py
#
# 이 스크립트가 하는 일:
#   1. firm_year_documents.csv 로드
#   2. 4가지 실험 설정(exp_A ~ exp_D)을 각각 적용
#   3. 토큰화 결과를 CSV로 저장
#   4. 설정별 비교 통계 및 시각화 출력
#
# 팀 비교 기준:
#   - 평균 토큰 수
#   - 어휘 크기(vocabulary size)
#   - Coverage (firm-year 중 토큰 1개 이상인 비율)
#   - Top-20 토큰 — 직접 눈으로 읽어볼 것!
#
# 중요: 통계가 좋아도 top-20 토큰이 ESG와 무관하면 나쁜 전처리다.

import os
import sys
import logging
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # 서버 환경에서도 동작
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from src.preprocessor import (
    EXPERIMENT_CONFIGS,
    preprocess_document,
    get_tagger,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# 한글 폰트 설정 (matplotlib)
# Windows: "Malgun Gothic" / Mac: "AppleGothic" / Linux: 별도 설치 필요
try:
    plt.rcParams["font.family"] = "Malgun Gothic"
except Exception:
    pass
plt.rcParams["axes.unicode_minus"] = False


# =============================================================================
# 메인 실험 함수
# =============================================================================

def run_experiments(exp_ids: list[str] = None):
    """
    exp_ids: 실행할 실험 ID 목록 (None이면 전체)
             예: ["exp_A", "exp_B"]
    """
    if exp_ids is None:
        exp_ids = list(EXPERIMENT_CONFIGS.keys())

    logger.info("=" * 60)
    logger.info(f"전처리 실험 시작: {exp_ids}")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: firm-year documents 로드
    # ------------------------------------------------------------------
    if not os.path.exists(config.FIRM_YEAR_DOC_PATH):
        logger.error("firm_year_documents.csv 없음. 먼저 02_extract_sections.py를 실행하세요.")
        return

    docs_df = pd.read_csv(config.FIRM_YEAR_DOC_PATH, dtype=str)
    logger.info(f"firm-year document 수: {len(docs_df)}개")

    # 회사명 목록 (회사명 제거 실험용)
    corp_names = _load_company_names()

    # ------------------------------------------------------------------
    # Step 2: 실험별 전처리
    # ------------------------------------------------------------------
    comparison_stats = []

    for exp_id in exp_ids:
        if exp_id not in EXPERIMENT_CONFIGS:
            logger.warning(f"알 수 없는 실험 ID: {exp_id}")
            continue

        cfg = EXPERIMENT_CONFIGS[exp_id]
        logger.info(f"\n--- {exp_id}: {cfg['description']} ---")

        # 형태소 분석기 초기화 (한 번만)
        try:
            tagger = get_tagger(cfg["tagger_name"])
        except Exception as e:
            logger.error(f"형태소 분석기 초기화 실패 ({cfg['tagger_name']}): {e}")
            continue

        result_rows = []
        all_tokens_flat = []

        for _, row in docs_df.iterrows():
            doc_text = str(row.get("document", ""))

            # 전처리 적용
            result = preprocess_document(
                text=doc_text,
                config=cfg,
                tagger=tagger,
                company_names=corp_names,
            )

            result_rows.append({
                "stock_code":   row["stock_code"],
                "corp_code":    row["corp_code"],
                "fiscal_year":  row["fiscal_year"],
                "esg_year":     row["esg_year"],
                "exp_id":       exp_id,
                "token_count":  result["token_count"],
                "joined_text":  result["joined_text"],
            })
            all_tokens_flat.extend(result["tokens"])

        result_df = pd.DataFrame(result_rows)

        # 저장
        out_path = os.path.join(config.PREPROC_DIR, f"tokenized_{exp_id}.csv")
        result_df.to_csv(out_path, index=False, encoding="utf-8-sig")
        logger.info(f"저장: {out_path}")

        # 통계 계산
        vocab = set(all_tokens_flat)
        top20 = [w for w, _ in Counter(all_tokens_flat).most_common(20)]
        coverage = (result_df["token_count"] > 0).mean()

        stats = {
            "exp_id":           exp_id,
            "description":      cfg["description"],
            "tagger":           cfg["tagger_name"],
            "stopword":         cfg["stopword_strength"],
            "number_mode":      cfg["number_mode"],
            "min_seeds":        cfg["passage_min_seeds"],
            "avg_token_count":  round(result_df["token_count"].mean(), 1),
            "vocab_size":       len(vocab),
            "coverage_pct":     round(coverage * 100, 1),
            "top20_tokens":     " | ".join(top20),
        }
        comparison_stats.append(stats)

        logger.info(f"  평균 토큰 수: {stats['avg_token_count']}")
        logger.info(f"  어휘 크기:   {stats['vocab_size']}")
        logger.info(f"  Coverage:    {stats['coverage_pct']}%")
        logger.info(f"  Top-20 토큰: {stats['top20_tokens']}")
        logger.info("  ↑ 이 목록이 ESG와 관련 있는지 직접 읽어볼 것!")

    # ------------------------------------------------------------------
    # Step 3: 비교 통계 저장
    # ------------------------------------------------------------------
    comp_path = os.path.join(config.PREPROC_DIR, "preprocessing_comparison.csv")
    comp_df = pd.DataFrame(comparison_stats)
    comp_df.to_csv(comp_path, index=False, encoding="utf-8-sig")
    logger.info(f"\n비교 통계 저장: {comp_path}")

    # ------------------------------------------------------------------
    # Step 4: 시각화
    # ------------------------------------------------------------------
    if len(comparison_stats) > 1:
        _plot_comparison(comp_df)

    logger.info("=" * 60)
    logger.info("실험 완료")
    logger.info("=" * 60)


# =============================================================================
# 시각화 함수
# =============================================================================

def _plot_comparison(comp_df: pd.DataFrame):
    """실험 설정별 핵심 지표를 막대그래프로 시각화"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle("전처리 실험 비교", fontsize=14, fontweight="bold")

    exp_labels = comp_df["exp_id"].tolist()

    # 평균 토큰 수
    axes[0].bar(exp_labels, comp_df["avg_token_count"], color="#4C72B0")
    axes[0].set_title("평균 토큰 수")
    axes[0].set_ylabel("tokens")
    for i, v in enumerate(comp_df["avg_token_count"]):
        axes[0].text(i, v + 5, str(v), ha="center", fontsize=9)

    # 어휘 크기
    axes[1].bar(exp_labels, comp_df["vocab_size"], color="#55A868")
    axes[1].set_title("어휘 크기 (Vocabulary Size)")
    axes[1].set_ylabel("unique tokens")
    for i, v in enumerate(comp_df["vocab_size"]):
        axes[1].text(i, v + 5, str(v), ha="center", fontsize=9)

    # Coverage
    axes[2].bar(exp_labels, comp_df["coverage_pct"], color="#C44E52")
    axes[2].set_title("Coverage (%)\n(토큰 있는 firm-year 비율)")
    axes[2].set_ylabel("%")
    axes[2].set_ylim(0, 105)
    for i, v in enumerate(comp_df["coverage_pct"]):
        axes[2].text(i, v + 1, f"{v}%", ha="center", fontsize=9)

    plt.tight_layout()
    plot_path = os.path.join(config.PREPROC_DIR, "experiment_comparison.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"시각화 저장: {plot_path}")


# =============================================================================
# 유틸리티 함수
# =============================================================================

def _load_company_names() -> list[str]:
    """
    수집된 보고서의 회사명 목록을 반환.
    corp_code_map.csv 또는 sample_firms.csv에서 읽는다.
    """
    names = []
    if os.path.exists(config.CORP_CODE_MAP_PATH):
        df = pd.read_csv(config.CORP_CODE_MAP_PATH, dtype=str)
        names = df["corp_name"].dropna().tolist()
    logger.info(f"회사명 목록: {len(names)}개 로드")
    return names


# =============================================================================
# TF-IDF 피처 계산 (선택적 실행)
# =============================================================================

def compute_tfidf_features(exp_id: str, max_features: int = 500) -> pd.DataFrame:
    """
    특정 실험 설정의 토큰화 결과로 TF-IDF 행렬을 계산하여 반환.

    왜 TF-IDF를 쓰는가:
        단순 단어 빈도(TF)는 보고서 길이에 편향된다.
        긴 보고서를 쓰는 기업이 ESG 단어도 더 많이 쓰는 것처럼 보인다.
        TF-IDF는 문서 내 희소 단어에 높은 가중치를 줘서
        보고서 길이 편향을 어느 정도 완화한다.

    이 행렬이 다음 단계(회귀 분석)의 입력이 된다.
    각 행 = firm-year, 각 열 = ESG 관련 단어, 값 = TF-IDF 가중치
    """
    csv_path = os.path.join(config.PREPROC_DIR, f"tokenized_{exp_id}.csv")
    if not os.path.exists(csv_path):
        logger.error(f"{csv_path} 없음. 먼저 run_experiments()를 실행하세요.")
        return pd.DataFrame()

    df = pd.read_csv(csv_path, dtype=str)
    df["joined_text"] = df["joined_text"].fillna("")

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=2,           # 2개 이상 문서에서 등장한 단어만
        sublinear_tf=True,  # log(1+TF) 스케일링
    )

    tfidf_matrix = vectorizer.fit_transform(df["joined_text"])
    feature_names = vectorizer.get_feature_names_out()

    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=feature_names
    )

    # 식별자 컬럼 붙이기
    meta_cols = ["stock_code", "corp_code", "fiscal_year", "esg_year"]
    for col in meta_cols:
        if col in df.columns:
            tfidf_df.insert(0, col, df[col].values)

    out_path = os.path.join(config.PREPROC_DIR, f"tfidf_{exp_id}.csv")
    tfidf_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"TF-IDF 행렬 저장: {out_path}  ({tfidf_df.shape})")
    return tfidf_df


# =============================================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exps", nargs="+", default=None,
        help="실행할 실험 ID (예: --exps exp_A exp_B). 기본값: 전체"
    )
    parser.add_argument(
        "--tfidf", action="store_true",
        help="전처리 후 TF-IDF 행렬도 계산할지 여부"
    )
    args = parser.parse_args()

    run_experiments(exp_ids=args.exps)

    if args.tfidf:
        for exp_id in (args.exps or list(EXPERIMENT_CONFIGS.keys())):
            compute_tfidf_features(exp_id)
