"""
Denoising structures of the paper (Sec. III).

Every method takes the noisy ECG, its IMFs (imfs[0] = IMF1) and residue r, and a
FilterBank f; f(d, noise) runs the adaptive filter of `noise` on the signal d and returns
the denoised d. Each noise has its own filter setting (step size, taps).

    METHODS[name] -> Method(function, algorithm, filter names)
    denoise(name, case, imfs, r, params) -> denoised ECG
"""
from dataclasses import dataclass

import numpy as np

from src.config import RLS_P0
from src.emd import imf_sum
from src.filters import ALGORITHMS, lms_parallel


class FilterBank:
    """The adaptive filters of one method: f(d, noise) -> d with that noise removed."""

    def __init__(self, algorithm, refs, params):
        self.algorithm, self.refs, self.params = algorithm, refs, params

    def reference(self, noise):
        """Reference of one noise; "all" = the sum of all references (PDAF)."""
        return np.sum(list(self.refs.values()), axis=0) if noise == "all" else self.refs[noise]

    def __call__(self, d, noise):
        settings = dict(self.params[noise])
        if self.algorithm == "RLS":
            settings.setdefault("p0", RLS_P0)
        return ALGORITHMS[self.algorithm](d, self.reference(noise), **settings)

    def parallel(self, d, noise1, noise2):
        """Two LMS filters on the same signal with one shared error (Fig. 5)."""
        return lms_parallel(d, self.refs[noise1], self.refs[noise2],
                            self.params[noise1], self.params[noise2])


# ------------------------------------------------------------------ Sec. III-A


def fig2(noisy, imfs, r, imf_range, f, noise):
    """
    Fig. 2: filter the sum of the IMFs in imf_range = (first, last), then add back the
    other IMFs and the residue: Y = noisy - used + f(used). None filters the whole signal.
    """
    if imf_range is None:
        return f(noisy, noise)
    used = imf_sum(imfs, *imf_range)
    return noisy - used + f(used, noise)


# ------------------------------------------------------------------ BW + PLI


def eq1(noisy, imfs, r, f):
    """Fig. 3 / Eq. (1): Y = IMF1' + IMF2 + IMF3 + IMF4 + IMF'58 + r."""
    return f(imfs[0], "pli") + imf_sum(imfs, 2, 4) + f(imf_sum(imfs, 5, 8), "bw") + r


# ------------------------------------------------------------------ BW + PLI + EM + MA


def peaf(noisy, imfs, r, f):
    """
    Parallel EMD Adaptive Filter, Fig. 4(a) / Eq. (2):
    X' = IMF1' + IMF2 + IMF'38 + IMF'58 + r - (IMF5 + ... + IMF8),  Y = MA filter on X'.
    """
    imf58 = imf_sum(imfs, 5, 8)
    x = (f(imfs[0], "pli") + imfs[1] + f(imf_sum(imfs, 3, 8), "em") + f(imf58, "bw")
         + r - imf58)
    return f(x, "ma")


def seaf(noisy, imfs, r, f):
    """
    Staged EMD Adaptive Filter, Fig. 4(b) / Eq. (3):
    IMF'58 = BW filter on IMF5~8,  IMF''38 = EM filter on IMF3 + IMF4 + IMF'58,
    X' = IMF1' + IMF2 + IMF''38 + r,  Y = MA filter on X'.
    """
    imf58_d = f(imf_sum(imfs, 5, 8), "bw")
    imf38_dd = f(imfs[2] + imfs[3] + imf58_d, "em")
    x = f(imfs[0], "pli") + imfs[1] + imf38_dd + r
    return f(x, "ma")


def sdaf(noisy, imfs, r, f):
    """
    Staged Direct Adaptive Filter, Fig. 5 (no EMD): PLI and BW filters in parallel on the
    noisy ECG (Thakor & Zhu [13]), then the EM filter, then the MA filter.
    """
    x = f.parallel(noisy, "pli", "bw")
    return f(f(x, "em"), "ma")


def pdaf(noisy, imfs, r, f):
    """Parallel Direct Adaptive Filter: all noises as one, one filter on the noisy ECG (Fig. 1)."""
    return f(noisy, "all")
 

# ------------------------------------------------------------------ registry


@dataclass(frozen=True)
class Method:
    function: callable
    algorithm: str  # "LMS", "NLMS" or "RLS"
    filters: tuple  # names of its adaptive filters, in signal-flow order
    uses_emd: bool = True


METHODS = {
    # BW + PLI (Figs. 6-8)
    "EMD+LMS": Method(eq1, "LMS", ("pli", "bw")),
    "EMD+NLMS": Method(eq1, "NLMS", ("pli", "bw")),
    "EMD+RLS": Method(eq1, "RLS", ("pli", "bw")),
    # BW + PLI + EM + MA (Figs. 9-11)
    "PEAF": Method(peaf, "LMS", ("pli", "bw", "em", "ma")),
    "SEAF": Method(seaf, "LMS", ("pli", "bw", "em", "ma")),
    "PDAF": Method(pdaf, "LMS", ("all",), uses_emd=False),
    "SDAF": Method(sdaf, "LMS", ("pli", "bw", "em", "ma"), uses_emd=False),
}
BW_PLI_METHODS = ["EMD+LMS", "EMD+NLMS", "EMD+RLS"]
FOUR_NOISE_METHODS = ["PEAF", "SEAF", "PDAF", "SDAF"]


def denoise(name, case, imfs, r, params):
    """Run method `name` on one case with filter settings params = {filter: settings}."""
    m = METHODS[name]
    return m.function(case["noisy"], imfs, r, FilterBank(m.algorithm, case["refs"], params))
