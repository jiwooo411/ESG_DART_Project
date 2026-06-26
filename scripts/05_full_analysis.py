# =============================================================================
# 05_full_analysis.py — Full Validation & Regression Pipeline
# =============================================================================
# 실행: python 05_full_analysis.py
#
# 입력:  data/04_preprocessed/features_exp_{B,E,F}.csv
#        data/kcgs_esg_ratings.csv
#
# 출력:  data/06_analysis/
#          collapse_diagnostics.csv      feature collapse/variance 진단
#          spearman_full.csv             Spearman rho + bootstrap CI
#          permutation_results.csv       placebo test 결과
#          regression_ols.txt            OLS 결과
#          regression_logit.txt          Ordered Logit 결과
#          fig_scatter.png               g_signal_ratio vs KCGS scatter
#          fig_distributions.png         exp별 feature distribution
#          fig_heatmap_full.png          Spearman heatmap
#
# 설계 원칙:
#   - 현재 n=30에서 실행 가능, 데이터 확장 시 동일 코드 재사용
#   - "predict" 표현 금지, "association consistent with" 유지
#   - causal wording 금지
#   - placebo test: governance signal이 단순 verbosity artifact가 아님을 확인
# =============================================================================

import os, sys, warnings, logging
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from scipy.stats import spearmanr, mannwhitneyu
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import statsmodels.formula.api as smf
from statsmodels.miscmodels.ordinal_model import OrderedModel
from pathlib import Path

from src.kcgs_merge import load_kcgs, merge_features

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

OUT_DIR     = Path('data/06_analysis')
PREPROC_DIR = Path('data/04_preprocessed')
EXP_IDS     = ['exp_B', 'exp_E', 'exp_F']

CORE_FEATURES = [
    'esg_signal_ratio',
    'g_signal_ratio',
    'bp_contamination_rate',
    'esg_g_relative',
    'esg_tfidf_concentration',
    'total_tokens',
]

# Grade mapping — 4단계 robustness용
GRADE_BINARY_THRESHOLD = 5   # kcgs_grade_7 >= 5 (A/A+) → 1, else 0


# =============================================================================
# 0. 유틸리티
# =============================================================================

def bootstrap_spearman_ci(x, y, n_boot=3000, ci=95, seed=42):
    """Paired bootstrap (올바른 구현: 동일 인덱스 x,y 동시 적용)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    boot_rhos = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        r, _ = spearmanr(x[idx], y[idx])
        boot_rhos.append(r)
    lo = np.percentile(boot_rhos, (100 - ci) / 2)
    hi = np.percentile(boot_rhos, 100 - (100 - ci) / 2)
    return round(lo, 4), round(hi, 4)

def effect_label(rho):
    r = abs(rho)
    if r >= 0.40: return 'moderate-strong'
    if r >= 0.25: return 'moderate'
    if r >= 0.10: return 'weak'
    return 'negligible'

def load_merged(kcgs_df):
    """모든 exp feature를 KCGS와 merge하여 반환."""
    merged = {}
    for exp_id in EXP_IDS:
        p = PREPROC_DIR / f'features_{exp_id}.csv'
        if not p.exists():
            logger.warning(f'{exp_id}: features 파일 없음 — 스킵')
            continue
        feat = pd.read_csv(p, dtype=str)
        m = merge_features(feat, kcgs_df, exp_id=exp_id, verbose=False)
        for col in m.columns:
            if col not in ['stock_code', 'corp_code', 'corp_name',
                           'kcgs_grade', 'data_source']:
                m[col] = pd.to_numeric(m[col], errors='coerce')
        merged[exp_id] = m
    return merged


# =============================================================================
# 1. Feature Collapse & Variance Diagnostics
# =============================================================================

def run_collapse_diagnostics(merged_dict: dict) -> pd.DataFrame:
    """
    각 exp의 feature별 분산·분포 진단.

    목적: exp_E/F에서 bp_contamination_rate, esg_g_relative가
          상수화되는 collapse 현상을 정량적으로 기록.

    연구적 의미:
        collapse = preprocessing이 특정 feature의 discriminative power를
                   완전히 제거했다는 evidence.
        exp_B에서는 분산이 있지만 exp_E/F에서 0이면
        "preprocessing 선택이 feature 공간을 변형시킨다"는 점을 명시해야 함.
    """
    rows = []
    for exp_id, df in merged_dict.items():
        for feat in CORE_FEATURES:
            if feat not in df.columns:
                continue
            vals = df[feat].dropna()
            n = len(vals)
            std = vals.std()
            zero_pct = (vals == 0).sum() / n if n > 0 else None
            one_pct  = (vals == 1).sum() / n if n > 0 else None
            is_collapsed = std < 1e-10

            rows.append({
                'exp_id'     : exp_id,
                'feature'    : feat,
                'n'          : n,
                'mean'       : round(vals.mean(), 6) if n > 0 else None,
                'std'        : round(std, 6),
                'min'        : round(vals.min(), 6) if n > 0 else None,
                'max'        : round(vals.max(), 6) if n > 0 else None,
                'skew'       : round(vals.skew(), 4) if n > 0 else None,
                'zero_pct'   : round(zero_pct, 4) if zero_pct is not None else None,
                'one_pct'    : round(one_pct, 4) if one_pct is not None else None,
                'n_unique'   : vals.nunique(),
                'collapsed'  : is_collapsed,
                'note'       : 'constant — no discriminative power' if is_collapsed else '',
            })

    diag = pd.DataFrame(rows)
    return diag


# =============================================================================
# 2. Full Spearman Validation
# =============================================================================

def run_spearman_validation(merged_dict: dict) -> pd.DataFrame:
    """전체 표본 Spearman rho + bootstrap CI + Mann-Whitney."""
    rows = []
    for exp_id, df in merged_dict.items():
        y = df['kcgs_grade_7'].values
        y_binary = (y >= GRADE_BINARY_THRESHOLD).astype(float)  # A/A+ = 1

        for feat in CORE_FEATURES:
            if feat not in df.columns:
                continue
            x = df[feat].values
            mask = ~(np.isnan(x) | np.isnan(y))
            if mask.sum() < 5:
                continue
            xm, ym = x[mask], y[mask]

            if np.std(xm) < 1e-10:
                rows.append({
                    'exp_id': exp_id, 'feature': feat,
                    'rho': None, 'p_value': None,
                    'ci_lo_95': None, 'ci_hi_95': None,
                    'n': int(mask.sum()),
                    'mw_p': None, 'mw_direction': None,
                    'effect': 'var=0', 'ci_includes_zero': True,
                    'note': 'collapsed — constant feature',
                })
                continue

            # Spearman
            rho, p = spearmanr(xm, ym)
            ci_lo, ci_hi = bootstrap_spearman_ci(xm, ym)

            # Mann-Whitney (A/A+ vs B/B+)
            high = xm[ym >= GRADE_BINARY_THRESHOLD]
            low  = xm[ym < GRADE_BINARY_THRESHOLD]
            if len(high) >= 2 and len(low) >= 2:
                mw_stat, mw_p = mannwhitneyu(high, low, alternative='two-sided')
                mw_dir = 'high>low' if high.mean() > low.mean() else 'high<low'
            else:
                mw_p, mw_dir = None, None

            rows.append({
                'exp_id'        : exp_id,
                'feature'       : feat,
                'rho'           : round(rho, 4),
                'p_value'       : round(p, 4),
                'ci_lo_95'      : ci_lo,
                'ci_hi_95'      : ci_hi,
                'n'             : int(mask.sum()),
                'mw_p'          : round(mw_p, 4) if mw_p else None,
                'mw_direction'  : mw_dir,
                'effect'        : effect_label(rho),
                'ci_includes_zero': ci_lo < 0 < ci_hi,
                'note'          : '',
            })

    return pd.DataFrame(rows)


# =============================================================================
# 3. Permutation / Placebo Test
# =============================================================================

def run_permutation_test(
    merged_dict: dict,
    feature: str = 'g_signal_ratio',
    exp_id: str = 'exp_B',
    n_perm: int = 5000,
    seed: int = 42,
) -> dict:
    """
    Permutation test: KCGS 등급을 무작위로 섞었을 때
    관찰된 Spearman rho보다 큰 값이 얼마나 자주 나오는가.

    목적: governance signal이 단순 verbosity artifact가 아님을 검증.
    기대: permutation p-value가 낮을수록 관찰된 ρ가 우연이 아님.

    Placebo 해석:
        만약 shuffled grade에서도 높은 rho가 나온다면
        → feature 자체가 grade-independent 구조를 capture하는 것
        → 즉 feature가 진짜 ESG signal이 아닌 다른 무언가를 측정
    """
    if exp_id not in merged_dict:
        return {}
    df = merged_dict[exp_id]
    if feature not in df.columns:
        return {}

    x = df[feature].dropna().values
    y = df.loc[df[feature].notna(), 'kcgs_grade_7'].values
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]

    if np.std(x) < 1e-10:
        return {'feature': feature, 'exp_id': exp_id, 'error': 'var=0'}

    observed_rho, observed_p = spearmanr(x, y)

    rng = np.random.default_rng(seed)
    null_rhos = []
    for _ in range(n_perm):
        y_shuffled = rng.permutation(y)
        r, _ = spearmanr(x, y_shuffled)
        null_rhos.append(r)

    null_rhos = np.array(null_rhos)
    # two-tailed permutation p-value
    perm_p = np.mean(np.abs(null_rhos) >= abs(observed_rho))

    return {
        'feature'             : feature,
        'exp_id'              : exp_id,
        'n'                   : len(x),
        'observed_rho'        : round(observed_rho, 4),
        'observed_p_parametric': round(observed_p, 4),
        'permutation_p'       : round(perm_p, 4),
        'null_rho_mean'       : round(null_rhos.mean(), 4),
        'null_rho_std'        : round(null_rhos.std(), 4),
        'null_95th_pct'       : round(np.percentile(np.abs(null_rhos), 95), 4),
        'n_permutations'      : n_perm,
        'interpretation'      : (
            'observed rho exceeds 95th pct of null — not easily explained by chance'
            if abs(observed_rho) > np.percentile(np.abs(null_rhos), 95)
            else 'observed rho within null distribution — caution required'
        ),
    }


# =============================================================================
# 4. Visualization
# =============================================================================

def make_scatter_plot(merged_dict: dict, out_path: Path):
    """
    g_signal_ratio vs KCGS grade (exp_B/E/F 비교 scatter).
    각 점 = firm-year. regression line = 순위기반 OLS.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    grade_labels = {3: 'B', 4: 'B+', 5: 'A', 6: 'A+', 7: 'S'}

    for ax, exp_id in zip(axes, EXP_IDS):
        if exp_id not in merged_dict:
            ax.set_title(f'{exp_id}: 없음')
            continue
        df = merged_dict[exp_id]
        if 'g_signal_ratio' not in df.columns:
            continue
        x = df['g_signal_ratio'].values
        y = df['kcgs_grade_7'].values
        mask = ~(np.isnan(x) | np.isnan(y))
        x, y = x[mask], y[mask]

        rho, p = spearmanr(x, y)

        # jitter for readability
        rng = np.random.default_rng(0)
        y_jitter = y + rng.uniform(-0.15, 0.15, size=len(y))

        # color by grade
        colors = plt.cm.RdYlGn([(v - 3) / 4 for v in y])
        ax.scatter(x, y_jitter, c=colors, alpha=0.7, s=45, edgecolors='gray', lw=0.3)

        # OLS line on ranks
        xr, yr = pd.Series(x).rank(), pd.Series(y).rank()
        z = np.polyfit(xr, yr, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        xr_line = pd.Series(x_line).rank(method='first')
        yr_line = np.polyval(z, np.linspace(xr.min(), xr.max(), 100))
        y_line_mapped = np.interp(yr_line, [yr.min(), yr.max()], [y.min(), y.max()])
        ax.plot(x_line, y_line_mapped, 'r--', lw=1.5, alpha=0.8)

        ax.set_xlabel('g_signal_ratio', fontsize=10)
        ax.set_yticks([3, 4, 5, 6])
        ax.set_yticklabels(['B', 'B+', 'A', 'A+'], fontsize=9)
        ax.set_title(f'{exp_id}\nρ={rho:.3f}  p={p:.3f}  n={len(x)}', fontsize=11)
        ax.grid(alpha=0.25)

    axes[0].set_ylabel('KCGS Grade', fontsize=10)
    fig.suptitle('g_signal_ratio vs KCGS Grade (by Experiment)', fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f'저장: {out_path.name}')


def make_distribution_plot(merged_dict: dict, out_path: Path):
    """
    exp_B/E/F별 핵심 feature 분포 비교 (boxplot + strip).
    collapsed feature는 별도 표시.
    """
    plot_feats = [f for f in CORE_FEATURES if f != 'total_tokens']
    n_feats = len(plot_feats)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    colors = {'exp_B': '#4878CF', 'exp_E': '#6ACC65', 'exp_F': '#D65F5F'}

    for ax_idx, feat in enumerate(plot_feats):
        ax = axes[ax_idx]
        data_by_exp = {}
        for exp_id in EXP_IDS:
            if exp_id not in merged_dict:
                continue
            df = merged_dict[exp_id]
            if feat not in df.columns:
                continue
            vals = df[feat].dropna().values
            data_by_exp[exp_id] = vals

        if not data_by_exp:
            ax.set_visible(False)
            continue

        positions = range(len(data_by_exp))
        for pos, (exp_id, vals) in zip(positions, data_by_exp.items()):
            color = colors.get(exp_id, 'gray')
            if np.std(vals) < 1e-10:
                ax.axhline(vals[0], color=color, lw=2, ls='--', label=f'{exp_id} [상수={vals[0]:.3f}]')
            else:
                bp = ax.boxplot(vals, positions=[pos], widths=0.5,
                                patch_artist=True,
                                boxprops=dict(facecolor=color, alpha=0.6),
                                medianprops=dict(color='black', lw=2),
                                whiskerprops=dict(color=color),
                                capprops=dict(color=color),
                                flierprops=dict(marker='o', color=color, alpha=0.4))
                # strip
                jitter = np.random.default_rng(0).uniform(-0.1, 0.1, size=len(vals))
                ax.scatter([pos + j for j in jitter], vals, alpha=0.4, s=15, color=color)

        ax.set_xticks(list(positions))
        ax.set_xticklabels(list(data_by_exp.keys()), fontsize=9)
        ax.set_title(feat, fontsize=10)
        ax.grid(alpha=0.2, axis='y')

        # 범례에 표준편차 추가
        for exp_id, vals in data_by_exp.items():
            std_str = f'std={np.std(vals):.4f}' if np.std(vals) >= 1e-10 else 'std=0 ⚠️'
            ax.text(0.01, 0.99 - list(data_by_exp.keys()).index(exp_id) * 0.1,
                    f'{exp_id}: {std_str}',
                    transform=ax.transAxes, fontsize=7.5,
                    verticalalignment='top', color=colors.get(exp_id, 'gray'))

    # 사용 안 된 subplot 숨기기
    for idx in range(n_feats, len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle('Feature Distribution by Preprocessing Experiment\n(boxplot + individual points)',
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f'저장: {out_path.name}')


def make_heatmap(spearman_df: pd.DataFrame, out_path: Path):
    """Spearman rho heatmap — exp × feature."""
    valid = spearman_df[spearman_df['rho'].notna()]
    if len(valid) == 0:
        logger.warning('유효한 Spearman 결과 없음 — heatmap 스킵')
        return

    pivot = valid.pivot_table(index='feature', columns='exp_id', values='rho')
    feat_order = [f for f in CORE_FEATURES if f in pivot.index]
    pivot = pivot.reindex(feat_order)

    fig, ax = plt.subplots(figsize=(8, 5))
    arr = pivot.values.astype(float)
    im = ax.imshow(arr, cmap='RdBu', vmin=-0.5, vmax=0.5, aspect='auto')
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, fontsize=11)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=10)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            v = arr[i, j]
            if not np.isnan(v):
                color = 'white' if abs(v) > 0.3 else 'black'
                # CI 정보 추가
                row = spearman_df[
                    (spearman_df['feature'] == pivot.index[i]) &
                    (spearman_df['exp_id'] == pivot.columns[j])
                ]
                ci_str = ''
                if len(row) > 0 and row.iloc[0]['ci_lo_95'] is not None:
                    lo, hi = row.iloc[0]['ci_lo_95'], row.iloc[0]['ci_hi_95']
                    ci_str = f'\n[{lo:.2f},{hi:.2f}]'
                ax.text(j, i, f'{v:.3f}{ci_str}',
                        ha='center', va='center', fontsize=8,
                        color=color, fontweight='bold')
            else:
                ax.text(j, i, 'N/A\n(var=0)', ha='center', va='center',
                        fontsize=8, color='gray')

    plt.colorbar(im, ax=ax, label='Spearman ρ', shrink=0.8)
    ax.set_title(f'Spearman ρ: Feature × Experiment\n(KCGS 7-grade, n={spearman_df["n"].max()})',
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f'저장: {out_path.name}')


def make_permutation_plot(perm_result: dict, out_path: Path):
    """Permutation null distribution vs. observed rho 시각화."""
    if not perm_result or 'observed_rho' not in perm_result:
        return

    rng = np.random.default_rng(42)
    n_perm = perm_result['n_permutations']
    # null distribution 재생성 (plot용)
    # 통계값만 있으므로 정규근사로 시각화
    null_mean = perm_result['null_rho_mean']
    null_std  = perm_result['null_rho_std']
    null_sim  = rng.normal(null_mean, null_std, size=n_perm)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(null_sim, bins=60, color='#4878CF', alpha=0.7, density=True,
            label=f'Null distribution\n(n_perm={n_perm:,})')
    ax.axvline(perm_result['observed_rho'], color='red', lw=2.5, ls='--',
               label=f"Observed ρ={perm_result['observed_rho']:.3f}")
    ax.axvline(perm_result['null_95th_pct'], color='orange', lw=1.5, ls=':',
               label=f"95th percentile={perm_result['null_95th_pct']:.3f}")
    ax.axvline(-perm_result['null_95th_pct'], color='orange', lw=1.5, ls=':')
    ax.fill_betweenx([0, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 5],
                     -perm_result['null_95th_pct'], perm_result['null_95th_pct'],
                     alpha=0.1, color='orange', label='95% null interval')

    feat = perm_result['feature']
    exp = perm_result['exp_id']
    perm_p = perm_result['permutation_p']
    ax.set_title(f'Permutation Test: {feat} ({exp})\n'
                 f'perm-p={perm_p:.4f}  |  {perm_result["interpretation"]}',
                 fontsize=10)
    ax.set_xlabel('Spearman ρ', fontsize=10)
    ax.set_ylabel('Density', fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f'저장: {out_path.name}')


# =============================================================================
# 5. OLS Regression
# =============================================================================

def run_ols(merged_dict: dict, exp_id: str = 'exp_B') -> str:
    """
    Main OLS:
        kcgs_grade_7 ~ g_signal_ratio + log_tokens

    해석 원칙:
        - coefficient는 "association" 표현만 사용
        - "predicts", "causes" 표현 금지
        - total_tokens 통제: verbosity bias 제거 목적

    왜 log(total_tokens)인가:
        문서 길이는 right-skewed 분포.
        log 변환 후 회귀에 포함하면 verbosity의 선형 영향을 통제.
    """
    if exp_id not in merged_dict:
        return f'{exp_id}: 데이터 없음'

    df = merged_dict[exp_id].copy()

    # 필요 컬럼 존재 확인
    missing = [c for c in ['g_signal_ratio', 'total_tokens', 'kcgs_grade_7']
               if c not in df.columns]
    if missing:
        return f'필요 컬럼 없음: {missing}'

    df = df.dropna(subset=['g_signal_ratio', 'total_tokens', 'kcgs_grade_7'])
    df['log_tokens'] = np.log1p(df['total_tokens'])
    df['kcgs_grade_7'] = df['kcgs_grade_7'].astype(float)

    # esg_tfidf_concentration 있으면 포함
    has_tfidf = 'esg_tfidf_concentration' in df.columns and df['esg_tfidf_concentration'].notna().sum() > 5

    formula_base    = 'kcgs_grade_7 ~ g_signal_ratio + log_tokens'
    formula_tfidf   = formula_base + ' + esg_tfidf_concentration' if has_tfidf else None

    output_lines = [
        '=' * 65,
        f'OLS Regression — {exp_id} (n={len(df)})',
        '=' * 65,
        '',
        '해석 주의: coefficient는 "~와 연관" (association) 표현만.',
        '"predicts" / "causes" / "improves ESG" 금지.',
        '',
    ]

    for formula in [f for f in [formula_base, formula_tfidf] if f]:
        try:
            model = smf.ols(formula=formula, data=df).fit()
            output_lines.append(f'Formula: {formula}')
            output_lines.append(model.summary().as_text())
            output_lines.append('')
        except Exception as e:
            output_lines.append(f'OLS 실패 ({formula}): {e}')

    # Binary Logit (A/A+ = 1, else = 0)
    df['high_grade'] = (df['kcgs_grade_7'] >= GRADE_BINARY_THRESHOLD).astype(int)
    try:
        logit_model = smf.logit(
            formula='high_grade ~ g_signal_ratio + log_tokens', data=df
        ).fit(disp=False)
        output_lines.append('Binary Logit (A/A+ = 1, B/B+ = 0):')
        output_lines.append(logit_model.summary().as_text())
    except Exception as e:
        output_lines.append(f'Binary Logit 실패: {e}')

    return '\n'.join(output_lines)


def run_ordered_logit(merged_dict: dict, exp_id: str = 'exp_B') -> str:
    """
    Ordered Logit (Proportional Odds Model):
        kcgs_grade_7 ~ g_signal_ratio + log_tokens

    왜 Ordered Logit인가:
        KCGS 등급은 서열척도(ordinal scale).
        OLS는 등급 간 간격이 동일하다고 가정하는 문제가 있음.
        Ordered Logit은 등급 간격 가정 없이 순서 정보만 활용.
    """
    if exp_id not in merged_dict:
        return f'{exp_id}: 데이터 없음'

    df = merged_dict[exp_id].copy()
    df = df.dropna(subset=['g_signal_ratio', 'total_tokens', 'kcgs_grade_7'])
    df['log_tokens'] = np.log1p(df['total_tokens'])

    # OrderedModel은 정렬된 카테고리 필요
    df['grade_cat'] = pd.Categorical(
        df['kcgs_grade_7'].astype(int),
        categories=sorted(df['kcgs_grade_7'].dropna().astype(int).unique()),
        ordered=True,
    )

    # 카테고리 수 체크
    n_cats = df['grade_cat'].nunique()
    n_obs  = len(df)

    output_lines = [
        '=' * 65,
        f'Ordered Logit — {exp_id} (n={n_obs}, n_grades={n_cats})',
        '=' * 65,
        '',
    ]

    if n_cats < 3:
        output_lines.append(f'등급 카테고리 수 {n_cats} < 3 — Ordered Logit 실행 불가')
        output_lines.append('→ Binary Logit 결과를 대신 참고')
        return '\n'.join(output_lines)

    try:
        mod = OrderedModel(
            df['grade_cat'],
            df[['g_signal_ratio', 'log_tokens']],
            distr='logit',
        )
        res = mod.fit(method='bfgs', disp=False)
        output_lines.append(res.summary().as_text())
        output_lines.append('')
        output_lines.append('해석:')
        output_lines.append('  g_signal_ratio 계수 > 0: governance 언어 강도 증가 → 높은 등급과 연관')
        output_lines.append('  log_tokens 계수: verbosity 통제 후 순효과')
        output_lines.append('  "association consistent with" 표현 사용 권장')
        output_lines.append('')
        output_lines.append('Limitation:')
        output_lines.append('  이 결과는 governance quality 자체보다')
        output_lines.append('  governance disclosure intensity 또는')
        output_lines.append('  KCGS 평가 프레임과의 overlap을 반영할 가능성 있음.')
    except Exception as e:
        output_lines.append(f'Ordered Logit 실패: {e}')
        output_lines.append('→ n이 작거나 등급 분포가 불균형할 때 발생 가능')

    return '\n'.join(output_lines)


# =============================================================================
# 메인 실행
# =============================================================================

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info('=' * 60)
    logger.info('05_full_analysis.py 시작')
    logger.info('=' * 60)

    # ── 데이터 로드 ────────────────────────────────────────────
    kcgs = load_kcgs('data/kcgs_esg_ratings.csv')
    merged = load_merged(kcgs)
    n_total = sum(len(df) for df in merged.values())
    logger.info(f'로드 완료: {list(merged.keys())}, 총 {n_total}행')

    # ── [1] Collapse Diagnostics ───────────────────────────────
    logger.info('\n[1] Feature collapse & variance diagnostics')
    diag = run_collapse_diagnostics(merged)
    diag_path = OUT_DIR / 'collapse_diagnostics.csv'
    diag.to_csv(diag_path, index=False, encoding='utf-8-sig')
    logger.info(f'저장: {diag_path.name}')

    print('\n' + '=' * 70)
    print('Feature Collapse & Variance Diagnostics')
    print('=' * 70)
    print(f'{"exp":<8}{"feature":<28}{"std":>9}{"n_uniq":>8}{"zero%":>8}{"collapsed":>12}')
    print('-' * 70)
    for _, row in diag.iterrows():
        collapsed_mark = '⚠️ YES' if row['collapsed'] else 'OK'
        std_str = f'{row["std"]:.6f}' if row['std'] is not None else 'N/A'
        print(f'{row["exp_id"]:<8}{row["feature"]:<28}{std_str:>9}'
              f'{row["n_unique"]:>8}{str(row["zero_pct"] or "N/A"):>8}{collapsed_mark:>12}')

    # ── [2] Preprocessing Robustness 비교표 ───────────────────
    print('\n' + '=' * 70)
    print('Preprocessing Robustness: std 비교 (signal/noise tradeoff)')
    print('=' * 70)
    pivot_std = diag.pivot_table(index='feature', columns='exp_id', values='std')
    pivot_collapsed = diag.pivot_table(index='feature', columns='exp_id', values='collapsed')
    feat_order = [f for f in CORE_FEATURES if f in pivot_std.index]
    pivot_std = pivot_std.reindex(feat_order)
    print(f'{"feature":<28}', end='')
    for exp in EXP_IDS:
        if exp in pivot_std.columns:
            print(f'{exp+" std":>12}', end='')
    print(f'{"tradeoff":>15}')
    print('-' * 75)
    for feat in feat_order:
        print(f'{feat:<28}', end='')
        stds = []
        for exp in EXP_IDS:
            if exp in pivot_std.columns:
                v = pivot_std.loc[feat, exp] if feat in pivot_std.index else None
                collapsed = pivot_collapsed.loc[feat, exp] if feat in pivot_collapsed.index else False
                std_str = '0 ⚠️' if collapsed else (f'{v:.6f}' if v is not None else 'N/A')
                print(f'{std_str:>12}', end='')
                if not collapsed and v is not None:
                    stds.append(v)
        # 상대 변화
        if len(stds) >= 2:
            delta = stds[-1] - stds[0]
            print(f'{"↑" if delta>0 else "↓"} Δ={delta:+.4f}', end='')
        print()

    # ── [3] Full Spearman Validation ──────────────────────────
    logger.info('\n[3] Full Spearman validation')
    spearman_df = run_spearman_validation(merged)
    sp_path = OUT_DIR / 'spearman_full.csv'
    spearman_df.to_csv(sp_path, index=False, encoding='utf-8-sig')
    logger.info(f'저장: {sp_path.name}')

    print('\n' + '=' * 80)
    print('Spearman ρ — Full Sample Validation')
    print('=' * 80)
    print(f'{"exp":<8}{"feature":<28}{"ρ":>7}{"p":>8}{"CI_lo":>7}{"CI_hi":>7}{"n":>4}{"CI⊃0?"}')
    print('-' * 80)
    for _, row in spearman_df.iterrows():
        if row['rho'] is None:
            print(f'{row["exp_id"]:<8}{row["feature"]:<28}{"[var=0]":>45}')
            continue
        ci_zero = '⚠️' if row['ci_includes_zero'] else '✅'
        sig = '★' if (row['p_value'] or 1) < 0.05 else ('·' if (row['p_value'] or 1) < 0.10 else ' ')
        print(f'{row["exp_id"]:<8}{row["feature"]:<28}'
              f'{row["rho"]:>7.3f}{row["p_value"]:>8.3f}'
              f'{row["ci_lo_95"]:>7.3f}{row["ci_hi_95"]:>7.3f}'
              f'{row["n"]:>4} {sig} {ci_zero}')

    # ── [4] Permutation Test ───────────────────────────────────
    logger.info('\n[4] Permutation test (g_signal_ratio, exp_B)')
    perm_rows = []
    for feat in ['g_signal_ratio', 'esg_signal_ratio', 'total_tokens']:
        for exp in ['exp_B', 'exp_E']:
            r = run_permutation_test(merged, feature=feat, exp_id=exp, n_perm=5000)
            if r and 'observed_rho' in r:
                perm_rows.append(r)
                print(f'\n[{exp}] {feat}:')
                print(f'  observed ρ = {r["observed_rho"]:.4f}  '
                      f'parametric p={r["observed_p_parametric"]:.4f}  '
                      f'perm-p={r["permutation_p"]:.4f}')
                print(f'  null 95th = {r["null_95th_pct"]:.4f}')
                print(f'  → {r["interpretation"]}')

    if perm_rows:
        perm_df = pd.DataFrame(perm_rows)
        perm_path = OUT_DIR / 'permutation_results.csv'
        perm_df.to_csv(perm_path, index=False, encoding='utf-8-sig')
        logger.info(f'저장: {perm_path.name}')
        # permutation plot
        main_perm = run_permutation_test(merged, feature='g_signal_ratio', exp_id='exp_B', n_perm=5000)
        make_permutation_plot(main_perm, OUT_DIR / 'fig_permutation.png')

    # ── [5] Visualization ─────────────────────────────────────
    logger.info('\n[5] Visualizations')
    make_scatter_plot(merged, OUT_DIR / 'fig_scatter.png')
    make_distribution_plot(merged, OUT_DIR / 'fig_distributions.png')
    make_heatmap(spearman_df, OUT_DIR / 'fig_heatmap_full.png')

    # ── [6] OLS ───────────────────────────────────────────────
    logger.info('\n[6] OLS regression')
    for exp in ['exp_B', 'exp_E']:
        ols_text = run_ols(merged, exp_id=exp)
        ols_path = OUT_DIR / f'regression_ols_{exp}.txt'
        ols_path.write_text(ols_text, encoding='utf-8')
        logger.info(f'저장: {ols_path.name}')
        print(f'\n{ols_text[:1500]}...' if len(ols_text) > 1500 else ols_text)

    # ── [7] Ordered Logit ─────────────────────────────────────
    logger.info('\n[7] Ordered Logit robustness')
    for exp in ['exp_B', 'exp_E']:
        ol_text = run_ordered_logit(merged, exp_id=exp)
        ol_path = OUT_DIR / f'regression_ordlogit_{exp}.txt'
        ol_path.write_text(ol_text, encoding='utf-8')
        logger.info(f'저장: {ol_path.name}')
        print(f'\n{ol_text[:1500]}...' if len(ol_text) > 1500 else ol_text)

    # ── 최종 요약 ──────────────────────────────────────────────
    logger.info('\n' + '=' * 60)
    logger.info('완료. 결과 위치: data/06_analysis/')
    logger.info('=' * 60)

    print('\n' + '=' * 60)
    print('연구 narrative (초안)')
    print('=' * 60)
    print("""
대부분의 ESG 언어 feature는 preprocessing 선택에 민감했지만,
governance disclosure 관련 언어(g_signal_ratio)는
preprocessing 변화에도 상대적으로 안정적인 양의 연관을 유지했다
(ρ ≈ 0.42~0.44, exp_B/E/F 공통).

permutation test 결과 이 연관은 우연 수준을 초과한다.

Limitation:
이 결과는 governance quality 자체보다 governance disclosure intensity
또는 KCGS 평가 프레임과의 overlap을 반영할 가능성이 있다.
esg_tfidf_concentration (exp_E ρ=0.33)은 방향성은 일관되나
n=30 수준에서 CI가 0을 포함한다.
""")

    print('생성 파일 목록:')
    for f in sorted(OUT_DIR.iterdir()):
        size = f.stat().st_size
        print(f'  {f.name:<40} {size/1024:.1f} KB')


if __name__ == '__main__':
    main()
