import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import logging

def plot_risk_vs_approval(validation_df, out_path='results/risk_vs_approval.png'):
    logger = logging.getLogger(__name__)
    x = validation_df['dili_risk_score'].values
    y = validation_df['approval_rate'].values
    c = validation_df['dili_risk_score'].values
    fig, ax = plt.subplots(figsize=(8, 6))
    if 'target_symbol' not in validation_df.columns:
        validation_df = validation_df.reset_index()
    if np.any(c > 0):
        norm = mpl.colors.LogNorm(vmin=np.min(c[c > 0]), vmax=np.max(c))
    else:
        norm = mpl.colors.Normalize(vmin=np.min(c), vmax=np.max(c))
    cmap = plt.get_cmap('coolwarm')
    sc = ax.scatter(x, y, c=c, cmap=cmap, norm=norm, s=50, edgecolor='k', alpha=0.8)
    ax.set_xscale('log')
    ax.set_xlabel('DILI Risk Score')
    ax.set_ylabel('Approval Rate')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    mags = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
    offsets = [(0, 15), (0, -20), (30, 0), (-30, 0), (0, 25)]
    for i, mag in enumerate(mags):
        idx = (np.abs(x - mag)).argmin()
        row = validation_df.iloc[idx]
        label = row['target_symbol'] if 'target_symbol' in row else str(idx)
        dx, dy = offsets[i % len(offsets)]
        ax.annotate(f"{label}\n({format_sig(row['dili_risk_score'])})",
                    (row['dili_risk_score'], row['approval_rate']),
                    textcoords="offset points", xytext=(dx, dy), ha='center', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", lw=0, alpha=0.8),
                    arrowprops=dict(arrowstyle="->", color="blue", lw=1, alpha=0.7))
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    logger.info(f"Saved risk vs approval plot to {out_path}")

def plot_risk_vs_withdrawal(validation_df, out_path='results/risk_vs_withdrawal.png'):
    logger = logging.getLogger(__name__)
    if 'withdrawal_rate' not in validation_df.columns:
        logger.warning("No withdrawal_rate column in validation_df. Skipping plot.")
        return
    x = validation_df['dili_risk_score'].values
    y = validation_df['withdrawal_rate'].values
    c = validation_df['dili_risk_score'].values
    fig, ax = plt.subplots(figsize=(8, 6))
    if 'target_symbol' not in validation_df.columns:
        validation_df = validation_df.reset_index()
    if np.any(c > 0):
        norm = mpl.colors.LogNorm(vmin=np.min(c[c > 0]), vmax=np.max(c))
    else:
        norm = mpl.colors.Normalize(vmin=np.min(c), vmax=np.max(c))
    cmap = plt.get_cmap('coolwarm')
    sc = ax.scatter(x, y, c=c, cmap=cmap, norm=norm, s=50, edgecolor='k', alpha=0.8)
    ax.set_xscale('log')
    ax.set_xlabel('DILI Risk Score')
    ax.set_ylabel('Withdrawal Rate')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    mags = [1e-4, 1e-3, 1e-2, 1e-1, 1.0]
    offsets = [(0, 15), (0, -20), (30, 0), (-30, 0), (0, 25)]
    for i, mag in enumerate(mags):
        idx = (np.abs(x - mag)).argmin()
        row = validation_df.iloc[idx]
        label = row['target_symbol'] if 'target_symbol' in row else str(idx)
        dx, dy = offsets[i % len(offsets)]
        ax.annotate(f"{label}\n({format_sig(row['dili_risk_score'])})",
                    (row['dili_risk_score'], row['withdrawal_rate']),
                    textcoords="offset points", xytext=(dx, dy), ha='center', fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", lw=0, alpha=0.8),
                    arrowprops=dict(arrowstyle="->", color="blue", lw=1, alpha=0.7))
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    logger.info(f"Saved risk vs withdrawal plot to {out_path}")

def format_sig(x, sig=1):
    if x == 0:
        return "0"
    from math import log10, floor
    return f"{round(x, -int(floor(log10(abs(x)))) + (sig - 1))}" 