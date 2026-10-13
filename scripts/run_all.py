"""
Run every step in order.

    python scripts/run_all.py
"""
import subprocess
import sys
from pathlib import Path

STEPS = ["01_tune_lms.py", "02_bw_pli.py", "03_four_methods.py", "04_ecg_norm_check.py"]

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    for step in STEPS:
        print(f"\n===== {step} =====", flush=True)
        subprocess.run([sys.executable, str(here / step)], check=True)
