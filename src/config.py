"""
All settings of the experiments in one place.

Paper: Dai & Bai, "Denoising ECG by adaptive filter with empirical mode decomposition".
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MITDB_DIR = ROOT / "data" / "physionet.org" / "files" / "mitdb" / "1.0.0"
NSTDB_DIR = ROOT / "data" / "physionet.org" / "files" / "nstdb" / "1.0.0"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
LMS_PARAMS_FILE = RESULTS_DIR / "lms_params.json"

# ---------------------------------------------------------------- test signals

FS = 360
RECORD_LENGTH = 650_000  # samples in a 30 min MIT-BIH / NSTDB record
DATA_FRACTION = 0.1      # only the first 10 % of every ECG record is used
N_SAMPLES = int(RECORD_LENGTH * DATA_FRACTION)  # 65 000 samples = 3.6 min
# Noise segments: the paper's test cases use the start of the NSTDB noise records; the LMS
# tuning uses a different part of the noise records (and different ECG records)
TEST_NOISE_START = 0
TUNE_NOISE_START = 325_000

PLI_FREQ = 60.0

# Sec. IV: the added noise is a "shifted and filtered" copy of the reference noise.
# The paper gives no values, so these are fixed choices: (delay in samples, FIR taps)
NOISE_PATHS = {
    "bw": (3, [0.6, 0.4]),
    "em": (5, [0.4, 0.3, 0.2, 0.1]),
    "ma": (4, [0.5, 0.3, 0.2]),
}

# ECG normalization modes compared in every experiment:
# "raw"  = MIT-BIH signal as recorded (in mV, with its DC offset)
# "norm" = zero mean, unit standard deviation
ECG_MODES = ("raw", "norm")

# ---------------------------------------------------------------- records and SNRs

FIG8_RECORDS = [119, 202, 213, 217, 234]
FIG10_RECORDS = [100, 103, 104, 105, 106, 111, 113, 115, 116, 121, 122, 123, 231]
FIG7_SNRS = [-5, 0, 5, 7, 10]
FIG11_SNRS = [-5, -2, 0, 3, 6, 10]

# Held-out records for the LMS tuning: not used in any figure of the paper, no pacemaker
TUNE_RECORDS = [101, 112, 117, 201, 220]
TUNE_SNRS = [-5, 0, 5, 10]

# ---------------------------------------------------------------- EMD and IMFs

N_IMFS = 8

# PyEMD sifting: a fixed number of sifting iterations per IMF (Huang's recommended ~10).
# PyEMD's default stopping rule sifts up to 1000 times on these signals, which makes the
# IMFs narrow-band and closely spaced (IMF8 at ~7 Hz), so BW ends up in the residue and
# the paper's IMF split (BW in IMF5-8) cannot work. With 10 sifts each IMF is roughly an
# octave lower than the one before (IMF1 ~70 Hz ... IMF8 ~0.2 Hz), as the paper assumes.
EMD_SIFTINGS = 10

# Sec. III-A: the IMFs each noise's adaptive filter works on (1-based, inclusive).
# None = the whole signal, no EMD.
PAPER_IMFS = {
    "pli": (1, 1),
    "bw": (5, 8),
    "em": (3, 8),
    "ma": None,
}

# Also filter the EMD residue in the branches that end at IMF8 (BW: IMF5-8 + r,
# EM: IMF3-8 + r). The paper adds the residue back unfiltered (Eqs. 1-3), but about a third
# of the BW noise and an eighth of the EM noise is slower than IMF8 and sits in the
# residue, where no filter can reach it. The residue's mean (the ECG's DC offset) is
# left out of the filter input and added back. False = exactly as in the paper.
FILTER_RESIDUE = True

# ---------------------------------------------------------------- adaptive filters

# LMS grid searched by scripts/01_tune_lms.py. The reference is scaled to unit power
# inside the filter, so the step size does not depend on the scale of the noise records.
LMS_MUS = [1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]
LMS_TAPS = [1, 2, 4, 8, 16, 32, 64]

# Fig. 7 compares LMS with NLMS and RLS at "default parameters in MATLAB"
# (dsp.LMSFilter / dsp.RLSFilter): 32 taps, NLMS step 0.1, RLS forgetting factor 1,
# initial inverse covariance 1000
MATLAB_TAPS = 32
NLMS_MU = 0.1
RLS_LAMBDA = 1.0
RLS_P0 = 1000.0

# ---------------------------------------------------------------- paper numbers

# Fig. 8, read off the plot (about +-0.3 dB): SNR output at SNRin = 10 dB
PAPER_FIG8 = {
    "Proposed LMS+EMD (paper)": [24.6, 22.6, 25.0, 29.2, 23.9],
    "Article [28]": [17.9, 23.0, 20.0, 25.9, 20.4],
    "Article [21]": [16.5, 20.4, 17.9, 24.0, 18.9],
    "Article [22]": [13.9, 18.9, 15.9, 22.9, 18.5],
}

# Fig. 11, PEAF line, read off the plot (about +-0.5 dB): SNRimp vs SNRin
PAPER_FIG11_PEAF = {-5: 10.2, -2: 9.5, 0: 9.4, 3: 7.0, 6: 5.6, 10: 4.3}
