"""
Step 4, Sec. IV-B: ECG corrupted by BW + PLI + EM + MA (Figs. 9, 10, 11).

Four methods (Sec. III-B), all with LMS filters at the tuned settings:
- PEAF: Parallel EMD Adaptive Filter (Fig. 4a, Eq. 2)       "proposed emd+adap parallel"
- SEAF: Staged EMD Adaptive Filter (Fig. 4b, Eq. 3)         "proposed emd+adap staged"
- PDAF: Parallel Direct Adaptive Filter (all noises as one) "adap parallel"
- SDAF: Staged Direct Adaptive Filter (Fig. 5)              "adap stage [13]"

- Fig. 9: example with PEAF
- Fig. 10: SNRimp per record, at SNRin = -5 dB and at 10 dB (see FIG10_SNRS in config)
- Fig. 11: SNRimp vs SNRin, mean over FIG11_RECORDS

    python scripts/04_four_noises.py

Writes results/four_noises.csv and results/figures/fig9_*.png, fig10_*.png, fig11_*.png.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd

from src import paper_values as paper
from src.config import FIG9_EXAMPLE, FIG10_RECORDS, FIG10_SNRS, FIG11_RECORDS, FIG11_SNRS
from src.data import ALL_NOISES
from src.methods import FOUR_NOISE_METHODS, denoise
from src.metrics import snr, snr_imp
from src.plots import lines_ours_vs_paper, plot_example, plt, save
from src.utils import load_case, load_params, run_parallel, save_table


def run_case(job):
    record, snr_in = job
    case, imfs, r = load_case(record, ALL_NOISES, snr_in)
    params = load_params()
    rows = []
    for name in FOUR_NOISE_METHODS:
        y = denoise(name, case, imfs, r, params[name])
        rows.append({"record": record, "SNRin_dB": snr_in, "method": name,
                     "SNRout_dB": snr(case["clean"], y),
                     "SNRimp_dB": snr_imp(case["clean"], case["noisy"], y)})
    return rows


def fig9():
    rec, snr_in = FIG9_EXAMPLE["record"], FIG9_EXAMPLE["snr"]
    case, imfs, r = load_case(rec, ALL_NOISES, snr_in)
    y = denoise("PEAF", case, imfs, r, load_params()["PEAF"])
    plot_example(case["clean"], case["noisy"], y, "PEAF",
                 f"Fig. 9: record {rec} + BW + PLI + EM + MA at SNRin {snr_in} dB, denoised by PEAF",
                 f"fig9_four_noise_example_peaf_record{rec}_snr{snr_in}dB.png")


def fig10(df, snr_in):
    d = df[df.SNRin_dB == snr_in].pivot(index="record", columns="method", values="SNRimp_dB")
    fig, ax = plt.subplots(figsize=(13, 5.5), constrained_layout=True)
    lines_ours_vs_paper(ax, [str(r) for r in FIG10_RECORDS],
                        {m: d.loc[FIG10_RECORDS, m].values for m in FOUR_NOISE_METHODS},
                        paper.FIG10_SNR_IMP)
    ax.set_xlabel("record")
    ax.set_ylabel("SNRimp (dB)")
    ax.set_title(f"Fig. 10: SNRimp per record, ours at SNRin = {snr_in} dB "
                 "(paper: text says 10 dB, values match its Fig. 11 at -5 dB)")
    ax.legend(fontsize=8, ncol=4)
    save(fig, f"fig10_snr_imp_per_record_four_methods_snr_in_{snr_in}dB.png".replace("-", "minus"))


def fig11(df):
    d = df[df.record.isin(FIG11_RECORDS)].groupby(["method", "SNRin_dB"]).SNRimp_dB.mean().unstack()
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    lines_ours_vs_paper(ax, FIG11_SNRS, {m: d.loc[m, FIG11_SNRS].values for m in FOUR_NOISE_METHODS},
                        paper.FIG11_SNR_IMP)
    ax.set_xticks(FIG11_SNRS)
    ax.set_xlabel("SNR input (dB)")
    ax.set_ylabel("SNRimp (dB)")
    ax.set_title(f"Fig. 11: SNRimp vs SNRin, mean over {len(FIG11_RECORDS)} records")
    ax.legend(fontsize=8, ncol=2)
    save(fig, "fig11_snr_imp_vs_snr_in_four_methods.png")


if __name__ == "__main__":
    snrs = sorted(set(FIG11_SNRS) | set(FIG10_SNRS))
    jobs = [(rec, s) for rec in sorted(set(FIG10_RECORDS) | set(FIG11_RECORDS)) for s in snrs]
    print(f"BW + PLI + EM + MA: {len(jobs)} cases x {len(FOUR_NOISE_METHODS)} methods")
    df = save_table(pd.DataFrame([row for rows in run_parallel(run_case, jobs) for row in rows]),
                    "four_noises.csv")
    fig9()
    for s in FIG10_SNRS:
        fig10(df, s)
    fig11(df)

    table = df[df.record.isin(FIG11_RECORDS)].groupby(["method", "SNRin_dB"]).SNRimp_dB.mean().unstack()
    print("\nMean SNRimp (dB), ours (paper):")
    for m in FOUR_NOISE_METHODS:
        print(f"  {m}  " + "  ".join(f"{table.loc[m, s]:5.2f} ({p:g})"
                                     for s, p in zip(FIG11_SNRS, paper.FIG11_SNR_IMP[m])))
