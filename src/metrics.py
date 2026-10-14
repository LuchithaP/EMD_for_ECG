"""Performance measures, Eqs. (4)-(6) of the paper. x_c = clean, x_n = noisy, x_d = denoised."""
import numpy as np


def snr(clean, x):
    """Eq. (4): 10 log10( sum x_c^2 / sum (x - x_c)^2 )."""
    return 10 * np.log10(np.sum(clean**2) / np.sum((x - clean) ** 2))


def rmse(clean, x):
    """Eq. (5): sqrt( sum (x - x_c)^2 / N )."""
    return np.sqrt(np.mean((x - clean) ** 2))


def snr_imp(clean, noisy, denoised):
    """Eq. (6): SNR_output - SNR_input = 10 log10( sum (x_n - x_c)^2 / sum (x_d - x_c)^2 )."""
    return 10 * np.log10(np.sum((noisy - clean) ** 2) / np.sum((denoised - clean) ** 2))
