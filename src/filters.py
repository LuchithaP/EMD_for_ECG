"""
Adaptive noise cancellers (Fig. 1 of the paper): the filter estimates the noise in the
desired signal d from a reference noise, and the output is the error e = d - y.

The reference is scaled to unit power before filtering. LMS convergence depends on
mu * (reference power), and the reference power changes with the record and the SNR, so
without this scaling no single step size works everywhere. NLMS is unaffected by the
scaling; RLS uses it so that its initial covariance means the same on every signal.

The sample loops are compiled with numba.
"""
import numpy as np
from numba import njit


def unit_power(ref):
    return ref / np.sqrt(np.mean(ref**2))


@njit(cache=True)
def _lms(d, x, mu, taps, normalized):
    w = np.zeros(taps)
    u = np.zeros(taps)  # last `taps` reference samples, newest first
    e = np.zeros(len(d))
    for n in range(len(d)):
        u[1:] = u[:-1].copy()
        u[0] = x[n]
        e[n] = d[n] - np.dot(w, u)
        step = mu / (1e-12 + np.dot(u, u)) if normalized else mu
        w += step * e[n] * u
    return e


@njit(cache=True)
def _rls(d, x, lam, taps, p0):
    w = np.zeros(taps)
    u = np.zeros(taps)
    P = np.eye(taps) * p0
    e = np.zeros(len(d))
    for n in range(len(d)):
        u[1:] = u[:-1].copy()
        u[0] = x[n]
        Pu = P @ u
        k = Pu / (lam + np.dot(u, Pu))
        e[n] = d[n] - np.dot(w, u)
        w += k * e[n]
        P = (P - np.outer(k, Pu)) / lam
    return e


def lms(d, ref, mu, taps):
    """LMS noise canceller. Returns the denoised signal e = d - y."""
    return _lms(np.asarray(d, float), unit_power(ref), mu, taps, False)


def nlms(d, ref, mu, taps):
    """Normalized LMS noise canceller."""
    return _lms(np.asarray(d, float), unit_power(ref), mu, taps, True)


def rls(d, ref, lam, taps, p0):
    """RLS noise canceller: forgetting factor lam, initial inverse covariance p0 * I."""
    return _rls(np.asarray(d, float), unit_power(ref), lam, taps, p0)


def diverged(d, e):
    """True if the filter blew up: non-finite output or far more power than its input."""
    return not np.all(np.isfinite(e)) or np.mean(e**2) > 100 * np.mean(d**2)
