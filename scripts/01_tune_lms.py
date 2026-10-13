"""
Step 1: find the optimum LMS step size (mu) and number of taps for every adaptive filter.

Each noise has its own filter, and each filter is tuned on its own (Fig. 2 structure):
- "emd" filters work on the paper's IMFs (Sec. III-A): PLI on IMF1, BW on IMF5-8,
  EM on IMF3-8. Used by Eq. (1), PEAF and SEAF.
- "direct" filters work on the whole signal: PLI, BW, EM, MA, and "all" (all four noises
  as one, with the summed reference). Used by the MA stage of PEAF/SEAF, by SDAF, PDAF
  and the no-EMD baseline.

Tuning data are held out from the paper's tests: other MIT-BIH records (TUNE_RECORDS)
and another part of the noise records (TUNE_NOISE_START), at SNRin = TUNE_SNRS.
For every filter the chosen setting has the highest mean SNRimp over all tuning cases,
among the settings that never diverge. Done separately for each ECG mode (raw / norm).

    python scripts/01_tune_lms.py

Writes results/lms_tuning.csv, results/lms_params.json and results/figures/lms_tuning_*.png.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import (ECG_MODES, FIGURES_DIR, LMS_MUS, LMS_PARAMS_FILE, LMS_TAPS,
                        PAPER_IMFS, RESULTS_DIR, TUNE_SNRS)
from src.data import make_case
from src.emd import decompose
from src.filters import diverged
from src.methods import fig2, make_filter
from src.metrics import snr_imp
from src.utils import run_parallel, save_table, tuning_cases

# (input, noise) of every filter that is tuned
FILTERS = [("emd", "pli"), ("emd", "bw"), ("emd", "em"), ("direct", "all"),
           ("direct", "pli"), ("direct", "bw"), ("direct", "em"), ("direct", "ma")]


def tune_case(case):
    """SNRimp of every (mu, taps) for the filters of one tuning case."""
    record, noises, snr, mode, _ = case
    c = make_case(*case)
    noise = noises[0] if len(noises) == 1 else "all"

    inputs = {"direct": None}
    if noise != "all" and PAPER_IMFS[noise] is not None:
        inputs["emd"] = PAPER_IMFS[noise]
        imfs, r = decompose(c["noisy"])
    else:
        imfs, r = None, None

    rows = []
    for inp, imf_range in inputs.items():
        for mu in LMS_MUS:
            for taps in LMS_TAPS:
                f = make_filter(c["refs"], {noise: {"mu": mu, "taps": taps}})
                y = fig2(c["noisy"], imfs, r, imf_range, f, noise)
                score = np.nan if diverged(c["noisy"], y) else snr_imp(c["clean"], c["noisy"], y)
                rows.append((mode, inp, noise, record, snr, mu, taps, score))
    return rows


def mean_if_stable(scores):
    """Mean SNRimp per setting; NaN if the setting diverged in any case."""
    return scores.mean().where(scores.count() == scores.size())


def choose(df):
    """{mode: {input: {noise: {"mu", "taps"}}}}, and a summary of each choice."""
    params, summary = {}, []
    for (mode, inp, noise), g in df.groupby(["ecg", "input", "noise"]):
        mu, taps = mean_if_stable(g.groupby(["mu", "taps"]).SNRimp_dB).idxmax()
        params.setdefault(mode, {}).setdefault(inp, {})[noise] = {"mu": mu, "taps": int(taps)}

        chosen = g[(g.mu == mu) & (g.taps == taps)]
        chosen_per_snr = chosen.groupby("SNRin_dB").SNRimp_dB.mean()
        best_per_snr = g.groupby(["SNRin_dB", "mu", "taps"]).SNRimp_dB.mean().groupby("SNRin_dB").max()
        summary.append({"ecg": mode, "input": inp, "noise": noise, "mu": mu, "taps": int(taps),
                        "mean_SNRimp_dB": round(chosen.SNRimp_dB.mean(), 2),
                        "worst_SNRimp_dB": round(chosen.SNRimp_dB.min(), 2),
                        "max_loss_vs_best_per_SNR_dB": round((best_per_snr - chosen_per_snr).max(), 2)})
    return params, pd.DataFrame(summary)


def plot_heatmaps(df, params, mode):
    fig, axes = plt.subplots(2, 4, figsize=(18, 8), constrained_layout=True)
    for ax, (inp, noise) in zip(axes.flat, FILTERS):
        g = df[(df.ecg == mode) & (df.input == inp) & (df.noise == noise)]
        table = mean_if_stable(g.groupby(["taps", "mu"]).SNRimp_dB).unstack()
        im = ax.imshow(table.values, origin="lower", aspect="auto", cmap="viridis")
        ax.set_xticks(range(len(table.columns)), [f"{m:g}" for m in table.columns], rotation=45)
        ax.set_yticks(range(len(table.index)), table.index)
        for i in range(table.shape[0]):
            for j in range(table.shape[1]):
                v = table.values[i, j]
                ax.text(j, i, "div" if np.isnan(v) else f"{v:.1f}", ha="center", va="center",
                        fontsize=7, color="w")
        p = params[mode][inp][noise]
        ax.add_patch(plt.Rectangle((list(table.columns).index(p["mu"]) - 0.5,
                                    list(table.index).index(p["taps"]) - 0.5), 1, 1,
                                   fill=False, ec="red", lw=2))
        ax.set_title(f"{noise.upper()} filter, {inp} input")
        ax.set_xlabel("mu (reference at unit power)")
        ax.set_ylabel("taps")
        fig.colorbar(im, ax=ax, label="mean SNRimp (dB)")
    fig.suptitle(f"LMS tuning, ECG {mode}: mean SNRimp over held-out cases (red = chosen)")
    fig.savefig(FIGURES_DIR / f"lms_tuning_{mode}.png", dpi=120)
    plt.close(fig)


def plot_vs_snr(df, params, mode):
    """SNRimp vs mu at the chosen taps, one line per SNRin: how the optimum moves with SNR."""
    fig, axes = plt.subplots(2, 4, figsize=(18, 8), constrained_layout=True)
    for ax, (inp, noise) in zip(axes.flat, FILTERS):
        p = params[mode][inp][noise]
        g = df[(df.ecg == mode) & (df.input == inp) & (df.noise == noise) & (df.taps == p["taps"])]
        for snr in TUNE_SNRS:
            line = g[g.SNRin_dB == snr].groupby("mu").SNRimp_dB.mean()
            ax.semilogx(line.index, line.values, "o-", label=f"SNRin {snr} dB")
        ax.axvline(p["mu"], color="r", ls="--", label="chosen mu")
        ax.set_ylim(bottom=max(-10, ax.get_ylim()[0]))
        ax.set_title(f"{noise.upper()} filter, {inp} input, {p['taps']} taps")
        ax.set_xlabel("mu")
        ax.set_ylabel("SNRimp (dB)")
        ax.grid(alpha=0.3)
    axes.flat[0].legend()
    fig.suptitle(f"LMS step size vs SNRin, ECG {mode}")
    fig.savefig(FIGURES_DIR / f"lms_tuning_vs_snr_{mode}.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    cases = tuning_cases()
    print(f"LMS tuning: {len(LMS_MUS)} step sizes x {len(LMS_TAPS)} tap counts on {len(cases)} cases")
    rows = run_parallel(tune_case, cases)
    df = save_table(rows, ["ecg", "input", "noise", "record", "SNRin_dB", "mu", "taps", "SNRimp_dB"],
                    "lms_tuning.csv")

    params, summary = choose(df)
    LMS_PARAMS_FILE.write_text(json.dumps(params, indent=2))
    print(f"  wrote results/{LMS_PARAMS_FILE.name}")
    summary.to_csv(RESULTS_DIR / "lms_params_summary.csv", index=False)
    print("  wrote results/lms_params_summary.csv")
    print(summary.to_string(index=False))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for mode in ECG_MODES:
        plot_heatmaps(df, params, mode)
        plot_vs_snr(df, params, mode)
