"""
Every setting of the reproduction in one place.

Paper: B. Dai and W. Bai, "Denoising ECG by adaptive filter with empirical mode decomposition".

Settings marked [PAPER] are taken from the paper as given. Settings marked [OURS] are not
given in the paper and are our choice (see README.md, "What the paper does not give").
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MITDB_DIR = ROOT / "data" / "physionet.org" / "files" / "mitdb" / "1.0.0"
NSTDB_DIR = ROOT / "data" / "physionet.org" / "files" / "nstdb" / "1.0.0"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
CACHE_DIR = ROOT / "cache"  # EMD results, so each noisy ECG is decomposed only once
TUNED_PARAMS_FILE = RESULTS_DIR / "tuned_filter_params.json"

# ------------------------------------------------------------------ signals

FS = 360                 # [PAPER] MIT-BIH sampling rate (spectra in Figs. 6, 9 go to 180 Hz)
RECORD_LENGTH = 650_000  # samples in a 30 min MIT-BIH / NSTDB record
DATA_FRACTION = 0.10     # [OURS] use 10 % of each ECG and noise record
N_SAMPLES = int(RECORD_LENGTH * DATA_FRACTION)  # 65 000 samples = 3 min 0.5 s

ECG_START = 0            # [OURS] the 10 % ECG segment starts at the beginning of the record
TEST_NOISE_START = 0     # [OURS] noise segment used for every figure
TUNE_NOISE_START = 325_000  # [OURS] a different noise segment, used only to tune the filters
ECG_CHANNEL = 0          # [OURS] MLII on almost every MIT-BIH record
NOISE_CHANNEL = 0        # [OURS] first channel of the NSTDB noise records

# [OURS, confirmed by Figs. 6, 7, 9] ECG scaling: x <- (x - mean) / max|x - mean|.
# Figs. 6 and 9 show the clean ECG at baseline ~0 with R peaks ~1 and no DC in its
# spectrum; Fig. 7's RMSE and SNRout together imply a clean ECG RMS of ~0.16.
ECG_SCALING = "zero_mean_peak_one"

PLI_FREQ = 60.0          # [PAPER] PLI is a 60 Hz sinusoid

# [OURS] How the noises are combined. Each NSTDB noise keeps its recorded amplitude (in mV,
# mean removed), so their natural ratio is kept: on the test segment BW ~25 %, EM ~47 %,
# MA ~4 % of the noise power. PLI gets the same power as BW. The sum of all noises is then
# scaled by one gain so that Eq. (4) gives exactly the requested SNRin.
PLI_POWER_LIKE = "bw"

# [PAPER] "the noises all have been shifted and passed through different filters to get
# noises that are not equal but correlated to the adaptive filters' reference noises".
# [OURS] the shift (delay in samples) and FIR filter of each noise. The adaptive filter gets
# the noise record itself as reference; the ECG gets the delayed and filtered version.
NOISE_PATHS = {
    "bw": {"delay": 5, "fir": [0.5, 0.3, 0.2]},
    "em": {"delay": 3, "fir": [0.6, 0.3, 0.1]},
    "ma": {"delay": 2, "fir": [0.7, 0.2, 0.1]},
}
# [OURS] the PLI added to the ECG is phase shifted against the 60 Hz reference
PLI_PHASE_SHIFT = 0.25 * 3.141592653589793  # rad

# ------------------------------------------------------------------ records and SNRs

FIG8_RECORDS = [119, 202, 213, 217, 234]                                       # [PAPER]
FIG10_RECORDS = [100, 103, 104, 105, 106, 111, 113, 115, 116, 121, 122, 123, 231]  # [PAPER]
FIG7_RECORDS = FIG8_RECORDS    # [OURS] Fig. 7 does not name its records: mean over Fig. 8's
FIG11_RECORDS = FIG10_RECORDS  # [OURS] Fig. 11 does not name its records: mean over Fig. 10's

FIG7_SNRS = [-5, 0, 5, 7, 10]       # [PAPER]
FIG8_SNR = 10                       # [PAPER]
FIG11_SNRS = [-5, -2, 0, 3, 6, 10]  # [PAPER]
# [PAPER] the text says Fig. 10 is at SNRin = 10 dB, but its values (~9-11 dB) match
# Fig. 11 at -5 dB (Fig. 11 at 10 dB is ~3.5-4.3 dB). We make Fig. 10 at both.
FIG10_SNRS = [-5, 10]

# [OURS] examples of Figs. 6 and 9 (the paper does not say which record or SNRin)
FIG6_EXAMPLE = {"record": 234, "snr": 5}
FIG9_EXAMPLE = {"record": 100, "snr": 5}
EXAMPLE_SAMPLES = 5000  # [PAPER] Figs. 6, 9 show 5000 samples

# [OURS] filter tuning uses records that appear in no figure (no paced records) and a
# different noise segment, so the tuned settings are not fitted to the test cases
TUNE_RECORDS = [101, 112, 117, 201, 220]
TUNE_SNRS = [-5, 0, 5, 10]

# ------------------------------------------------------------------ EMD

# [PAPER] the methods use IMF1 ... IMF8 and the residue r (Eqs. 1-3)
N_IMFS = 8
# [OURS] the paper used MATLAB; we follow MATLAB's emd() defaults: cubic spline envelopes,
# sifting stops when ||h_prev - h||^2 / ||h_prev||^2 < 0.2 or after 100 sifts.
SIFT_RELATIVE_TOLERANCE = 0.2
SIFT_MAX_ITERATIONS = 100

# [PAPER] Sec. III-A: the IMFs each noise's adaptive filter works on (1-based, inclusive).
# None = the whole signal, no EMD.
NOISE_IMFS = {"pli": (1, 1), "bw": (5, 8), "em": (3, 8), "ma": None}

# ------------------------------------------------------------------ adaptive filters

# [OURS] search grids. Every filter of every method gets its own setting, tuned on the
# held-out cases (scripts/01_tune_filters.py). The reference keeps its recorded scale (it
# does not change with SNRin), so one step size behaves the same at every SNRin.
LMS_MUS = [1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0, 3.0]
NLMS_MUS = [1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0]
RLS_LAMBDAS = [0.99, 0.995, 0.999, 0.9995, 0.9999, 1.0]
LMS_TAPS = [1, 2, 4, 8, 16, 32, 64]
RLS_TAPS = [1, 2, 4, 8, 16, 32]
RLS_P0 = 1000.0  # [OURS] initial inverse covariance P(0) = 1000 I, MATLAB's dsp.RLSFilter default
TUNING_PASSES = 2  # [OURS] coordinate-descent passes over the filters of a method
