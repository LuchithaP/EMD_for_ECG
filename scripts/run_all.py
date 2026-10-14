"""
Run every step in order.

    python scripts/run_all.py
"""
import subprocess
import sys
from pathlib import Path

STEPS = ["01_imf_selection.py", "02_tune_filters.py", "03_bw_pli.py", "04_four_noises.py",
         "05_compare_with_paper.py"]

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    for step in STEPS:
        print(f"\n===== {step} =====", flush=True)
        subprocess.run([sys.executable, str(here / step)], check=True)
