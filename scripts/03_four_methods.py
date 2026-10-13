"""
Step 3: ECG corrupted by BW + PLI + EM + MA (Sec. IV-B, Figs. 9, 10, 11).

Four methods (Sec. III-B):
- PEAF: Parallel EMD Adaptive Filter (Fig. 4a, Eq. 2)
- SEAF: Staged EMD Adaptive Filter (Fig. 4b, Eq. 3)
- PDAF: Parallel Direct Adaptive Filter (one filter, all noises as one)
- SDAF: Staged Direct Adaptive Filter (Fig. 5)
Every filter is LMS with the tuned setting of its noise (results/lms_params.json).

- Fig. 10: SNRimp of every record at SNRin = 10 dB
- Fig. 11: mean SNRimp over the records at every SNRin

    python scripts/03_four_methods.py

Writes results/four_methods.csv and results/figures/fig9_*.png, fig10_*.png, fig11_*.png.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import ECG_MODES, FIG10_RECORDS, FIGURES_DIR, PAPER_FIG11_PEAF
from src.data import make_case
from src.emd import decompose
from src.methods import make_filter, pdaf, peaf, sdaf, seaf
from src.metrics import snr, snr_imp
from src.plots import plot_example
from src.utils import four_noise_cases, load_lms_params, run_parallel, save_table

METHODS = ["PEAF", "SEAF", "PDAF", "SDAF"]
EXAMPLE = (100, 10)  # record and SNRin of the Fig. 9 example


def denoise(c, params):
    """{method: denoised ECG} for one BW + PLI + EM + MA case."""
    imfs, r = decompose(c["noisy"])
    f_emd = make_filter(c["refs"], params["emd"])
    f_direct = make_filter(c["refs"], params["direct"])
    return {
        "PEAF": peaf(imfs, r, f_emd, f_direct),
        "SEAF": seaf(imfs, r, f_emd, f_direct),
        "PDAF": pdaf(c["noisy"], f_direct),
        "SDAF": sdaf(c["noisy"], f_direct),
    }


def run_case(case):
    record, _, snr_in, mode, _ = case
    c = make_case(*case)
    outputs = denoise(c, load_lms_params()[mode])
    if (record, snr_in) == EXAMPLE:
        plot_example(c["clean"], c["noisy"], outputs["PEAF"],
                     f"Fig. 9: record {record}, BW + PLI + EM + MA at {snr_in} dB, PEAF, ECG {mode}",
                     FIGURES_DIR / f"fig9_{mode}.png")
    return [(mode, record, snr_in, method, snr(c["clean"], y), snr_imp(c["clean"], c["noisy"], y))
            for method, y in outputs.items()]


def plot_fig10(df, mode):
    d = df[(df.ecg == mode) & (df.SNRin_dB == 10)]
    table = d.pivot(index="record", columns="method", values="SNRimp_dB").loc[FIG10_RECORDS, METHODS]
    x = np.arange(len(FIG10_RECORDS))
    fig, ax = plt.subplots(figsize=(11, 4.5), constrained_layout=True)
    for method in METHODS:
        ax.plot(x, table[method], "o-", label=method)
    ax.set_xticks(x, FIG10_RECORDS)
    ax.set_xlabel("record")
    ax.set_ylabel("SNRimp (dB)")
    ax.set_title(f"Fig. 10: SNRimp per record at SNRin = 10 dB, ECG {mode}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(FIGURES_DIR / f"fig10_{mode}.png", dpi=120)
    plt.close(fig)


def plot_fig11(df, mode):
    table = df[df.ecg == mode].groupby(["SNRin_dB", "method"]).SNRimp_dB.mean().unstack()[METHODS]
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    for method in METHODS:
        ax.plot(table.index, table[method], "o-", label=method)
    ax.plot(list(PAPER_FIG11_PEAF), list(PAPER_FIG11_PEAF.values()), "k--", label="PEAF (paper)")
    ax.set_xlabel("SNR input (dB)")
    ax.set_ylabel("mean SNRimp (dB)")
    ax.set_title(f"Fig. 11: SNRimp vs SNRin, mean over {len(FIG10_RECORDS)} records, ECG {mode}")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.savefig(FIGURES_DIR / f"fig11_{mode}.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    cases = four_noise_cases()
    print(f"BW + PLI + EM + MA: {len(cases)} cases")
    rows = run_parallel(run_case, cases)
    df = save_table(rows, ["ecg", "record", "SNRin_dB", "method", "SNRout_dB", "SNRimp_dB"],
                    "four_methods.csv")

    for mode in ECG_MODES:
        plot_fig10(df, mode)
        plot_fig11(df, mode)

    print(df.groupby(["ecg", "SNRin_dB", "method"]).SNRimp_dB.mean().unstack()[METHODS].round(2).to_string())
