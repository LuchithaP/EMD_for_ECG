"""
Empirical mode decomposition with the default settings of MATLAB's `emd`.

The paper gives no EMD settings. Since it uses MATLAB defaults for the adaptive
filters, the same is assumed here:
- cubic spline envelopes ('spline', not-a-knot end conditions)
- sifting stops when the Cauchy-type relative tolerance
  sum((h_prev - h)^2) / sum(h_prev^2) < 0.2, or after 100 sifting iterations
- decomposition stops when the residual has <= 1 extremum, or when
  10*log10(||x|| / ||r||) >= 20
The number of IMFs is fixed at 8, because the paper uses IMF1..IMF8 plus the residue.
The signal end points are used as envelope knots.
"""
import numpy as np
from scipy.interpolate import CubicSpline

N_IMFS = 8
SIFT_RELATIVE_TOLERANCE = 0.2
SIFT_MAX_ITERATIONS = 100
MAX_NUM_EXTREMA = 1
MAX_ENERGY_RATIO = 20


def _extrema(h):
    """Indices of local maxima and minima."""
    d = np.diff(h)
    maxima = np.flatnonzero((d[:-1] > 0) & (d[1:] <= 0)) + 1
    minima = np.flatnonzero((d[:-1] < 0) & (d[1:] >= 0)) + 1
    return maxima, minima


def _envelope_mean(h, t):
    """Mean of the upper and lower spline envelopes, or None if h has no maxima or minima."""
    maxima, minima = _extrema(h)
    if len(maxima) == 0 or len(minima) == 0:
        return None
    ends = [0], [len(h) - 1]
    upper_knots = np.concatenate([ends[0], maxima, ends[1]])
    lower_knots = np.concatenate([ends[0], minima, ends[1]])
    upper = CubicSpline(upper_knots, h[upper_knots])(t)
    lower = CubicSpline(lower_knots, h[lower_knots])(t)
    return (upper + lower) / 2


def emd_decompose(signal, n_imfs=N_IMFS):
    """
    Decompose a signal into exactly n_imfs IMFs plus a residue.

    If the decomposition stops early, the missing IMFs are returned as zeros, so IMF
    indices always mean the same thing.

    Returns:
    - imfs: (n_imfs, N) array; imfs[0] is IMF1 (highest frequency)
    - residue: (N,) array, with signal == imfs.sum(0) + residue
    """
    x = np.asarray(signal, float)
    t = np.arange(len(x))
    imfs = np.zeros((n_imfs, len(x)))
    r = x.copy()
    for i in range(n_imfs):
        n_extrema = sum(len(e) for e in _extrema(r))
        energy_ratio = 10 * np.log10(np.linalg.norm(x) / np.linalg.norm(r))
        if n_extrema <= MAX_NUM_EXTREMA or energy_ratio >= MAX_ENERGY_RATIO:
            break
        h = r.copy()
        for _ in range(SIFT_MAX_ITERATIONS):
            m = _envelope_mean(h, t)
            if m is None:
                break
            tolerance = np.sum(m**2) / np.sum(h**2)
            h = h - m
            if tolerance < SIFT_RELATIVE_TOLERANCE:
                break
        imfs[i] = h
        r = r - h
    return imfs, r


def imf_sum(imfs, first, last):
    """Sum of IMF<first>..IMF<last> using the paper's 1-based numbering (inclusive)."""
    return imfs[first - 1 : last].sum(axis=0)
