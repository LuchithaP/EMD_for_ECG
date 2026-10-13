"""
Empirical mode decomposition with PyEMD (package EMD-signal), with a fixed number of
sifting iterations per IMF (EMD_SIFTINGS, see src/config.py). Under 1 s per signal.
"""
import numpy as np
from PyEMD import EMD

from src.config import EMD_SIFTINGS, N_IMFS


def decompose(x):
    """
    Decompose x into N_IMFS IMFs plus a residue.

    Returns imfs (N_IMFS x len(x), imfs[0] = IMF1, highest frequency) and residue,
    with x == imfs.sum(0) + residue. Missing IMFs (if EMD stops early) are zeros.
    """
    x = np.asarray(x, dtype=float)
    emd = EMD(FIXE=EMD_SIFTINGS)
    emd.emd(x, max_imf=N_IMFS)
    found, _ = emd.get_imfs_and_residue()
    imfs = np.zeros((N_IMFS, len(x)))
    imfs[: len(found)] = found[:N_IMFS]
    return imfs, x - imfs.sum(axis=0)


def imf_sum(imfs, first, last):
    """IMF<first> + ... + IMF<last>, 1-based like the paper (IMF5-8 = imf_sum(imfs, 5, 8))."""
    return imfs[first - 1 : last].sum(axis=0)
