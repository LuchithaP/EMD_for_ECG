"""Loading cases with their EMD, running jobs on all cores, saving tables and settings."""
import json
import os
from multiprocessing import Pool

import pandas as pd

from src.config import RESULTS_DIR, TEST_NOISE_START, TUNED_PARAMS_FILE
from src.data import make_case
from src.emd import decompose_cached


def load_case(record, noises, snr, noise_start=TEST_NOISE_START):
    """(case, imfs, residue): one noisy ECG and the EMD of the noisy signal."""
    case = make_case(record, noises, snr, noise_start)
    imfs, r = decompose_cached(case["noisy"])
    return case, imfs, r


def run_parallel(func, jobs, processes=None):
    """[func(job) for job in jobs] on all CPU cores, in the order of jobs."""
    processes = processes or min(len(jobs), os.cpu_count())
    with Pool(processes) as pool:
        results = []
        for i, result in enumerate(pool.imap(func, jobs), 1):
            results.append(result)
            print(f"  {i}/{len(jobs)}", end="\r", flush=True)
    print()
    return results


def save_table(df, name):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RESULTS_DIR / name, index=False, float_format="%.5g")
    print(f"  wrote results/{name}")
    return df


def read_table(name):
    return pd.read_csv(RESULTS_DIR / name)


def save_params(params):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TUNED_PARAMS_FILE.write_text(json.dumps(params, indent=2))
    print(f"  wrote results/{TUNED_PARAMS_FILE.name}")


def load_params():
    """{method: {filter: setting}} written by scripts/02_tune_filters.py."""
    if not TUNED_PARAMS_FILE.exists():
        raise FileNotFoundError("Run scripts/02_tune_filters.py first.")
    return json.loads(TUNED_PARAMS_FILE.read_text())
