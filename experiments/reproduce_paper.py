"""
Run the experiments of Dai & Bai, "Denoising ECG by adaptive filter with empirical
mode decomposition", and save the numbers to results/. The notebooks plot them.

    python experiments/reproduce_paper.py                 # everything, in order
    python experiments/reproduce_paper.py fig10 fig11     # selected stages

Stages:
- sweep:    LMS step size x number of taps on the paper's records at SNRin = -5 and
            10 dB. The paper's MATLAB default (0.1, 32 taps) diverges on this data, so
            one setting is chosen here and used for every LMS filter in every stage.
- imf:      Sec. III-A / Fig. 2, which IMF combination suits each noise.
- bw_pli:   Figs. 6, 7, 8, BW + PLI with EMD (Eq. 1); LMS, NLMS and RLS.
- four:     Figs. 9, 10, 11, BW + PLI + EM + MA; PEAF, SEAF, PDAF, SDAF.

Setup (see src/data_load.make_noisy_ecg): whole MIT-BIH records, NSTDB noises at
their recorded amplitudes (shifted and filtered before being added), PLI = 60 Hz
sinusoid with the power of BW, total noise scaled to SNRin. EMD with MATLAB `emd`
defaults, 8 IMFs + residue. Metrics: Eqs. (4)-(6) over the whole record.
"""

import json
import sys
import warnings
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore", category=RuntimeWarning)  # diverging filters overflow

from src.adaptive_filters import LMS_filter, NLMS_filter, RLS_filter, rmse, snr_db
from src.data_load import make_noisy_ecg
from src.EMD import emd_decompose
from src.methods import denoise_imf_combination, emd_bw_pli, run_all_four

RESULTS = Path(__file__).resolve().parent.parent / "results"
LMS_SETTING = RESULTS / "lms_setting.json"

FIG8_RECORDS = [119, 202, 213, 217, 234]
FIG10_RECORDS = [100, 103, 104, 105, 106, 111, 113, 115, 116, 121, 122, 123, 231]
FIG7_SNRS = [-5, 0, 5, 7, 10]
FIG11_SNRS = [-5, -2, 0, 3, 6, 10]

SWEEP_MUS = [1e-1, 1e-2, 1e-3, 1e-4, 1e-5]
SWEEP_TAPS = [8, 16, 32, 64]
SWEEP_SNRS = [-5, 10]

# Sec. III-A: the adaptive filter is applied to combinations of IMFs; here every
# contiguous range IMFi..IMFj, plus the whole signal without EMD
IMF_COMBOS = [None] + [(i, j) for i in range(1, 9) for j in range(i, 9)]

# Fig. 8 of the paper, read off the plot (about +-0.3 dB): SNR output at SNRin = 10 dB
PAPER_FIG8 = {
    "Proposed LMS+EMD (paper)": [24.6, 22.6, 25.0, 29.2, 23.9],
    "Article [28]": [17.9, 23.0, 20.0, 25.9, 20.4],
    "Article [21]": [16.5, 20.4, 17.9, 24.0, 18.9],
    "Article [22]": [13.9, 18.9, 15.9, 22.9, 18.5],
}


def make_case(record, snr, noises=("bw", "em", "ma"), pli=True):
    case = make_noisy_ecg(record, noises, pli, snr)
    imfs, residue = emd_decompose(case["noisy"])
    return case, imfs, residue


def snr_imp(case, y):
    return float(snr_db(case["clean"], y) - snr_db(case["clean"], case["noisy"]))


def lms(setting):
    return partial(LMS_filter, mu=setting["mu"], filter_order=setting["taps"])


def load_setting():
    if not LMS_SETTING.exists():
        raise FileNotFoundError("Run `python experiments/reproduce_paper.py sweep` first.")
    return json.loads(LMS_SETTING.read_text())


def write_csv(name, header, rows):
    path = RESULTS / name
    with open(path, "w") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(f"{v:.6g}" if isinstance(v, float) else str(v) for v in r) + "\n")
    print(f"  wrote {path.relative_to(RESULTS.parent)}", flush=True)


# ---------------------------------------------------------------- jobs (one per case)


def _sweep_job(args):
    setup, record, snr = args
    rows = []
    if setup == "BW+PLI":
        case, imfs, residue = make_case(record, snr, ("bw",))
    else:
        case, imfs, residue = make_case(record, snr)
    for mu in SWEEP_MUS:
        for taps in SWEEP_TAPS:
            af = lms({"mu": mu, "taps": taps})
            if setup == "BW+PLI":
                outs = {"EMD+LMS": emd_bw_pli(case["references"], imfs, residue, af)}
            else:
                outs = run_all_four(case["noisy"], case["references"], imfs, residue, af)
            rows += [(setup, record, snr, mu, taps, m, snr_imp(case, y)) for m, y in outs.items()]
    return rows


def _imf_job(args):
    noise, record, setting = args
    case, imfs, residue = make_case(
        record, 10, () if noise == "pli" else (noise,), noise == "pli"
    )
    rows = []
    for c in IMF_COMBOS:
        first, last = (None, None) if c is None else c
        name = "no EMD" if c is None else (f"IMF{first}" if first == last else f"IMF{first}-{last}")
        y = denoise_imf_combination(
            case["noisy"], case["references"][noise], imfs, first, last, lms(setting)
        )
        rows.append((noise, record, name, snr_imp(case, y)))
    return rows


def _bw_pli_job(args):
    record, snr, setting = args
    case, imfs, residue = make_case(record, snr, ("bw",))
    taps = setting["taps"]
    filters = {
        "LMS": lms(setting),
        "NLMS": partial(NLMS_filter, filter_order=taps),
        "RLS": partial(RLS_filter, filter_order=taps),
    }
    rows = []
    for name, af in filters.items():
        y = emd_bw_pli(case["references"], imfs, residue, af)
        rows.append((record, snr, name, float(snr_db(case["clean"], y)),
                     float(rmse(case["clean"], y)), snr_imp(case, y)))
        if name == "LMS" and record == FIG8_RECORDS[0] and snr == 10:
            save_example("fig6_example.npz", case, {"EMD+LMS": y})
    return rows


def _four_job(args):
    record, snr, setting = args
    case, imfs, residue = make_case(record, snr)
    outs = run_all_four(case["noisy"], case["references"], imfs, residue, lms(setting))
    if record == FIG10_RECORDS[0] and snr == 10:
        save_example("fig9_example.npz", case, outs)
    return [(record, snr, m, float(snr_db(case["clean"], y)), snr_imp(case, y))
            for m, y in outs.items()]


def save_example(name, case, outputs):
    """Signals for the time/frequency example plots (Figs. 6 and 9)."""
    np.savez_compressed(
        RESULTS / name,
        fs=case["fs"],
        clean=case["clean"].astype(np.float32),
        noisy=case["noisy"].astype(np.float32),
        **{k: v.astype(np.float32) for k, v in outputs.items()},
    )


def _run(pool, job, jobs):
    rows = []
    for i, r in enumerate(pool.imap_unordered(job, jobs), 1):
        rows += r
        print(f"  {i}/{len(jobs)}", end="\r", flush=True)
    return rows


# ---------------------------------------------------------------- stages


def stage_sweep(pool):
    print("LMS step size x taps sweep")
    jobs = [("BW+PLI", r, s) for r in FIG8_RECORDS for s in SWEEP_SNRS]
    jobs += [("BW+PLI+EM+MA", r, s) for r in FIG10_RECORDS for s in SWEEP_SNRS]
    rows = sorted(_run(pool, _sweep_job, jobs))
    write_csv("lms_sweep.csv", ["setup", "record", "SNRin_dB", "mu", "taps", "method", "SNRimp_dB"], rows)

    # One setting for everything: stable (finite) on every run, then the highest mean
    # SNRimp over all runs and methods
    scores = {}
    for *_, mu, taps, _, v in rows:
        scores.setdefault((mu, taps), []).append(v)
    stable = {k: float(np.mean(v)) for k, v in scores.items() if np.all(np.isfinite(v))}
    mu, taps = max(stable, key=stable.get)
    LMS_SETTING.write_text(json.dumps({"mu": mu, "taps": taps}, indent=2))
    print(f"  chosen LMS setting: mu = {mu:g}, taps = {taps}")


def stage_imf(pool):
    setting = load_setting()
    print("IMF selection (Sec. III-A), single noise at SNRin = 10 dB, LMS", setting)
    jobs = [(n, r, setting) for n in ("pli", "bw", "em", "ma") for r in FIG10_RECORDS]
    write_csv("imf_selection.csv", ["noise", "record", "combination", "SNRimp_dB"],
              _run(pool, _imf_job, jobs))


def stage_bw_pli(pool):
    setting = load_setting()
    print("BW+PLI (Figs. 6, 7, 8), LMS", setting)
    jobs = [(r, s, setting) for r in FIG8_RECORDS for s in FIG7_SNRS]
    write_csv("bw_pli.csv", ["record", "SNRin_dB", "filter", "SNRout_dB", "RMSE", "SNRimp_dB"],
              sorted(_run(pool, _bw_pli_job, jobs)))
    write_csv("paper_fig8_reported.csv", ["record", "method", "SNRout_dB"],
              [(r, m, float(v[i])) for m, v in PAPER_FIG8.items() for i, r in enumerate(FIG8_RECORDS)])


def stage_four(pool):
    setting = load_setting()
    print("BW+PLI+EM+MA, four methods (Figs. 9, 10, 11), LMS", setting)
    jobs = [(r, s, setting) for r in FIG10_RECORDS for s in FIG11_SNRS]
    write_csv("four_methods.csv", ["record", "SNRin_dB", "method", "SNRout_dB", "SNRimp_dB"],
              sorted(_run(pool, _four_job, jobs)))


STAGES = {"sweep": stage_sweep, "imf": stage_imf, "bw_pli": stage_bw_pli, "four": stage_four}


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    selected = sys.argv[1:] or list(STAGES)
    with Pool() as pool:
        for name in selected:
            STAGES[name](pool)
