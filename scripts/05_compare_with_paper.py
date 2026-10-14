"""
Step 5: our numbers next to the paper's, and a check of each claim of the paper.

    python scripts/05_compare_with_paper.py

Reads results/*.csv and writes results/comparison_with_paper.md.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from src import paper_values as paper
from src.config import (FIG7_RECORDS, FIG8_SNR, FIG10_RECORDS, FIG10_SNRS, FIG11_RECORDS,
                        FIG11_SNRS, RESULTS_DIR)
from src.data import noise_shares
from src.methods import FOUR_NOISE_METHODS
from src.utils import load_params, read_table

lines = []


def out(text=""):
    lines.append(text)


def md_table(df, floatfmt="{:.2f}"):
    """DataFrame -> markdown table (index included)."""
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        cells = [floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in row]
        rows.append("| " + " | ".join([str(idx)] + cells) + " |")
    out("\n".join(rows))
    out()


def ours_paper(ours, paper_values):
    """Cells 'ours (paper)'."""
    return [f"{o:.2f} ({p:g})" for o, p in zip(ours, paper_values)]


def verdict(hits, total):
    return "Yes" if hits == total else ("Partly" if hits > 0 else "No")


claims = []

# ------------------------------------------------------------------ setup
out("# Comparison with the paper")
out()
out("Each cell: **ours (paper)**. Paper values were measured from the PDF figures (about "
    "+-0.2 dB). See README.md for the settings the paper does not give.")
out()
shares = noise_shares()
out("Noise power shares in the four-noise experiments (NSTDB natural ratio, PLI = BW power): "
    + ", ".join(f"{k.upper()} {100 * v:.1f} %" for k, v in shares.items()) + ".")
out()

# ------------------------------------------------------------------ Sec. III-A
imf = read_table("imf_selection.csv")
out("## Sec. III-A: IMFs for each noise (each noise alone, held-out cases)")
out()
rows = {}
for noise in ["pli", "bw", "em", "ma"]:
    d = imf[imf.noise == noise]
    best = d.loc[d.mean_SNRimp_dB.idxmax()]
    chosen = d[d.paper_choice].iloc[0]
    no_emd = d[d.imfs == "no EMD"].iloc[0]
    rows[noise.upper()] = [best.imfs, f"{best.mean_SNRimp_dB:.2f}", chosen.imfs,
                           f"{chosen.mean_SNRimp_dB:.2f}", f"{no_emd.mean_SNRimp_dB:.2f}"]
    claims.append((f"Sec. III-A: {chosen.imfs} is the best input for {noise.upper()}",
                   f"best: {best.imfs} {best.mean_SNRimp_dB:.2f} dB; paper's "
                   f"{chosen.imfs} {chosen.mean_SNRimp_dB:.2f} dB",
                   "Yes" if best.imfs == chosen.imfs else
                   ("Partly" if best.mean_SNRimp_dB - chosen.mean_SNRimp_dB < 1 else "No")))
md_table(pd.DataFrame.from_dict(rows, orient="index", columns=[
    "best IMFs (ours)", "SNRimp", "paper's IMFs", "SNRimp", "no EMD SNRimp"]).rename_axis("noise"))

# ------------------------------------------------------------------ settings
out("## Tuned filter settings")
out()
for name, p in load_params().items():
    out(f"- **{name}**: " + "; ".join(
        f"{f.upper()} " + ", ".join(f"{k}={v:g}" for k, v in s.items()) for f, s in p.items()))
out()

# ------------------------------------------------------------------ Fig. 7
bw = read_table("bw_pli.csv")
d7 = bw[bw.record.isin(FIG7_RECORDS)]
order = ["EMD+LMS", "EMD+RLS", "EMD+NLMS"]
for column, values, title in [("SNRout_dB", paper.FIG7_SNR_OUT, "SNR output (dB)"),
                              ("RMSE", paper.FIG7_RMSE, "RMSE")]:
    table = d7.groupby(["method", "SNRin_dB"])[column].mean().unstack()
    out(f"## Fig. 7: {title}, BW + PLI, mean over records {FIG7_RECORDS}")
    out()
    md_table(pd.DataFrame({f"{s} dB": ours_paper(table.loc[order, s], [values[m][i] for m in order])
                           for i, s in enumerate(paper.FIG7_SNRS)}, index=order).rename_axis("SNRin"))
snr_out = d7.groupby(["method", "SNRin_dB"]).SNRout_dB.mean().unstack()
wins = int((snr_out.idxmax() == "EMD+LMS").sum())
claims.append(("Fig. 7: LMS is better and more stable than NLMS and RLS",
               f"LMS has the best SNRout at {wins}/{snr_out.shape[1]} SNRin "
               f"(winners: {', '.join(snr_out.idxmax().values)})", verdict(wins, snr_out.shape[1])))

# ------------------------------------------------------------------ Fig. 8
d8 = bw[(bw.SNRin_dB == FIG8_SNR) & (bw.method == "EMD+LMS")].set_index("record").SNRout_dB
out(f"## Fig. 8: SNR output at SNRin = {FIG8_SNR} dB, BW + PLI")
out()
rows = {"EMD+LMS": ours_paper(d8.loc[paper.FIG8_RECORDS], paper.FIG8_SNR_OUT["EMD+LMS"])}
for name in ["Article [28]", "Article [21]", "Article [22]"]:
    rows[f"{name} (paper)"] = [f"{v:g}" for v in paper.FIG8_SNR_OUT[name]]
md_table(pd.DataFrame.from_dict(rows, orient="index", columns=paper.FIG8_RECORDS).rename_axis("record"))
best_article = np.max([paper.FIG8_SNR_OUT[n] for n in ["Article [28]", "Article [21]", "Article [22]"]], axis=0)
wins = int((d8.loc[paper.FIG8_RECORDS].values > best_article).sum())
claims.append(("Fig. 8: EMD + LMS beats articles [28, 21, 22] (their values as reported)",
               f"ours better than the best article on {wins}/5 records", verdict(wins, 5)))
diff = d8.loc[paper.FIG8_RECORDS].values - np.array(paper.FIG8_SNR_OUT["EMD+LMS"])
claims.append(("Fig. 8: our EMD + LMS SNR output matches the paper's",
               f"mean difference {diff.mean():+.2f} dB, mean |difference| {np.abs(diff).mean():.2f} dB",
               "Yes" if np.abs(diff).mean() < 2 else ("Partly" if np.abs(diff).mean() < 5 else "No")))

# ------------------------------------------------------------------ Fig. 10
four = read_table("four_noises.csv")
for s in FIG10_SNRS:
    d = four[four.SNRin_dB == s].pivot(index="record", columns="method", values="SNRimp_dB")
    out(f"## Fig. 10: SNRimp per record, ours at SNRin = {s} dB")
    out()
    table = pd.DataFrame({m: ours_paper(d.loc[FIG10_RECORDS, m], paper.FIG10_SNR_IMP[m])
                          for m in FOUR_NOISE_METHODS}, index=FIG10_RECORDS)
    table["best (ours)"] = d.loc[FIG10_RECORDS, FOUR_NOISE_METHODS].idxmax(axis=1)
    md_table(table.rename_axis("record"))
    wins = int((table["best (ours)"] == "PEAF").sum())
    claims.append((f"Fig. 10 (SNRin {s} dB): PEAF is best on every record",
                   f"PEAF best on {wins}/{len(FIG10_RECORDS)} records; mean SNRimp " +
                   ", ".join(f"{m} {d[m].mean():.2f}" for m in FOUR_NOISE_METHODS),
                   verdict(wins, len(FIG10_RECORDS))))

# ------------------------------------------------------------------ Fig. 11
d11 = four[four.record.isin(FIG11_RECORDS)].groupby(["method", "SNRin_dB"]).SNRimp_dB.mean().unstack()
out(f"## Fig. 11: SNRimp vs SNRin, mean over {len(FIG11_RECORDS)} records")
out()
table = pd.DataFrame({f"{s} dB": ours_paper(d11.loc[FOUR_NOISE_METHODS, s],
                                            [paper.FIG11_SNR_IMP[m][i] for m in FOUR_NOISE_METHODS])
                      for i, s in enumerate(FIG11_SNRS)}, index=FOUR_NOISE_METHODS)
md_table(table.rename_axis("SNRin"))
best = d11.loc[FOUR_NOISE_METHODS, FIG11_SNRS].idxmax()
wins = int((best == "PEAF").sum())
claims.append(("Fig. 11: PEAF is best at every SNRin",
               f"PEAF best at {wins}/{len(FIG11_SNRS)} SNRin (winners: {', '.join(best.values)})",
               verdict(wins, len(FIG11_SNRS))))
emd_better = int(sum(d11.loc[["PEAF", "SEAF"], s].max() > d11.loc[["PDAF", "SDAF"], s].max()
                     for s in FIG11_SNRS))
claims.append(("Figs. 10-11: EMD + adaptive filter beats adaptive filter only",
               f"best EMD method (PEAF/SEAF) beats best direct method (PDAF/SDAF) at "
               f"{emd_better}/{len(FIG11_SNRS)} SNRin", verdict(emd_better, len(FIG11_SNRS))))
falling = [m for m in FOUR_NOISE_METHODS if (np.diff(d11.loc[m, FIG11_SNRS].values) < 0).all()]
claims.append(("Fig. 11: SNRimp falls as SNRin rises",
               f"true for {len(falling)}/4 methods ({', '.join(falling) or 'none'})",
               verdict(len(falling), 4)))
diff = d11.loc["PEAF", FIG11_SNRS].values - np.array(paper.FIG11_SNR_IMP["PEAF"])
claims.append(("Fig. 11: our PEAF SNRimp matches the paper's",
               f"mean difference {diff.mean():+.2f} dB, mean |difference| {np.abs(diff).mean():.2f} dB",
               "Yes" if np.abs(diff).mean() < 1 else ("Partly" if np.abs(diff).mean() < 3 else "No")))

# ------------------------------------------------------------------ claims
out("## Claims of the paper")
out()
md_table(pd.DataFrame(claims, columns=["claim", "ours", "reproduced"]).set_index("claim"))

path = RESULTS_DIR / "comparison_with_paper.md"
path.write_text("\n".join(lines), encoding="utf-8")
print(f"  wrote results/{path.name}\n")
print("\n".join(lines[lines.index("## Claims of the paper"):]))
