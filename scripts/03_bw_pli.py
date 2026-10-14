"""
Step 3, Sec. IV-A: ECG corrupted by BW + PLI (Figs. 6, 7, 8).

Method (Fig. 3 / Eq. 1): PLI filter on IMF1, BW filter on IMF5~8,
Y = IMF1' + IMF2 + IMF3 + IMF4 + IMF'58 + r, with LMS, NLMS or RLS (tuned settings).
- Fig. 6: example (time domain and spectrum) with LMS
- Fig. 7: SNR output and RMSE of LMS / NLMS / RLS vs SNRin, mean over FIG7_RECORDS
- Fig. 8: SNR output of EMD + LMS on records 119, 202, 213, 217, 234 at SNRin = 10 dB,
  next to the paper's proposed method and the articles [28, 21, 22] it compares with

    python scripts/03_bw_pli.py

Writes results/bw_pli.csv and results/figures/fig6_*.png, fig7*.png, fig8_*.png.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd

from src import paper_values as paper
from src.config import FIG6_EXAMPLE, FIG7_RECORDS, FIG7_SNRS, FIG8_RECORDS, FIG8_SNR
from src.methods import BW_PLI_METHODS, denoise
from src.metrics import rmse, snr, snr_imp
from src.plots import bars_ours_vs_paper, lines_ours_vs_paper, plot_example, plt, save
from src.utils import load_case, load_params, run_parallel, save_table

NOISES = ("bw", "pli")


def run_case(job):
    record, snr_in = job
    case, imfs, r = load_case(record, NOISES, snr_in)
    params = load_params()
    rows = []
    for name in BW_PLI_METHODS:
        y = denoise(name, case, imfs, r, params[name])
        rows.append({"record": record, "SNRin_dB": snr_in, "method": name,
                     "SNRout_dB": snr(case["clean"], y), "RMSE": rmse(case["clean"], y),
                     "SNRimp_dB": snr_imp(case["clean"], case["noisy"], y)})
    return rows


def fig6():
    rec, snr_in = FIG6_EXAMPLE["record"], FIG6_EXAMPLE["snr"]
    case, imfs, r = load_case(rec, NOISES, snr_in)
    y = denoise("EMD+LMS", case, imfs, r, load_params()["EMD+LMS"])
    plot_example(case["clean"], case["noisy"], y, "EMD+LMS",
                 f"Fig. 6: record {rec} + BW + PLI at SNRin {snr_in} dB, denoised by EMD + LMS (Eq. 1)",
                 f"fig6_bw_pli_example_emd_lms_record{rec}_snr{snr_in}dB.png")


def fig7(df):
    d = df[df.record.isin(FIG7_RECORDS)]
    groups = [f"SNRin {s} dB" for s in FIG7_SNRS]
    for column, label, values, part, name in [
            ("SNRout_dB", "SNR output (dB)", paper.FIG7_SNR_OUT, "a", "snr_out"),
            ("RMSE", "RMSE", paper.FIG7_RMSE, "b", "rmse")]:
        table = d.groupby(["method", "SNRin_dB"])[column].mean().unstack().loc[:, FIG7_SNRS]
        order = ["EMD+LMS", "EMD+RLS", "EMD+NLMS"]
        fig, ax = plt.subplots(figsize=(12, 5), constrained_layout=True)
        bars_ours_vs_paper(ax, groups, {m: table.loc[m].values for m in order},
                           {m: values[m] for m in order})
        ax.set_ylabel(label)
        ax.legend(ncol=3, fontsize=8)
        ax.set_title(f"Fig. 7({part}): {label} of EMD + LMS / RLS / NLMS, BW + PLI, "
                     f"mean over records {FIG7_RECORDS}")
        save(fig, f"fig7{part}_{name}_lms_rls_nlms_vs_snr_in_bw_pli.png")


def fig8(df):
    d = df[(df.SNRin_dB == FIG8_SNR) & (df.method == "EMD+LMS")].set_index("record")
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    x = [str(r) for r in FIG8_RECORDS]
    lines_ours_vs_paper(ax, x, {"EMD+LMS": d.SNRout_dB.loc[FIG8_RECORDS].values},
                        paper.FIG8_SNR_OUT)
    ax.set_xlabel("record")
    ax.set_ylabel("SNR output (dB)")
    ax.set_ylim(0, 35)
    ax.set_title(f"Fig. 8: SNR output at SNRin = {FIG8_SNR} dB, BW + PLI "
                 "(Articles [28, 21, 22]: values reported in the paper)")
    ax.legend(fontsize=8, ncol=2)
    save(fig, f"fig8_snr_out_per_record_emd_lms_vs_articles_snr_in_{FIG8_SNR}dB.png")


if __name__ == "__main__":
    jobs = [(rec, s) for rec in sorted(set(FIG7_RECORDS) | set(FIG8_RECORDS)) for s in FIG7_SNRS]
    print(f"BW + PLI: {len(jobs)} cases x {len(BW_PLI_METHODS)} methods")
    df = save_table(pd.DataFrame([row for rows in run_parallel(run_case, jobs) for row in rows]),
                    "bw_pli.csv")
    fig6()
    fig7(df)
    fig8(df)

    print("\nMean over records, ours (paper):")
    for column, values in [("SNRout_dB", paper.FIG7_SNR_OUT), ("RMSE", paper.FIG7_RMSE)]:
        table = df[df.record.isin(FIG7_RECORDS)].groupby(["method", "SNRin_dB"])[column].mean().unstack()
        print(f"  {column}")
        for m in ["EMD+LMS", "EMD+RLS", "EMD+NLMS"]:
            print(f"    {m:9s} " + "  ".join(f"{o:6.3g} ({p:g})" for o, p in zip(table.loc[m], values[m])))
