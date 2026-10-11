"""
Adaptive noise cancellers (Fig. 1 of the paper) and the metrics of Eqs. (4)-(6).

The paper uses "default parameters in MATLAB" for LMS, NLMS and RLS, so the defaults
here are those of dsp.LMSFilter and dsp.RLSFilter:
- LMS:  Length 32, StepSize 0.1, zero initial weights
- NLMS: Length 32, StepSize 0.1, zero initial weights
- RLS:  Length 32, ForgettingFactor 1, InitialInverseCovariance 1 (identity), zero weights

Each filter sees the reference through a tapped delay line with zero initial states,
so the output has the same length as the input and stays sample-aligned. The loops
are compiled with numba; a full 30-minute MIT-BIH record takes well under a second.
"""
import numpy as np
from numba import njit

FILTER_ORDER = 32


@njit(cache=True)
def _lms(d, x, mu, L, normalized):
    w = np.zeros(L)
    u = np.zeros(L)
    e = np.empty(len(d))
    eps = np.finfo(np.float64).eps
    for n in range(len(d)):
        u[1:] = u[:-1]
        u[0] = x[n]
        e[n] = d[n] - np.dot(w, u)
        if normalized:
            w += mu * e[n] * u / (eps + np.dot(u, u))
        else:
            w += mu * e[n] * u
    return e


@njit(cache=True)
def _rls(d, x, lam, L, p0):
    w = np.zeros(L)
    u = np.zeros(L)
    P = np.eye(L) * p0
    e = np.empty(len(d))
    for n in range(len(d)):
        u[1:] = u[:-1]
        u[0] = x[n]
        Pu = P @ u
        k = Pu / (lam + np.dot(u, Pu))
        e[n] = d[n] - np.dot(w, u)
        w += k * e[n]
        P = (P - np.outer(k, Pu)) / lam
    return e


def _trim(noisy_signal, reference_signal, N):
    N = min(len(noisy_signal), len(reference_signal)) if not N else N
    return np.asarray(noisy_signal[:N], float), np.asarray(reference_signal[:N], float)


def LMS_filter(noisy_signal, reference_signal, mu=0.1, filter_order=FILTER_ORDER, N=None):
    """
    Apply LMS adaptive noise cancellation (Fig. 1 of the paper).

    Parameters:
    noisy_signal (numpy.ndarray): The noisy input signal (desired signal d).
    reference_signal (numpy.ndarray): The reference noise signal.
    mu (float): The step size for the LMS algorithm.
    filter_order (int): The order of the adaptive filter (number of taps).
    N (int): The number of samples to process (default: all).

    Returns:
    numpy.ndarray: The error signal e = d - y, i.e. the denoised signal.
    """
    d, ref = _trim(noisy_signal, reference_signal, N)
    return _lms(d, ref, mu, filter_order, False)


def NLMS_filter(noisy_signal, reference_signal, mu=0.1, filter_order=FILTER_ORDER, N=None):
    """
    Apply NLMS adaptive noise cancellation.

    Parameters:
    noisy_signal (numpy.ndarray): The noisy input signal.
    reference_signal (numpy.ndarray): The reference signal (noise).
    mu (float): The normalised step size.
    filter_order (int): The order of the adaptive filter.
    N (int): The number of samples to process (default: all).

    Returns:
    numpy.ndarray: The error signal, i.e. the denoised signal.
    """
    d, ref = _trim(noisy_signal, reference_signal, N)
    return _lms(d, ref, mu, filter_order, True)


def RLS_filter(noisy_signal, reference_signal, mu=1.0, filter_order=FILTER_ORDER, eps=1.0, N=None):
    """
    RLS adaptive noise cancellation.

    Parameters:
    noisy_signal : (np.ndarray) Noisy signal. This is the desired signal d(n).
    reference_signal : (np.ndarray) Reference noise correlated with the noise in
        noisy_signal.
    mu : (float) RLS forgetting factor.
    filter_order : (int) Number of adaptive filter taps.
    eps : (float) The initial inverse covariance matrix is identity / eps.
    N : (int) The number of samples to process (default: all).

    Returns:
    denoised_signal : (np.ndarray) Error signal e(n) = d(n) - y(n).
    """
    d, ref = _trim(noisy_signal, reference_signal, N)
    return _rls(d, ref, mu, filter_order, 1.0 / eps)


def snr_db(clean_signal, test_signal):
    """Eq. (4): 10 log10( sum xc^2 / sum (x - xc)^2 )."""
    return 10 * np.log10(np.sum(clean_signal**2) / np.sum((test_signal - clean_signal) ** 2))


def rmse(clean_signal, test_signal):
    """Eq. (5)."""
    return np.sqrt(np.mean((test_signal - clean_signal) ** 2))


def snr_improvement(clean_signal, noisy_signal, denoised_signal):
    """Eq. (6): SNR_output - SNR_input."""
    return snr_db(clean_signal, denoised_signal) - snr_db(clean_signal, noisy_signal)


def evaluate_filter_performance(clean_signal, denoised_signal, noise_signal):
    """
    Evaluate denoising performance (Eqs. 4-6 of the paper).

    Parameters:
    clean_signal (numpy.ndarray): The original clean signal.
    denoised_signal (numpy.ndarray): The denoised signal after filtering.
    noise_signal (numpy.ndarray): The noise that was added to the clean signal.

    Returns:
    tuple: SNR, RMSE, and SNR improvement.
    """
    n = len(denoised_signal)
    if n == 0:
        raise ValueError("denoised_signal must contain at least one sample.")
    if len(clean_signal) < n or len(noise_signal) < n:
        raise ValueError(
            "clean_signal and noise_signal must be at least as long as denoised_signal."
        )

    # Shorter outputs (e.g. from filters that drop the first taps) are aligned on the end.
    clean_signal = clean_signal[-n:]
    noise_signal = noise_signal[-n:]

    SNR = snr_db(clean_signal, denoised_signal)
    RMSE = rmse(clean_signal, denoised_signal)
    SNR_impr = snr_improvement(clean_signal, clean_signal + noise_signal, denoised_signal)
    return SNR, RMSE, SNR_impr
