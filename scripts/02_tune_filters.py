"""
Step 2: tune the adaptive filter settings (the paper does not give them).

Every filter of every method gets its own setting, chosen by coordinate descent over a grid
(src/tuning.py) to maximize the mean SNRimp on held-out cases: records TUNE_RECORDS (not
used in any figure) at SNRin TUNE_SNRS, with a different part of the noise records
(TUNE_NOISE_START). One setting per filter is used at every SNRin.
- EMD+LMS / EMD+NLMS / EMD+RLS (Eq. 1): PLI and BW filters, tuned on BW + PLI cases.
- PEAF, SEAF, SDAF: PLI, BW, EM and MA filters; PDAF: one filter; tuned on BW + PLI + EM + MA.

    python scripts/02_tune_filters.py

Writes results/tuned_filter_params.json, results/filter_tuning_scores.csv and
results/figures/filter_tuning_mean_snr_imp_<method>.png.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import pandas as pd

from src.config import TUNE_NOISE_START, TUNE_RECORDS, TUNE_SNRS, TUNING_PASSES
from src.data import ALL_NOISES
from src.methods import BW_PLI_METHODS, FOUR_NOISE_METHODS, METHODS
from src.plots import plt, save
from src.tuning import tune
from src.utils import load_case, run_parallel, save_params, save_table

NOISES = {**{m: ("bw", "pli") for m in BW_PLI_METHODS},
          **{m: ALL_NOISES for m in FOUR_NOISE_METHODS}}


def tuning_cases(noises):
    return [(rec, noises, snr, TUNE_NOISE_START) for rec in TUNE_RECORDS for snr in TUNE_SNRS]


def decompose_case(job):
    load_case(*job)  # computes and caches the EMD


def tune_method(name):
    cases = [load_case(*job) for job in tuning_cases(NOISES[name])]
    params, rows = tune(name, cases)
    return name, params, rows


def plot_scores(df, name, params):
    """Mean SNRimp over the grid of each filter in the last pass (others at their chosen setting)."""
    d = df[(df.method == name) & (df["pass"] == TUNING_PASSES)]
    filters = METHODS[name].filters
    step = "lam" if METHODS[name].algorithm == "RLS" else "mu"
    fig, axes = plt.subplots(1, len(filters), figsize=(5.2 * len(filters), 4.4),
                             constrained_layout=True, squeeze=False)
    for ax, filt in zip(axes[0], filters):
        table = d[d["filter"] == filt].pivot(index="taps", columns=step, values="mean_SNRimp_dB")
        values = table.values.copy()
        values[~np.isfinite(values)] = np.nan
        im = ax.imshow(values, origin="lower", aspect="auto", cmap="viridis")
        for (i, j), v in np.ndenumerate(values):
            ax.text(j, i, "div" if np.isnan(v) else f"{v:.1f}", ha="center", va="center",
                    fontsize=6, color="w")
        chosen = params[filt]
        ax.add_patch(plt.Rectangle((list(table.columns).index(chosen[step]) - 0.5,
                                    list(table.index).index(chosen["taps"]) - 0.5), 1, 1,
                                   fill=False, ec="red", lw=2))
        ax.set_xticks(range(len(table.columns)), [f"{v:g}" for v in table.columns], rotation=60)
        ax.set_yticks(range(len(table.index)), table.index)
        ax.set_xlabel("lambda" if step == "lam" else "mu")
        ax.set_ylabel("taps")
        ax.set_title(f"{filt.upper()} filter: {step}={chosen[step]:g}, {chosen['taps']} taps")
        fig.colorbar(im, ax=ax, shrink=0.85)
    fig.suptitle(f"{name} ({METHODS[name].algorithm}): mean SNRimp (dB) on the tuning cases, "
                 "red = chosen")
    save(fig, f"filter_tuning_mean_snr_imp_{name.replace('+', '_').lower()}.png")


if __name__ == "__main__":
    jobs = sorted({job for m in METHODS for job in tuning_cases(NOISES[m])}, key=str)
    print(f"EMD of {len(jobs)} tuning cases")
    run_parallel(decompose_case, jobs)

    print(f"Tuning {len(METHODS)} methods (one per process)")
    results = run_parallel(tune_method, list(METHODS))
    params = {name: p for name, p, _ in results}
    save_params(params)
    df = save_table(pd.DataFrame([row for _, _, rows in results for row in rows]),
                    "filter_tuning_scores.csv")
    for name in METHODS:
        plot_scores(df, name, params[name])

    print("\nChosen settings (mean SNRimp on the tuning cases):")
    for name, p in params.items():
        best = df[df.method == name].mean_SNRimp_dB.max()
        print(f"  {name:9s} {best:5.2f} dB  " + ", ".join(
            f"{f}: " + " ".join(f"{k}={v:g}" for k, v in s.items()) for f, s in p.items()))
