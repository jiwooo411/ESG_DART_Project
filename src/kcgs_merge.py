# =============================================================================
# src/kcgs_merge.py — features × KCGS merge pipeline
# =============================================================================
# 사용법:
#   from src.kcgs_merge import load_kcgs, merge_features, merge_all_experiments
#
# merge key: [stock_code, fiscal_year]
# join type: inner join (KCGS 미매칭 firm-year 제외, 데이터 조작 방지)
#
# 왜 fiscal_year로 merge하는가:
#   config.py 정의: esg_year = fiscal_year + 1 (보고서 제출 연도)
#   KCGS 등급은 회계연도(fiscal_year) 기준 활동을 평가한다.
#   따라서 features의 fiscal_year ↔ kcgs의 fiscal_year 가 올바른 정렬.
#   esg_year로 merge하면 1년 misalignment 발생.

import os
import logging
import pandas as pd
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 프로젝트 루트 기준 경로
_ROOT = Path(__file__).parent.parent
KCGS_PATH     = _ROOT / "data" / "kcgs_esg_ratings.csv"
PREPROC_DIR   = _ROOT / "data" / "04_preprocessed"
MERGE_OUT_DIR = _ROOT / "data" / "05_merged"

MERGE_KEYS  = ["stock_code", "fiscal_year"]
KCGS_COLS   = ["stock_code", "fiscal_year", "corp_name",
               "kcgs_grade", "kcgs_grade_7", "kcgs_grade_4"]


# =============================================================================
# 1. KCGS 데이터 로드
# =============================================================================

def load_kcgs(path: Optional[Path] = None) -> pd.DataFrame:
    """
    kcgs_esg_ratings.csv 로드 + 기본 검증.

    반환: stock_code(str, 6자리), fiscal_year(int), kcgs_grade_7(int) 포함 DataFrame
    """
    p = Path(path) if path else KCGS_PATH
    if not p.exists():
        raise FileNotFoundError(
            f"KCGS 파일 없음: {p}\n"
            "sample_firms.csv 기반으로 자동 생성하려면 build_kcgs_from_sample() 실행."
        )

    df = pd.read_csv(p, dtype=str)
    df["stock_code"]   = df["stock_code"].str.zfill(6)
    df["fiscal_year"]  = df["fiscal_year"].astype(int)
    df["kcgs_grade_7"] = pd.to_numeric(df["kcgs_grade_7"], errors="coerce")
    df["kcgs_grade_4"] = pd.to_numeric(df["kcgs_grade_4"], errors="coerce")

    unmapped = df[df["kcgs_grade_7"].isna()]
    if len(unmapped) > 0:
        logger.warning(f"KCGS 등급 매핑 실패 {len(unmapped)}건: "
                       f"{unmapped['kcgs_grade'].unique()}")

    logger.info(f"KCGS 로드: {len(df)}건 | "
                f"등급 분포: {df['kcgs_grade_7'].value_counts().sort_index().to_dict()}")
    return df


# =============================================================================
# 2. features × KCGS merge
# =============================================================================

def merge_features(
    feat_df: pd.DataFrame,
    kcgs_df: pd.DataFrame,
    exp_id: str = "",
    verbose: bool = True,
) -> pd.DataFrame:
    """
    features DataFrame과 KCGS DataFrame을 inner join.

    Parameters
    ----------
    feat_df : features_exp_*.csv 로드 결과
    kcgs_df : load_kcgs() 결과
    exp_id  : 로그 식별용 레이블 (예: "exp_B")

    반환: merged DataFrame (KCGS 미매칭 행 제외)
    """
    label = f"[{exp_id}]" if exp_id else ""

    # 타입 통일
    feat = feat_df.copy()
    feat["stock_code"]  = feat["stock_code"].astype(str).str.zfill(6)
    feat["fiscal_year"] = feat["fiscal_year"].astype(int)

    kcgs = kcgs_df[KCGS_COLS].copy()

    before = len(feat)
    merged = feat.merge(kcgs, on=MERGE_KEYS, how="inner")
    after  = len(merged)
    dropped = before - after

    if verbose:
        print(f"{label} merge: {before}건 → {after}건 (inner join)")
        if dropped > 0:
            # 어떤 stock_code가 매칭 안 됐는지 특정
            feat_keys  = set(zip(feat["stock_code"], feat["fiscal_year"]))
            kcgs_keys  = set(zip(kcgs["stock_code"], kcgs["fiscal_year"]))
            unmatched  = feat_keys - kcgs_keys
            print(f"  ⚠️  KCGS 미매칭 {dropped}건: {sorted(unmatched)}")
        else:
            print(f"  ✅ 전건 매칭 완료")

    # 등급 분포 출력
    if "kcgs_grade_7" in merged.columns and verbose:
        dist = merged["kcgs_grade"].value_counts().sort_index().to_dict()
        print(f"  등급 분포: {dist}")

    logger.info(f"{label} merge 완료: {after}건")
    return merged


# =============================================================================
# 3. 전체 실험 일괄 merge
# =============================================================================

def merge_all_experiments(
    exp_ids: list[str] | None = None,
    save: bool = True,
) -> dict[str, pd.DataFrame]:
    """
    exp_B / exp_E / exp_F 세 실험 features를 모두 KCGS와 merge.

    Parameters
    ----------
    exp_ids : None이면 ["exp_B", "exp_E", "exp_F"] 사용
    save    : True이면 data/05_merged/merged_{exp_id}.csv 저장

    반환: {"exp_B": df, "exp_E": df, "exp_F": df}
    """
    if exp_ids is None:
        exp_ids = ["exp_B", "exp_E", "exp_F"]

    if save:
        MERGE_OUT_DIR.mkdir(parents=True, exist_ok=True)

    kcgs = load_kcgs()
    results = {}

    for exp_id in exp_ids:
        feat_path = PREPROC_DIR / f"features_{exp_id}.csv"
        if not feat_path.exists():
            logger.warning(f"features 파일 없음: {feat_path} — 스킵")
            continue

        feat = pd.read_csv(feat_path, dtype=str)
        merged = merge_features(feat, kcgs, exp_id=exp_id)
        results[exp_id] = merged

        if save and len(merged) > 0:
            out_path = MERGE_OUT_DIR / f"merged_{exp_id}.csv"
            merged.to_csv(out_path, index=False, encoding="utf-8-sig")
            print(f"  저장: {out_path.relative_to(_ROOT)}")

    print(f"\n총 {len(results)}개 실험 merge 완료")
    return results


# =============================================================================
# 4. merge 품질 요약 리포트
# =============================================================================

def merge_quality_report(merged_dict: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    merge 결과 품질을 DataFrame으로 요약.

    반환 컬럼:
        exp_id, n_rows, n_stocks, n_fiscal_years,
        kcgs_grade_min, kcgs_grade_max, kcgs_grade_mean,
        grade_variance  (분산이 너무 낮으면 discrimination 어려움)
    """
    rows = []
    for exp_id, df in merged_dict.items():
        g = df["kcgs_grade_7"].dropna()
        rows.append({
            "exp_id"          : exp_id,
            "n_rows"          : len(df),
            "n_stocks"        : df["stock_code"].nunique(),
            "n_fiscal_years"  : df["fiscal_year"].nunique(),
            "kcgs_min"        : int(g.min()) if len(g) > 0 else None,
            "kcgs_max"        : int(g.max()) if len(g) > 0 else None,
            "kcgs_mean"       : round(g.mean(), 2) if len(g) > 0 else None,
            "kcgs_std"        : round(g.std(), 2) if len(g) > 0 else None,
            "kcgs_dist"       : df["kcgs_grade"].value_counts().sort_index().to_dict()
                                if "kcgs_grade" in df.columns else {},
        })
    report = pd.DataFrame(rows)
    return report


# =============================================================================
# CLI 실행
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    print("=" * 60)
    print("features × KCGS merge pipeline")
    print("=" * 60)

    results = merge_all_experiments(save=True)

    if results:
        report = merge_quality_report(results)
        print("\n[Merge 품질 요약]")
        print(report.to_string(index=False))

        report_path = MERGE_OUT_DIR / "merge_quality_report.csv"
        report.to_csv(report_path, index=False, encoding="utf-8-sig")
        print(f"\n저장: {report_path.relative_to(_ROOT)}")
