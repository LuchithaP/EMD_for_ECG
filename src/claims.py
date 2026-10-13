"""
The paper's claims, checked against the result tables in results/.

Each check takes the ECG mode ("raw" or "norm") and returns a dict:
{"claim": ..., "ours": text with our numbers, "verdict": "Yes" | "Partly" | "No"}.

    python -m src.claims        # prints the table for both ECG modes
"""
import numpy as np
import pandas as pd

from src.config import FIG8_RECORDS, PAPER_FIG8, PAPER_FIG11_PEAF, RESULTS_DIR

METHODS = ["PEAF", "SEAF", "PDAF", "SDAF"]


def load(name):
    return pd.read_csv(RESULTS_DIR / f"{name}.csv")


def graded(hits, total):
    return "Yes" if hits == total else ("Partly" if hits > 0 else "No")


def result(claim, ours, verdict):
    return {"claim": claim, "ours": ours, "verdict": verdict}


# ---------------------------------------------------------------- Sec. III-A


def imf_choice(mode, noise):
    """Sec. III-A / Fig. 2: filtering the paper's IMFs beats filtering the whole signal."""
    s = load("lms_params_summary")
    s = s[(s.ecg == mode) & (s.noise == noise)].set_index("input").mean_SNRimp_dB
    imfs = {"pli": "IMF1", "bw": "IMF5-8", "em": "IMF3-8"}[noise]
    return result(f"{noise.upper()}: filter {imfs} (better than no EMD)",
                  f"{imfs}: {s['emd']:.1f} dB, no EMD: {s['direct']:.1f} dB (held-out tuning records)",
                  "Yes" if s["emd"] > s["direct"] else "No")


# ---------------------------------------------------------------- BW + PLI, Figs. 7, 8


def lms_best(mode):
    """Fig. 7: LMS gives a better SNR output than NLMS and RLS."""
    d = load("bw_pli")
    d = d[(d.ecg == mode) & d.method.str.startswith("EMD+")]
    table = d.groupby(["SNRin_dB", "method"]).SNRout_dB.mean().unstack()
    wins = int((table.idxmax(axis=1) == "EMD+LMS").sum())
    at10 = table.loc[10]
    return result("Fig. 7: LMS beats NLMS and RLS",
                  f"LMS best at {wins}/{len(table)} SNRin; at 10 dB: LMS {at10['EMD+LMS']:.1f}, "
                  f"NLMS {at10['EMD+NLMS']:.1f}, RLS {at10['EMD+RLS']:.1f} dB",
                  graded(wins, len(table)))


def emd_beats_direct(mode):
    """BW + PLI: EMD + LMS is better than the same LMS without EMD."""
    d = load("bw_pli")
    table = d[d.ecg == mode].groupby(["SNRin_dB", "method"]).SNRimp_dB.mean().unstack()
    wins = int((table["EMD+LMS"] > table["LMS, no EMD"]).sum())
    return result("BW+PLI: EMD + LMS beats LMS without EMD",
                  f"better at {wins}/{len(table)} SNRin "
                  f"(-5 dB: {table.loc[-5, 'EMD+LMS']:.1f} vs {table.loc[-5, 'LMS, no EMD']:.1f}; "
                  f"10 dB: {table.loc[10, 'EMD+LMS']:.1f} vs {table.loc[10, 'LMS, no EMD']:.1f} dB)",
                  graded(wins, len(table)))


def fig8_vs_articles(mode):
    """Fig. 8: the proposed method beats the methods of [21, 22, 28] on every record."""
    d = load("bw_pli")
    ours = d[(d.ecg == mode) & (d.SNRin_dB == 10) & (d.method == "EMD+LMS")].set_index("record").SNRout_dB
    others = np.max([v for k, v in PAPER_FIG8.items() if k.startswith("Article")], axis=0)
    wins = sum(ours[r] > others[i] for i, r in enumerate(FIG8_RECORDS))
    return result("Fig. 8: EMD + LMS beats articles [21, 22, 28] (their reported SNRout)",
                  f"better on {wins}/{len(FIG8_RECORDS)} records at SNRin 10 dB",
                  graded(wins, len(FIG8_RECORDS)))


def fig8_numbers(mode):
    """Fig. 8: our SNR output is close to the paper's (within 2 dB on average)."""
    d = load("bw_pli")
    ours = d[(d.ecg == mode) & (d.SNRin_dB == 10) & (d.method == "EMD+LMS")].set_index("record").SNRout_dB
    paper = PAPER_FIG8["Proposed LMS+EMD (paper)"]
    diff = [ours[r] - paper[i] for i, r in enumerate(FIG8_RECORDS)]
    text = ", ".join(f"{r}: {ours[r]:.1f} ({paper[i]})" for i, r in enumerate(FIG8_RECORDS))
    mean_abs = np.mean(np.abs(diff))
    return result("Fig. 8: SNRout at 10 dB, ours (paper)",
                  f"{text}; mean |difference| {mean_abs:.1f} dB",
                  "Yes" if mean_abs < 2 else ("Partly" if mean_abs < 5 else "No"))


# ---------------------------------------------------------------- four noises, Figs. 10, 11


def peaf_best_per_record(mode):
    """Fig. 10: PEAF has the best SNRimp on every record at SNRin = 10 dB."""
    d = load("four_methods")
    table = d[(d.ecg == mode) & (d.SNRin_dB == 10)].pivot(index="record", columns="method", values="SNRimp_dB")
    best = table.idxmax(axis=1)
    mean = table.mean()
    return result("Fig. 10: PEAF best on every record (SNRin 10 dB)",
                  f"PEAF best on {(best == 'PEAF').sum()}/{len(best)}; winners {best.value_counts().to_dict()}; "
                  f"mean: " + ", ".join(f"{m} {mean[m]:.1f}" for m in METHODS),
                  graded(int((best == "PEAF").sum()), len(best)))


def peaf_best_per_snr(mode):
    """Fig. 11: PEAF has the best mean SNRimp at every SNRin."""
    d = load("four_methods")
    table = d[d.ecg == mode].groupby(["SNRin_dB", "method"]).SNRimp_dB.mean().unstack()
    best = table.idxmax(axis=1)
    return result("Fig. 11: PEAF best at every SNRin",
                  f"PEAF best at {(best == 'PEAF').sum()}/{len(best)}; winners by SNRin: {best.to_dict()}",
                  graded(int((best == "PEAF").sum()), len(best)))


def snrimp_falls(mode):
    """Fig. 11: SNRimp falls as SNRin rises."""
    d = load("four_methods")
    table = d[d.ecg == mode].groupby(["SNRin_dB", "method"]).SNRimp_dB.mean().unstack()
    falling = [m for m in METHODS if (np.diff(table[m].values) < 0).all()]
    return result("Fig. 11: SNRimp falls as SNRin rises",
                  f"true for {len(falling)}/{len(METHODS)} methods ({', '.join(falling)})",
                  graded(len(falling), len(METHODS)))


def peaf_numbers(mode):
    """Fig. 11: our PEAF SNRimp is close to the paper's (within 1 dB on average)."""
    d = load("four_methods")
    ours = d[(d.ecg == mode) & (d.method == "PEAF")].groupby("SNRin_dB").SNRimp_dB.mean()
    diff = [ours[s] - v for s, v in PAPER_FIG11_PEAF.items()]
    text = ", ".join(f"{s} dB: {ours[s]:.1f} ({v})" for s, v in PAPER_FIG11_PEAF.items())
    mean_abs = np.mean(np.abs(diff))
    return result("Fig. 11: PEAF SNRimp, ours (paper)",
                  f"{text}; mean |difference| {mean_abs:.1f} dB",
                  "Yes" if mean_abs < 1 else ("Partly" if mean_abs < 3 else "No"))


def all_claims(mode):
    checks = [imf_choice(mode, n) for n in ("pli", "bw", "em")]
    checks += [lms_best(mode), emd_beats_direct(mode), fig8_vs_articles(mode), fig8_numbers(mode),
               peaf_best_per_record(mode), peaf_best_per_snr(mode), snrimp_falls(mode),
               peaf_numbers(mode)]
    return pd.DataFrame(checks)


if __name__ == "__main__":
    pd.set_option("display.max_colwidth", None, "display.width", 250)
    for mode in ("raw", "norm"):
        print(f"\n===== ECG {mode} =====")
        print(all_claims(mode)[["verdict", "claim", "ours"]].to_string(index=False))
