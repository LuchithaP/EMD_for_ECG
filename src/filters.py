"""
Adaptive noise cancellers (Fig. 1 of the paper). The filter estimates the noise in the
desired signal d from a reference noise x: y(n) = w . u(n), with u(n) the last `taps`
reference samples. The output is the error e = d - y, the denoised signal.

Update rules (as in MATLAB dsp.LMSFilter / dsp.RLSFilter):
- LMS:  w += mu e u
- NLMS: w += mu e u / (eps + u.u)
- RLS:  forgetting factor lam, P(0) = p0 I

The sample loops are compiled with numba, with numpy's error model: a diverging filter
returns inf / NaN (caught by diverged()) instead of raising.
"""
import numpy as np
from numba import njit


@njit(cache=True, error_model="numpy")
def _push(u, value):
    """Shift the tap-delay line by one sample and put `value` first."""
    for k in range(len(u) - 1, 0, -1):
        u[k] = u[k - 1]
    u[0] = value


@njit(cache=True, error_model="numpy")
def _lms(d, x, mu, taps, normalized):
    w = np.zeros(taps)
    u = np.zeros(taps)  # newest reference sample first
    e = np.empty(len(d))
    for n in range(len(d)):
        _push(u, x[n])
        y, power = 0.0, 0.0
        for k in range(taps):
            y += w[k] * u[k]
            power += u[k] * u[k]
        e[n] = d[n] - y
        step = mu / (1e-12 + power) if normalized else mu
        for k in range(taps):
            w[k] += step * e[n] * u[k]
    return e


@njit(cache=True, error_model="numpy")
def _rls(d, x, lam, taps, p0):
    w = np.zeros(taps)
    u = np.zeros(taps)
    P = np.eye(taps) * p0
    Pu = np.zeros(taps)
    e = np.empty(len(d))
    for n in range(len(d)):
        _push(u, x[n])
        y, denom = 0.0, lam
        for i in range(taps):
            y += w[i] * u[i]
            s = 0.0
            for j in range(taps):
                s += P[i, j] * u[j]
            Pu[i] = s
            denom += u[i] * s
        e[n] = d[n] - y
        for i in range(taps):  # k = Pu / denom;  w += k e;  P = (P - k Pu^T) / lam
            w[i] += Pu[i] / denom * e[n]
        for i in range(taps):
            for j in range(taps):
                P[i, j] = (P[i, j] - Pu[i] * Pu[j] / denom) / lam
    return e


@njit(cache=True, error_model="numpy")
def _lms2(d, x1, x2, mu1, mu2, taps1, taps2):
    w1, u1 = np.zeros(taps1), np.zeros(taps1)
    w2, u2 = np.zeros(taps2), np.zeros(taps2)
    e = np.empty(len(d))
    for n in range(len(d)):
        _push(u1, x1[n])
        _push(u2, x2[n])
        y = 0.0
        for k in range(taps1):
            y += w1[k] * u1[k]
        for k in range(taps2):
            y += w2[k] * u2[k]
        e[n] = d[n] - y
        for k in range(taps1):
            w1[k] += mu1 * e[n] * u1[k]
        for k in range(taps2):
            w2[k] += mu2 * e[n] * u2[k]
    return e


def lms(d, ref, mu, taps):
    """LMS noise canceller, returns the denoised signal e = d - y."""
    return _lms(np.asarray(d, float), np.asarray(ref, float), float(mu), int(taps), False)


def nlms(d, ref, mu, taps):
    """Normalized LMS noise canceller."""
    return _lms(np.asarray(d, float), np.asarray(ref, float), float(mu), int(taps), True)


def rls(d, ref, lam, taps, p0):
    """RLS noise canceller."""
    return _rls(np.asarray(d, float), np.asarray(ref, float), float(lam), int(taps), float(p0))


def lms_parallel(d, ref1, ref2, s1, s2):
    """
    Two LMS filters in parallel on the same signal, sharing one error
    e = d - y1 - y2 (the PLI + BW stage of SDAF, Fig. 5). s1, s2: {"mu", "taps"}.
    """
    return _lms2(np.asarray(d, float), np.asarray(ref1, float), np.asarray(ref2, float),
                 float(s1["mu"]), float(s2["mu"]), int(s1["taps"]), int(s2["taps"]))


ALGORITHMS = {"LMS": lms, "NLMS": nlms, "RLS": rls}


def diverged(d, e):
    """True if the filter blew up: non-finite output or far more power than its input."""
    with np.errstate(over="ignore", invalid="ignore"):
        return not np.all(np.isfinite(e)) or np.mean(e**2) > 100 * np.mean(d**2)
