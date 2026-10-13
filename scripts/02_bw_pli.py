"""
Step 2: ECG corrupted by BW + PLI (Sec. IV-A, Figs. 6, 7, 8).

Method (Fig. 3 / Eq. 1): PLI filter on IMF1, BW filter on IMF5-8,
Y = IMF1' + IMF2 + IMF3 + IMF4 + IMF'58 + r.

- Fig. 7: the same structure with LMS (tuned settings), NLMS and RLS (MATLAB defaults).
- Fig. 8: SNR output at SNRin = 10 dB on records 119, 202, 213, 217, 234, next to the
  numbers the paper reports. "LMS, no EMD" (PLI and BW filters on the whole signal) is
  added to show what EMD contributes.

    python scripts/02_bw_pli.py

Writes results/bw_pli.csv and results/figures/fig6_*.png, fig7_*.png, fig8_*.png.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import (ECG_MODES, FIG8_RECORDS, FIGURES_DIR, MATLAB_TAPS, NLMS_MU, PAPER_FIG8,
                        RLS_LAMBDA, RLS_P0)
from src.data import make_case
from src.emd import decompose
from src.filters import nlms, rls
from src.methods import direct_bw_pli, emd_bw_pli, make_filter
from src.metrics import rmse, snr, snr_imp
from src.plots import plot_example
from src.utils import bw_pli_cases, load_lms_params, run_parallel, save_table

EXAMPLE = (119, 10)  # record and SNRin of the Fig. 6 example


def denoise(c, params):
    """{method: denoised ECG} for one BW + PLI case."""
    imfs, r = decompose(c["noisy"])
    refs = c["refs"]
    nlms_settings = {n: {"mu": NLMS_MU, "taps": MATLAB_TAPS} for n in refs}
    rls_settings = {n: {"lam": RLS_LAMBDA, "taps": MATLAB_TAPS, "p0": RLS_P0} for n in refs}
    return {
        "EMD+LMS": emd_bw_pli(imfs, r, make_filter(refs, params["emd"])),
        "EMD+NLMS": emd_bw_pli(imfs, r, make_filter(refs, nlms_settings, nlms)),
        "EMD+RLS": emd_bw_pli(imfs, r, make_filter(refs, rls_settings, rls)),
        "LMS, no EMD": direct_bw_pli(c["noisy"], make_filter(refs, params["direct"])),
    }


def run_case(case):
    record, _, snr_in, mode, _ = case
    c = make_case(*case)
    outputs = denoise(c, load_lms_params()[mode])
    if (record, snr_in) == EXAMPLE:
        plot_example(c["clean"], c["noisy"], outputs["EMD+LMS"],
                     f"Fig. 6: record {record}, BW + PLI at {snr_in} dB, EMD + LMS, ECG {mode}",
                     FIGURES_DIR / f"fig6_{mode}.png")
    return [(mode, record, snr_in, method, snr(c["clean"], y), rmse(c["clean"], y),
             snr_imp(c["clean"], c["noisy"], y)) for method, y in outputs.items()]


def plot_fig7(df, mode):
    d = df[(df.ecg == mode) & df.method.str.startswith("EMD+")]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), constrained_layout=True)
    for ax, column, label in [(axes[0], "SNRout_dB", "SNR output (dB)"), (axes[1], "RMSE", "RMSE")]:
        table = d.groupby(["SNRin_dB", "method"])[column].mean().unstack()
        table.plot.bar(ax=ax, rot=0)
        ax.set_xlabel("SNR input (dB)")
        ax.set_ylabel(label)
        ax.grid(axis="y", alpha=0.3)
    axes[0].set_title("(a) SNR output, mean over records")
    axes[1].set_title("(b) RMSE, mean over records")
    fig.suptitle(f"Fig. 7: LMS vs NLMS vs RLS with EMD, BW + PLI, ECG {mode}")
    fig.savefig(FIGURES_DIR / f"fig7_{mode}.png", dpi=120)
    plt.close(fig)


def plot_fig8(df, mode):
    d = df[(df.ecg == mode) & (df.SNRin_dB == 10)].set_index("record")
    x = np.arange(len(FIG8_RECORDS))
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    for method, style in [("EMD+LMS", "o-"), ("LMS, no EMD", "s-")]:
        ax.plot(x, d[d.method == method].SNRout_dB.loc[FIG8_RECORDS], style, lw=2, label=f"ours: {method}")
    for name, values in PAPER_FIG8.items():
        ax.plot(x, values, "--", alpha=0.7, label=f"reported: {name}")
    ax.set_xticks(x, FIG8_RECORDS)
    ax.set_xlabel("record")
    ax.set_ylabel("SNR output (dB)")
    ax.set_title(f"Fig. 8: SNR output at SNRin = 10 dB, BW + PLI, ECG {mode}")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.savefig(FIGURES_DIR / f"fig8_{mode}.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cases = bw_pli_cases()
    print(f"BW + PLI: {len(cases)} cases")
    rows = run_parallel(run_case, cases)
    df = save_table(rows, ["ecg", "record", "SNRin_dB", "method", "SNRout_dB", "RMSE", "SNRimp_dB"],
                    "bw_pli.csv")

    for mode in ECG_MODES:
        plot_fig7(df, mode)
        plot_fig8(df, mode)

    print(df.groupby(["ecg", "SNRin_dB", "method"]).SNRimp_dB.mean().unstack().round(2).to_string())
