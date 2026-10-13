"""Case lists, parallel running and saving, shared by the scripts."""
import json
from multiprocessing import Pool

import pandas as pd

from src.config import (ECG_MODES, FIG7_SNRS, FIG8_RECORDS, FIG10_RECORDS, FIG11_SNRS,
                        LMS_PARAMS_FILE, RESULTS_DIR, TEST_NOISE_START, TUNE_NOISE_START,
                        TUNE_RECORDS, TUNE_SNRS)

ALL_NOISES = ("bw", "em", "ma", "pli")

# ---------------------------------------------------------------- cases
# A case is (record, noises, snr_db, ecg_mode, noise_start), the arguments of make_case.


def tuning_cases():
    """LMS tuning: each noise alone, and all four together, on the held-out records."""
    noise_sets = [("pli",), ("bw",), ("em",), ("ma",), ALL_NOISES]
    return [(rec, noises, snr, mode, TUNE_NOISE_START)
            for mode in ECG_MODES for rec in TUNE_RECORDS for snr in TUNE_SNRS
            for noises in noise_sets]


def bw_pli_cases():
    """Figs. 6-8: BW + PLI."""
    return [(rec, ("bw", "pli"), snr, mode, TEST_NOISE_START)
            for mode in ECG_MODES for rec in FIG8_RECORDS for snr in FIG7_SNRS]


def four_noise_cases():
    """Figs. 9-11: BW + EM + MA + PLI."""
    return [(rec, ALL_NOISES, snr, mode, TEST_NOISE_START)
            for mode in ECG_MODES for rec in FIG10_RECORDS for snr in FIG11_SNRS]


# ---------------------------------------------------------------- running and saving


def run_parallel(func, jobs):
    """func(job) -> list of rows, run on all CPU cores. Returns all rows."""
    rows = []
    with Pool() as pool:
        for i, result in enumerate(pool.imap_unordered(func, jobs), 1):
            rows += result
            print(f"  {i}/{len(jobs)}", end="\r", flush=True)
    print()
    return rows


def save_table(rows, columns, name):
    df = pd.DataFrame(rows, columns=columns).sort_values(columns[:-1]).reset_index(drop=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / name, index=False, float_format="%.6g")
    print(f"  wrote results/{name}")
    return df


def load_lms_params():
    """{ecg_mode: {"emd": {noise: {"mu", "taps"}}, "direct": {...}}} from scripts/01_tune_lms.py."""
    if not LMS_PARAMS_FILE.exists():
        raise FileNotFoundError("Run scripts/01_tune_lms.py first.")
    return json.loads(LMS_PARAMS_FILE.read_text())
