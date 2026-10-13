"""Performance measures, Eqs. (4)-(6) of the paper."""
import numpy as np


def snr(clean, x):
    """Eq. (4): 10 log10( sum clean^2 / sum (x - clean)^2 )."""
    return 10 * np.log10(np.sum(clean**2) / np.sum((x - clean) ** 2))


def rmse(clean, x):
    """Eq. (5)."""
    return np.sqrt(np.mean((x - clean) ** 2))


def snr_imp(clean, noisy, denoised):
    """Eq. (6): SNR_output - SNR_input."""
    return snr(clean, denoised) - snr(clean, noisy)
