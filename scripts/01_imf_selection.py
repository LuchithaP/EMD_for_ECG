"""
Step 1, Sec. III-A: which IMFs should each noise's adaptive filter work on?

The paper filters the sum of different IMF combinations with the simplified structure of
Fig. 2 and keeps the one with the best SNRimp: PLI -> IMF1, BW -> IMF5~8, EM -> IMF3~8,
MA -> the whole signal (no EMD). We repeat this for each noise alone: every contiguous
range IMFi~IMFj (1 <= i <= j <= 8) and the whole signal, each with its best LMS setting,
on the held-out tuning cases. The methods (Eqs. 1-3) always use the paper's choice; this
step only checks it.

    python scripts/01_imf_selection.py

Writes results/imf_selection.csv and
results/figures/imf_selection_snr_imp_per_imf_range.png,
results/figures/emd_imfs_and_spectra_of_noisy_ecg.png.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from src.config import (N_IMFS, NOISE_IMFS, TUNE_NOISE_START, TUNE_RECORDS, TUNE_SNRS)
from src.data import ALL_NOISES
from src.filters import diverged
from src.methods import FilterBank, fig2
from src.metrics import snr_imp
from src.plots import amplitude_spectrum, plt, save
from src.tuning import grid
from src.utils import load_case, run_parallel, save_table

RANGES = [(i, j) for i in range(1, N_IMFS + 1) for j in range(i, N_IMFS + 1)] + [None]
SETTINGS = grid("LMS")


def range_name(imf_range):
    if imf_range is None:
        return "no EMD"
    i, j = imf_range
    return f"IMF{i}" if i == j else f"IMF{i}~{j}"


def score_case(job):
    """SNRimp of every (IMF range, LMS setting) for one noise alone on one case."""
    noise, record, snr = job
    case, imfs, r = load_case(record, (noise,), snr, TUNE_NOISE_START)
    scores = np.full((len(RANGES), len(SETTINGS)), np.nan)
    for a, imf_range in enumerate(RANGES):
        for b, setting in enumerate(SETTINGS):
            f = FilterBank("LMS", case["refs"], {noise: setting})
            y = fig2(case["noisy"], imfs, r, imf_range, f, noise)
            if not diverged(case["noisy"], y):
                scores[a, b] = snr_imp(case["clean"], case["noisy"], y)
    return noise, scores


def best_per_range(results):
    """For each noise and IMF range: the LMS setting with the best mean SNRimp over the cases."""
    rows = []
    for noise in ALL_NOISES:
        stack = np.stack([s for n, s in results if n == noise])  # cases x ranges x settings
        mean = stack.mean(axis=0)  # NaN if the setting diverged in any case
        for a, imf_range in enumerate(RANGES):
            b = int(np.nanargmax(mean[a]))
            rows.append({"noise": noise, "imfs": range_name(imf_range),
                         "first": imf_range[0] if imf_range else 0,
                         "last": imf_range[1] if imf_range else 0,
                         **SETTINGS[b], "mean_SNRimp_dB": mean[a, b],
                         "paper_choice": imf_range == NOISE_IMFS[noise]})
    return pd.DataFrame(rows)


def plot_heatmaps(df):
    fig, axes = plt.subplots(1, 4, figsize=(20, 5), constrained_layout=True)
    for ax, noise in zip(axes, ALL_NOISES):
        d = df[df.noise == noise]
        table = np.full((N_IMFS, N_IMFS), np.nan)
        for _, row in d[d.first > 0].iterrows():
            table[row["last"] - 1, row["first"] - 1] = row.mean_SNRimp_dB
        im = ax.imshow(table, origin="lower", cmap="viridis")
        for (i, j), v in np.ndenumerate(table):
            if np.isfinite(v):
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=7, color="w")
        best = d.loc[d.mean_SNRimp_dB.idxmax()]
        paper = NOISE_IMFS[noise]
        if paper:
            ax.add_patch(plt.Rectangle((paper[0] - 1.5, paper[1] - 1.5), 1, 1, fill=False,
                                       ec="red", lw=2.5))
        no_emd = d[d.imfs == "no EMD"].mean_SNRimp_dB.iloc[0]
        ax.set_title(f"{noise.upper()}: best ours = {best.imfs} ({best.mean_SNRimp_dB:.1f} dB)\n"
                     f"paper = {range_name(paper)} (red box); no EMD: {no_emd:.1f} dB")
        ax.set_xticks(range(N_IMFS), range(1, N_IMFS + 1))
        ax.set_yticks(range(N_IMFS), range(1, N_IMFS + 1))
        ax.set_xlabel("first IMF")
        ax.set_ylabel("last IMF")
        fig.colorbar(im, ax=ax, shrink=0.8, label="mean SNRimp (dB)")
    fig.suptitle("Sec. III-A: SNRimp of an LMS filter on IMFi~IMFj, each noise alone "
                 f"(held-out records {TUNE_RECORDS}, SNRin {TUNE_SNRS} dB)")
    save(fig, "imf_selection_snr_imp_per_imf_range.png")


def plot_imfs(record=TUNE_RECORDS[0], snr=0):
    """IMFs of one noisy ECG (all four noises) and their spectra."""
    case, imfs, r = load_case(record, ALL_NOISES, snr, TUNE_NOISE_START)
    rows = [("noisy ECG", case["noisy"])] + [(f"IMF{k + 1}", imfs[k]) for k in range(N_IMFS)]
    rows.append(("residue r", r))
    fig, axes = plt.subplots(len(rows), 2, figsize=(15, 16), constrained_layout=True,
                             gridspec_kw={"width_ratios": [2, 1]})
    for (label, x), (ax_t, ax_f) in zip(rows, axes):
        ax_t.plot(x[:5000], lw=0.6)
        ax_t.set_ylabel(label, rotation=0, ha="right")
        f, a = amplitude_spectrum(x)
        ax_f.semilogx(f[1:], a[1:], lw=0.6)
        ax_f.set_xlim(0.05, 180)
    axes[-1, 0].set_xlabel("sample")
    axes[-1, 1].set_xlabel("f (Hz)")
    fig.suptitle(f"EMD of record {record} + BW + EM + MA + PLI at SNRin {snr} dB "
                 "(left: first 5000 samples, right: amplitude spectrum)")
    save(fig, "emd_imfs_and_spectra_of_noisy_ecg.png")


if __name__ == "__main__":
    jobs = [(noise, rec, snr) for noise in ALL_NOISES for rec in TUNE_RECORDS for snr in TUNE_SNRS]
    print(f"IMF selection: {len(RANGES)} inputs x {len(SETTINGS)} LMS settings on {len(jobs)} cases")
    df = save_table(best_per_range(run_parallel(score_case, jobs)), "imf_selection.csv")
    plot_heatmaps(df)
    plot_imfs()

    best = df.loc[df.groupby("noise").mean_SNRimp_dB.idxmax()].set_index("noise")
    paper = df[df.paper_choice].set_index("noise")
    print("\nBest input per noise (mean SNRimp, dB):")
    for noise in ALL_NOISES:
        print(f"  {noise.upper():4s} ours: {best.loc[noise, 'imfs']:8s} {best.loc[noise, 'mean_SNRimp_dB']:5.1f}"
              f"   paper's choice {range_name(NOISE_IMFS[noise]):8s} {paper.loc[noise, 'mean_SNRimp_dB']:5.1f}")
