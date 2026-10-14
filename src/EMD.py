"""
Empirical mode decomposition (Huang et al. 1998), following MATLAB's emd() defaults
(the paper used MATLAB):
- envelopes: cubic splines through the maxima / minima (extrema mirrored at both ends),
- sifting stops when ||h_prev - h||^2 / ||h_prev||^2 < SIFT_RELATIVE_TOLERANCE (0.2) or
  after SIFT_MAX_ITERATIONS (100) sifts,
- the decomposition stops after N_IMFS (8) IMFs, or earlier when the residue has fewer
  than 3 extrema (missing IMFs are zeros).

decompose(x) -> imfs (N_IMFS x len(x), imfs[0] = IMF1, highest frequency), residue r,
with x == imfs.sum(0) + r.
"""
import hashlib
import os

import numpy as np
from scipy.interpolate import CubicSpline

from src.config import CACHE_DIR, N_IMFS, SIFT_MAX_ITERATIONS, SIFT_RELATIVE_TOLERANCE


def extrema(x):
    """Indices of the local maxima and minima of x (middle of a flat top / bottom)."""
    d = np.diff(x)
    steps = np.nonzero(d)[0]  # skip flat parts
    s = np.sign(d[steps])
    turn = np.nonzero(s[:-1] != s[1:])[0]
    pos = (steps[turn] + 1 + steps[turn + 1]) // 2
    is_max = s[turn] > 0
    return pos[is_max], pos[~is_max]


def envelope(x, idx, n_mirror=2):
    """Cubic spline through x[idx], with the first / last n_mirror extrema mirrored at the ends."""
    n = len(x)
    left, right = idx[:n_mirror][::-1], idx[-n_mirror:][::-1]
    t = np.concatenate([-left, idx, 2 * (n - 1) - right])
    v = x[np.concatenate([left, idx, right])]
    t, first = np.unique(t, return_index=True)
    return CubicSpline(t, v[first])(np.arange(n))


def sift(r):
    """One IMF of r."""
    h = r.copy()
    for _ in range(SIFT_MAX_ITERATIONS):
        maxima, minima = extrema(h)
        if len(maxima) < 2 or len(minima) < 2:
            break
        mean = (envelope(h, maxima) + envelope(h, minima)) / 2
        tolerance = np.sum(mean**2) / np.sum(h**2)
        h = h - mean
        if tolerance < SIFT_RELATIVE_TOLERANCE:
            break
    return h


def decompose(x):
    x = np.asarray(x, dtype=float)
    imfs = np.zeros((N_IMFS, len(x)))
    r = x.copy()
    for k in range(N_IMFS):
        maxima, minima = extrema(r)
        if len(maxima) + len(minima) < 3:
            break
        imfs[k] = sift(r)
        r = r - imfs[k]
    return imfs, r


def decompose_cached(x):
    """decompose(x), stored in CACHE_DIR under a hash of x."""
    key = hashlib.sha1(np.ascontiguousarray(x, dtype=float).tobytes()).hexdigest()[:16]
    path = CACHE_DIR / f"emd_{key}.npz"
    if path.exists():
        data = np.load(path)
        return data["imfs"], data["residue"]
    imfs, r = decompose(x)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    with open(tmp, "wb") as fh:
        np.savez(fh, imfs=imfs, residue=r)
    os.replace(tmp, path)  # atomic: parallel workers never read a half-written file
    return imfs, r


def imf_sum(imfs, first, last):
    """IMF<first> + ... + IMF<last>, 1-based like the paper (IMF5~8 = imf_sum(imfs, 5, 8))."""
    return imfs[first - 1 : last].sum(axis=0)
