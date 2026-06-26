# =============================================================================
# 04_evaluate_preprocessing.py — Preprocessing Quality Evaluation
# =============================================================================
#
# 목적:
#   전처리 실험(exp_A ~ exp_F) 결과를 measurement validity 기준으로 평가한다.
#   단순히 "토큰 수가 줄었는가"를 보는 게 아니라, 아래 질문에 답한다:
#
#   1. Boilerplate Contamination 감소
#      → 재무/법무 의무공시 토큰이 top-N에서 줄었는가?
#
#   2. ESG Specificity 향상
#      → top-N 토큰 중 ESG_SIGNAL / G_SIGNAL 비율이 높아졌는가?
#
#   3. G-Signal Preservation
#      → 이사회·감사·이해관계자 등이 살아 있는가?
#
#   4. Coverage 유지
#      → 토큰이 0인 firm-year가 늘지 않았는가?
#
# 실행:
#   python 04_evaluate_preprocessing.py
#   python 04_evaluate_preprocessing.py --exps exp_B exp_E exp_F
#   python 04_evaluate_preprocessing.py --top_n 30 --save_report
#
# 출력:
#   data/04_preprocessed/eval_report.txt     — 텍스트 요약
#   data/04_preprocessed/eval_comparison.csv — 실험별 지표 비교
#   data/04_preprocessed/eval_tfidf_top.csv  — TF-IDF top token 비교
#   data/04_preprocessed/eval_comparison.png — 시각화
# =============================================================================

import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    plt.rcParams["font.family"] = "Malgun Gothic"
except Exception:
    pass
plt.rcParams["axes.unicode_minus"] = False

# =============================================================================
# 평가 기준 사전 (taxonomy 결과 반영)
# =============================================================================

# 측정 타당도 평가 기준 토큰 목록
# 이 목록을 보고 top-N에서의 비율을 측정함

G_SIGNAL_TOKENS = {
    "이사", "감사", "이사회", "준법", "이해관계자",
    "사외이사", "감사위원회", "ESG위원회", "컴플라이언스",
    "위원회", "지배구조", "투명성", "내부통제", "주주",
}

ESG_SIGNAL_TOKENS = {
    "온실가스", "탄소중립", "탄소", "탄소배출", "탄소발자국",
    "안전보건", "안전", "보건",
    "임직원", "고용", "다양성", "인권", "노동",
    "재생에너지", "태양광", "풍력", "수소",
    "폐기물", "오염", "생태계", "순환경제",
    "공급망", "협력사", "사회공헌", "지역사회",
    "배출량", "감축", "저감", "친환경",
    "기후변화", "기후",
}

BOILERPLATE_TOKENS = {
    "재무제표", "부채", "차입금", "자본금", "사채", "배당금",
    "원리금", "특수관계인", "당기순이익", "이자비용", "충당금",
    "매출액", "손익", "부채비율", "회사채", "원가",
    "연결재무제표", "연결", "주석", "장부", "회계",
    "정관", "의결권", "의결", "결의", "등기",
    "법인세", "상법", "공고", "위임",
}


# =============================================================================
# 핵심 지표 계산 함수
# =============================================================================

def compute_metrics(exp_id: str,
                    df: pd.DataFrame,
                    top_n: int = 30) -> dict:
    """
    단일 실험의 평가 지표를 계산한다.

    계산하는 것:
        1. 기본 통계: avg_token_count, vocab_size, coverage_pct
        2. TF corpus 기반 top-N 토큰 빈도 분포
        3. top-N 중 G_SIGNAL / ESG_SIGNAL / BOILERPLATE 비율
        4. G_SIGNAL 토큰 중 실제 등장한 개수 (G-coverage)

    왜 corpus TF (전체 빈도)와 TF-IDF를 둘 다 보는가:
        - Corpus TF top-N: 실제로 어떤 단어가 많이 쓰이는지 보여줌
          → Boilerplate contamination을 직접 확인하는 데 적합
        - TF-IDF top-N: 문서 간 변별력이 높은 단어가 어디인지 보여줌
          → ESG 피처의 실질 신호 강도를 확인하는 데 적합
        두 관점을 비교해야 "top-N이 ESG를 측정하는가"를 판단할 수 있음
    """
    if df.empty:
        return {}

    # 기본 통계
    all_tokens_flat = []
    for joined in df["joined_text"].fillna(""):
        all_tokens_flat.extend(joined.split())

    token_counts = df["token_count"].astype(int)
    avg_token = round(token_counts.mean(), 1)
    vocab = set(all_tokens_flat)
    coverage = round((token_counts > 0).mean() * 100, 1)

    # Corpus TF top-N
    tf_counter = Counter(all_tokens_flat)
    corpus_top_n = [w for w, _ in tf_counter.most_common(top_n)]

    # 분류별 비율 (corpus TF 기준)
    g_in_top = [t for t in corpus_top_n if t in G_SIGNAL_TOKENS]
    esg_in_top = [t for t in corpus_top_n if t in ESG_SIGNAL_TOKENS]
    bp_in_top = [t for t in corpus_top_n if t in BOILERPLATE_TOKENS]

    g_coverage = len([t for t in G_SIGNAL_TOKENS if t in vocab])

    # TF-IDF top-N (문서 간 변별력 기준)
    texts = df["joined_text"].fillna("").tolist()
    tfidf_top_n = []
    try:
        vectorizer = TfidfVectorizer(max_features=500, min_df=2, sublinear_tf=True)
        mat = vectorizer.fit_transform(texts)
        mean_tfidf = np.asarray(mat.mean(axis=0)).flatten()
        feature_names = vectorizer.get_feature_names_out()
        top_idx = mean_tfidf.argsort()[::-1][:top_n]
        tfidf_top_n = [feature_names[i] for i in top_idx]
    except Exception as e:
        logger.warning(f"TF-IDF 계산 실패 ({exp_id}): {e}")

    tfidf_g = [t for t in tfidf_top_n if t in G_SIGNAL_TOKENS]
    tfidf_esg = [t for t in tfidf_top_n if t in ESG_SIGNAL_TOKENS]
    tfidf_bp = [t for t in tfidf_top_n if t in BOILERPLATE_TOKENS]

    return {
        "exp_id":            exp_id,
        "n_docs":            len(df),
        "avg_token_count":   avg_token,
        "vocab_size":        len(vocab),
        "coverage_pct":      coverage,

        # Corpus TF 기준
        "tf_top_n":          " | ".join(corpus_top_n),
        "tf_bp_count":       len(bp_in_top),
        "tf_bp_rate":        round(len(bp_in_top) / top_n * 100, 1),
        "tf_esg_count":      len(esg_in_top),
        "tf_esg_rate":       round(len(esg_in_top) / top_n * 100, 1),
        "tf_g_count":        len(g_in_top),
        "tf_g_rate":         round(len(g_in_top) / top_n * 100, 1),
        "tf_bp_tokens":      ", ".join(bp_in_top),
        "tf_esg_tokens":     ", ".join(esg_in_top),
        "tf_g_tokens":       ", ".join(g_in_top),

        # TF-IDF 기준
        "tfidf_top_n":       " | ".join(tfidf_top_n),
        "tfidf_bp_count":    len(tfidf_bp),
        "tfidf_bp_rate":     round(len(tfidf_bp) / top_n * 100, 1) if tfidf_top_n else None,
        "tfidf_esg_count":   len(tfidf_esg),
        "tfidf_esg_rate":    round(len(tfidf_esg) / top_n * 100, 1) if tfidf_top_n else None,
        "tfidf_g_count":     len(tfidf_g),
        "tfidf_g_rate":      round(len(tfidf_g) / top_n * 100, 1) if tfidf_top_n else None,

        # G-Signal 절대 보존 확인
        "g_signal_in_vocab": g_coverage,
        "g_signal_total":    len(G_SIGNAL_TOKENS),
        "g_signal_pct":      round(g_coverage / len(G_SIGNAL_TOKENS) * 100, 1),
        "g_missing":         ", ".join(
            [t for t in G_SIGNAL_TOKENS if t not in vocab]
        ),
    }


# =============================================================================
# Boilerplate 감소 Delta 계산
# =============================================================================

def compute_boilerplate_reduction(baseline_metrics: dict,
                                   target_metrics: dict,
                                   top_n: int = 30) -> dict:
    """
    baseline(exp_B) 대비 target(exp_E 또는 exp_F)의 boilerplate 감소를 계산.

    해석 기준:
        tf_bp_rate 감소 → 재무 boilerplate 명사가 top-N에서 줄었음
        tfidf_bp_rate 감소 → TF-IDF 기준으로도 boilerplate 변별력이 낮아졌음
        두 지표가 모두 감소해야 "boilerplate contamination 감소" 주장 가능

    주의:
        bp_rate가 낮아진 것이 ESG specificity 증가를 의미하지 않는다.
        esg_rate도 함께 확인해야 한다.
    """
    b = baseline_metrics
    t = target_metrics

    if not b or not t:
        return {}

    return {
        "baseline_exp":          b.get("exp_id"),
        "target_exp":            t.get("exp_id"),
        # Corpus TF 기준 변화
        "delta_tf_bp_rate":      round(t["tf_bp_rate"] - b["tf_bp_rate"], 1),
        "delta_tf_esg_rate":     round(t["tf_esg_rate"] - b["tf_esg_rate"], 1),
        "delta_tf_g_rate":       round(t["tf_g_rate"] - b["tf_g_rate"], 1),
        "delta_token_count":     round(t["avg_token_count"] - b["avg_token_count"], 1),
        "delta_vocab_size":      t["vocab_size"] - b["vocab_size"],
        # TF-IDF 기준 변화
        "delta_tfidf_bp_rate":   round((t["tfidf_bp_rate"] or 0) - (b["tfidf_bp_rate"] or 0), 1),
        "delta_tfidf_esg_rate":  round((t["tfidf_esg_rate"] or 0) - (b["tfidf_esg_rate"] or 0), 1),
        # G-signal 보존
        "g_signal_pct_baseline": b["g_signal_pct"],
        "g_signal_pct_target":   t["g_signal_pct"],
        "g_missing_target":      t.get("g_missing", ""),
    }


# =============================================================================
# 평가 리포트 출력
# =============================================================================

def print_evaluation_report(metrics_list: list, deltas: list, top_n: int):
    """
    연구자 관점의 평가 리포트를 출력한다.
    단순 수치 나열이 아니라 각 지표의 의미를 함께 서술.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("  ESG DART 전처리 품질 평가 보고서")
    lines.append(f"  기준: top-{top_n} 토큰 / taxonomy 분류 사전 적용")
    lines.append("=" * 70)
    lines.append("")

    # 1. 기본 통계 비교
    lines.append("▶ 1. 기본 통계 비교")
    lines.append("-" * 50)
    header = f"{'실험':<8} {'문서수':>6} {'평균토큰':>8} {'어휘크기':>8} {'Coverage':>9}"
    lines.append(header)
    for m in metrics_list:
        row = (f"{m['exp_id']:<8} {m['n_docs']:>6} {m['avg_token_count']:>8.1f} "
               f"{m['vocab_size']:>8} {m['coverage_pct']:>8.1f}%")
        lines.append(row)
    lines.append("")

    # 2. Boilerplate Contamination
    lines.append(f"▶ 2. Boilerplate Contamination (top-{top_n} 중 재무/법무 boilerplate 비율)")
    lines.append(f"   해석: 이 비율이 낮을수록 피처가 ESG 신호를 더 잘 담는다.")
    lines.append("-" * 60)
    header2 = f"{'실험':<8} {'TF-BP%':>8} {'TF-BP 토큰'}"
    lines.append(header2)
    for m in metrics_list:
        row2 = (f"{m['exp_id']:<8} {m['tf_bp_rate']:>7.1f}%  {m['tf_bp_tokens']}")
        lines.append(row2)
    lines.append("")

    # 3. ESG Specificity
    lines.append(f"▶ 3. ESG Specificity (top-{top_n} 중 ESG_SIGNAL + G_SIGNAL 비율)")
    lines.append(f"   해석: 높을수록 피처가 ESG 표현 언어를 선택적으로 담는다.")
    lines.append("-" * 60)
    header3 = f"{'실험':<8} {'TF-ESG%':>8} {'TF-G%':>7} {'ESG+G합계%':>10}"
    lines.append(header3)
    for m in metrics_list:
        total_rate = round(m['tf_esg_rate'] + m['tf_g_rate'], 1)
        row3 = (f"{m['exp_id']:<8} {m['tf_esg_rate']:>7.1f}%"
                f" {m['tf_g_rate']:>6.1f}%  {total_rate:>9.1f}%")
        lines.append(row3)
    lines.append("")

    # 4. G-Signal Preservation ← 가장 중요한 검증
    lines.append("▶ 4. G-Signal Preservation (KCGS G등급 핵심 신호 보존 여부)")
    lines.append(f"   보호 대상: {len(G_SIGNAL_TOKENS)}개 토큰")
    lines.append(f"   위반 시: G 피처가 소실되어 governance 상관분석이 불가능해짐")
    lines.append("-" * 60)
    for m in metrics_list:
        status = "✅ 보존" if m['g_signal_pct'] >= 80 else "⚠️ 일부 손실"
        missing_str = f"  (누락: {m['g_missing']})" if m['g_missing'] else ""
        row4 = (f"  {m['exp_id']}: {m['g_signal_in_vocab']}/{m['g_signal_total']} "
                f"({m['g_signal_pct']}%) {status}{missing_str}")
        lines.append(row4)
    lines.append("")

    # 5. exp_B 대비 Delta
    if deltas:
        lines.append("▶ 5. exp_B 대비 변화량 (Δ)")
        lines.append(f"   해석: Δbp_rate < 0 → boilerplate 감소 / Δesg_rate > 0 → ESG specificity 향상")
        lines.append("-" * 70)
        header5 = (f"{'비교':<14} {'Δbp_rate':>10} {'Δesg_rate':>10} "
                   f"{'Δg_rate':>8} {'Δtokens':>8} {'G_missing'}")
        lines.append(header5)
        for d in deltas:
            row5 = (
                f"{d['baseline_exp']}→{d['target_exp']:<6}"
                f" {d['delta_tf_bp_rate']:>+9.1f}%"
                f" {d['delta_tf_esg_rate']:>+9.1f}%"
                f" {d['delta_tf_g_rate']:>+7.1f}%"
                f" {d['delta_token_count']:>+7.1f}"
                f"  {d['g_missing_target'] or '없음'}"
            )
            lines.append(row5)
        lines.append("")

    # 6. TF-IDF Top Token 비교 (직접 읽을 것)
    lines.append(f"▶ 6. TF-IDF Top-{top_n} 토큰 비교 (직접 읽고 해석할 것)")
    lines.append(f"   ★ 통계보다 이 목록이 더 중요하다.")
    lines.append(f"   ESG 연구자라면 top token을 보고 직관적으로 판단해야 한다.")
    lines.append("-" * 70)
    for m in metrics_list:
        lines.append(f"\n  [{m['exp_id']}] {m.get('description', '')}")
        # 3줄로 분할 출력
        tfidf_tokens = m.get("tfidf_top_n", "").split(" | ")
        chunk_size = 10
        for i in range(0, len(tfidf_tokens), chunk_size):
            lines.append("  " + " / ".join(tfidf_tokens[i:i+chunk_size]))

    lines.append("")
    lines.append("=" * 70)
    lines.append("  평가 완료. 다음 단계: Spearman 상관 분석 (EXP_001)")
    lines.append("  주의: 이 평가 결과를 보고 exp 설정을 바꾸면 p-hacking이다.")
    lines.append("        pre-registered baseline(exp_B)은 변경 불가.")
    lines.append("=" * 70)

    report = "\n".join(lines)
    print(report)
    return report


# =============================================================================
# 시각화
# =============================================================================

def plot_evaluation(metrics_list: list, top_n: int, out_path: str):
    """
    4개 지표를 2×2 그리드로 시각화:
        [0,0] Boilerplate Rate (낮을수록 좋음)
        [0,1] ESG+G Specificity Rate (높을수록 좋음)
        [1,0] Average Token Count
        [1,1] G-Signal Coverage %
    """
    exp_ids = [m["exp_id"] for m in metrics_list]
    bp_rates = [m["tf_bp_rate"] for m in metrics_list]
    esg_g_rates = [m["tf_esg_rate"] + m["tf_g_rate"] for m in metrics_list]
    avg_tokens = [m["avg_token_count"] for m in metrics_list]
    g_pcts = [m["g_signal_pct"] for m in metrics_list]

    colors = {
        "exp_A": "#AAAAAA",
        "exp_B": "#4C72B0",   # 파란색: pre-reg baseline
        "exp_C": "#AAAAAA",
        "exp_D": "#C44E52",   # 빨간색: G-signal 위험
        "exp_E": "#55A868",   # 초록색: 개선 실험
        "exp_F": "#8172B2",   # 보라색: 최적 탐색
    }
    bar_colors = [colors.get(e, "#AAAAAA") for e in exp_ids]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"전처리 실험 품질 평가 (top-{top_n} 기준)", fontsize=14, fontweight="bold")

    def bar_with_labels(ax, values, label, color_list, lower_is_better=False):
        bars = ax.bar(exp_ids, values, color=color_list)
        ax.set_title(label)
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{v:.1f}", ha="center", fontsize=9)
        if lower_is_better:
            ax.set_ylabel("% (낮을수록 좋음)")
        else:
            ax.set_ylabel("% 또는 값 (높을수록 좋음)")

    bar_with_labels(axes[0, 0], bp_rates,
                    f"Boilerplate Contamination Rate\n(top-{top_n} 중 재무/법무 boilerplate %)",
                    bar_colors, lower_is_better=True)

    bar_with_labels(axes[0, 1], esg_g_rates,
                    f"ESG + G Specificity Rate\n(top-{top_n} 중 ESG/G_SIGNAL %)",
                    bar_colors, lower_is_better=False)

    bar_with_labels(axes[1, 0], avg_tokens,
                    "평균 토큰 수\n(너무 낮으면 정보 손실 위험)",
                    bar_colors, lower_is_better=False)

    bar_with_labels(axes[1, 1], g_pcts,
                    "G-Signal Coverage %\n(낮으면 G 피처 소실 위험 ⚠️)",
                    bar_colors, lower_is_better=False)

    # baseline 표시선
    for ax in axes.flat:
        ax.axhline(y=0, color="black", linewidth=0.5)

    # 범례
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#4C72B0", label="exp_B (pre-reg baseline)"),
        Patch(facecolor="#55A868", label="exp_E (BP 감소 실험)"),
        Patch(facecolor="#8172B2", label="exp_F (최적 설정 탐색)"),
        Patch(facecolor="#C44E52", label="exp_D (G-signal 위험 ⚠️)"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=4, fontsize=9)

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"시각화 저장: {out_path}")


# =============================================================================
# 메인 평가 함수
# =============================================================================

def run_evaluation(exp_ids: list = None, top_n: int = 30, save_report: bool = True):
    """
    전처리 평가 메인 함수.

    Args:
        exp_ids: 평가할 실험 목록 (None이면 존재하는 모든 실험)
        top_n:   상위 N개 토큰 기준
        save_report: 결과를 파일로 저장할지 여부
    """
    os.makedirs(config.PREPROC_DIR, exist_ok=True)

    # 사용 가능한 tokenized CSV 탐색
    if exp_ids is None:
        exp_ids = []
        for exp_id in ["exp_A", "exp_B", "exp_C", "exp_D", "exp_E", "exp_F"]:
            csv_path = os.path.join(config.PREPROC_DIR, f"tokenized_{exp_id}.csv")
            if os.path.exists(csv_path):
                exp_ids.append(exp_id)

    if not exp_ids:
        logger.error(
            "평가할 tokenized CSV가 없습니다.\n"
            "먼저 03_preprocess_experiment.py를 실행하세요:\n"
            "  python 03_preprocess_experiment.py --exps exp_B exp_E exp_F"
        )
        return

    logger.info(f"평가 대상: {exp_ids}")

    # 각 실험 메트릭 계산
    metrics_list = []
    all_metrics = {}

    for exp_id in exp_ids:
        csv_path = os.path.join(config.PREPROC_DIR, f"tokenized_{exp_id}.csv")
        if not os.path.exists(csv_path):
            logger.warning(f"파일 없음, 건너뜀: {csv_path}")
            continue

        df = pd.read_csv(csv_path, dtype=str)
        df["token_count"] = pd.to_numeric(df["token_count"], errors="coerce").fillna(0)

        logger.info(f"지표 계산 중: {exp_id} (n={len(df)})")
        m = compute_metrics(exp_id, df, top_n=top_n)
        m["description"] = _get_exp_description(exp_id)
        metrics_list.append(m)
        all_metrics[exp_id] = m

    if not metrics_list:
        logger.error("계산할 지표가 없습니다.")
        return

    # exp_B 대비 Delta 계산
    deltas = []
    baseline_id = "exp_B"
    if baseline_id in all_metrics:
        for exp_id in exp_ids:
            if exp_id != baseline_id and exp_id in all_metrics:
                delta = compute_boilerplate_reduction(
                    all_metrics[baseline_id], all_metrics[exp_id], top_n=top_n
                )
                if delta:
                    deltas.append(delta)

    # 리포트 출력
    report = print_evaluation_report(metrics_list, deltas, top_n=top_n)

    if save_report:
        # 텍스트 리포트 저장
        report_path = os.path.join(config.PREPROC_DIR, "eval_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"텍스트 리포트 저장: {report_path}")

        # CSV 비교 저장
        comp_path = os.path.join(config.PREPROC_DIR, "eval_comparison.csv")
        comp_df = pd.DataFrame(metrics_list)
        comp_df.to_csv(comp_path, index=False, encoding="utf-8-sig")
        logger.info(f"지표 비교 CSV 저장: {comp_path}")

        # Delta CSV 저장
        if deltas:
            delta_path = os.path.join(config.PREPROC_DIR, "eval_delta.csv")
            pd.DataFrame(deltas).to_csv(delta_path, index=False, encoding="utf-8-sig")
            logger.info(f"Delta CSV 저장: {delta_path}")

        # TF-IDF top token 비교 CSV
        tfidf_rows = []
        for m in metrics_list:
            tfidf_tokens = m.get("tfidf_top_n", "").split(" | ")
            for rank, token in enumerate(tfidf_tokens, 1):
                tfidf_rows.append({
                    "exp_id": m["exp_id"],
                    "rank":   rank,
                    "token":  token,
                    "class":  _classify_token(token),
                })
        if tfidf_rows:
            tfidf_path = os.path.join(config.PREPROC_DIR, "eval_tfidf_top.csv")
            pd.DataFrame(tfidf_rows).to_csv(tfidf_path, index=False, encoding="utf-8-sig")
            logger.info(f"TF-IDF top token CSV 저장: {tfidf_path}")

        # 시각화
        if len(metrics_list) > 1:
            plot_path = os.path.join(config.PREPROC_DIR, "eval_comparison.png")
            plot_evaluation(metrics_list, top_n=top_n, out_path=plot_path)

    return metrics_list, deltas


# =============================================================================
# 유틸리티
# =============================================================================

def _classify_token(token: str) -> str:
    """토큰을 G_SIGNAL / ESG_SIGNAL / BOILERPLATE / OTHER로 분류"""
    if token in G_SIGNAL_TOKENS:
        return "G_SIGNAL"
    elif token in ESG_SIGNAL_TOKENS:
        return "ESG_SIGNAL"
    elif token in BOILERPLATE_TOKENS:
        return "BOILERPLATE"
    else:
        return "OTHER"


def _get_exp_description(exp_id: str) -> str:
    desc_map = {
        "exp_A": "minimal | remove_all | no filter",
        "exp_B": "standard | remove_all | no filter [PRE-REG BASELINE]",
        "exp_C": "minimal | keep_quantity | no filter",
        "exp_D": "extended | remove_all | no filter [G-signal 위험]",
        "exp_E": "extended | remove_all | sent-filter | BP 감소",
        "exp_F": "extended | keep_quantity | sent-filter | 최적 설정",
    }
    return desc_map.get(exp_id, "")


# =============================================================================
# CLI 진입점
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="전처리 실험 품질 평가 스크립트"
    )
    parser.add_argument(
        "--exps", nargs="+", default=None,
        help="평가할 실험 ID 목록 (예: --exps exp_B exp_E exp_F). 기본값: 존재하는 모든 실험"
    )
    parser.add_argument(
        "--top_n", type=int, default=30,
        help="상위 N개 토큰 기준으로 평가 (기본값: 30)"
    )
    parser.add_argument(
        "--save_report", action="store_true", default=True,
        help="결과를 CSV/PNG/TXT로 저장 (기본값: True)"
    )
    args = parser.parse_args()

    run_evaluation(
        exp_ids=args.exps,
        top_n=args.top_n,
        save_report=args.save_report,
    )
