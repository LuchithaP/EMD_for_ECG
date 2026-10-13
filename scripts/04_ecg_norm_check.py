"""
Step 4: does normalizing the ECG help?

Every experiment was run twice: with the MIT-BIH ECG as recorded ("raw", in mV with a DC
offset) and with the ECG normalized to zero mean and unit standard deviation ("norm").
Each mode has its own tuned LMS settings. This script compares the two.

Note: Eq. (4) counts the DC offset of the raw ECG as signal power. With a large offset,
the noise added for a given SNRin is large compared with the ECG waveform itself.
"wave_SNR_dB" below is the SNR of the waveform alone (ECG minus its mean) at SNRin = 10 dB.

    python scripts/04_ecg_norm_check.py

Writes results/ecg_norm_check.csv, results/ecg_dc_offset.csv and
results/figures/ecg_norm_check.png.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import FIG8_RECORDS, FIG10_RECORDS, FIGURES_DIR, RESULTS_DIR
from src.data import load_ecg
from src.utils import load_lms_params, save_table


def dc_offset_table():
    rows = []
    for record in FIG8_RECORDS + FIG10_RECORDS:
        x = load_ecg(record, "raw")
        dc_share = x.mean() ** 2 / np.mean(x**2)
        rows.append((record, x.mean(), x.std(), 100 * dc_share, 10 + 10 * np.log10(1 - dc_share)))
    return save_table(rows, ["record", "mean_mV", "std_mV", "DC_share_of_power_pct", "wave_SNR_dB"],
                      "ecg_dc_offset.csv")


def compare(df, setup):
    table = df.groupby(["method", "SNRin_dB", "ecg"]).SNRimp_dB.mean().unstack()
    table["norm_minus_raw"] = table["norm"] - table["raw"]
    table.insert(0, "setup", setup)
    return table.reset_index()


if __name__ == "__main__":
    bw_pli = pd.read_csv(RESULTS_DIR / "bw_pli.csv")
    four = pd.read_csv(RESULTS_DIR / "four_methods.csv")
    table = pd.concat([compare(bw_pli, "BW+PLI"), compare(four, "BW+PLI+EM+MA")])
    table.to_csv(RESULTS_DIR / "ecg_norm_check.csv", index=False, float_format="%.4g")
    print("  wrote results/ecg_norm_check.csv")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    for ax, (setup, d) in zip(axes, table.groupby("setup", sort=False)):
        for i, (method, m) in enumerate(d.groupby("method")):
            color = f"C{i}"
            ax.plot(m.SNRin_dB, m.raw, "o-", color=color, label=f"{method} raw")
            ax.plot(m.SNRin_dB, m.norm, "s--", color=color, label=f"{method} norm")
        ax.set_title(setup)
        ax.set_xlabel("SNR input (dB)")
        ax.set_ylabel("mean SNRimp (dB)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, ncol=2)
    fig.suptitle("ECG raw (solid) vs normalized (dashed)")
    fig.savefig(FIGURES_DIR / "ecg_norm_check.png", dpi=120)
    plt.close(fig)

    print("\nMean SNRimp (dB), raw vs normalized ECG:")
    print(table.round(2).to_string(index=False))
    print("\nMean over all cases, norm - raw (dB):")
    print(table.groupby(["setup", "method"]).norm_minus_raw.mean().round(2).to_string())

    print("\nDC offset of the raw ECG:")
    print(dc_offset_table().round(2).to_string(index=False))

    params = load_lms_params()
    print("\nTuned LMS settings (mu, taps), raw vs norm:")
    for inp in ("emd", "direct"):
        for noise, p in params["raw"][inp].items():
            q = params["norm"][inp][noise]
            print(f"  {inp:6s} {noise:3s}  raw: mu={p['mu']:g}, {p['taps']} taps   "
                  f"norm: mu={q['mu']:g}, {q['taps']} taps")
