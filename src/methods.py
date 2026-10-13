"""
Denoising structures of the paper (Sec. III).

Every adaptive filter is called as f(d, noise): it removes `noise` ("pli", "bw", "em",
"ma", or "all" = the sum of all references) from the signal d. make_filter builds f
from the reference noises and the LMS settings, so each noise gets its own step size
and number of taps.

EMD-based methods use the IMFs of the noisy ECG (imfs[0] = IMF1) and the residue r.
With FILTER_RESIDUE (src/config.py) the BW and EM branches also filter the residue.
"""
from src.config import FILTER_RESIDUE, N_IMFS
from src.emd import imf_sum
from src.filters import lms


def make_filter(refs, settings, algorithm=lms):
    """
    f(d, noise) -> denoised d.

    settings: {noise: {"mu": ..., "taps": ...}} for LMS / NLMS, or
              {noise: {"lam": ..., "taps": ..., "p0": ...}} for RLS.
    """
    def f(d, noise):
        ref = sum(refs.values()) if noise == "all" else refs[noise]
        return algorithm(d, ref, **settings[noise])
    return f


def branch(imfs, r, first, last):
    """
    Filter input for IMF<first>..IMF<last>. A branch that ends at IMF8 also gets the
    residue (minus its mean) if FILTER_RESIDUE.
    """
    x = imf_sum(imfs, first, last)
    if FILTER_RESIDUE and last == N_IMFS:
        x = x + r - r.mean()
    return x


def untouched_residue(r):
    """The part of the residue no filter sees: all of it, or only its mean if FILTER_RESIDUE."""
    return r.mean() if FILTER_RESIDUE else r


def fig2(noisy, imfs, r, imf_range, f, noise):
    """
    Fig. 2: filter only the IMFs in imf_range (first, last), then add back the other
    IMFs and the residue. imf_range None filters the whole signal (no EMD).
    """
    if imf_range is None:
        return f(noisy, noise)
    used = branch(imfs, r, *imf_range)
    return noisy - used + f(used, noise)


def emd_bw_pli(imfs, r, f):
    """Fig. 3 / Eq. (1): Y = IMF1' + IMF2 + IMF3 + IMF4 + IMF'58 + r."""
    imf1_d = f(imfs[0], "pli")
    imf58_d = f(branch(imfs, r, 5, 8), "bw")
    return imf1_d + imf_sum(imfs, 2, 4) + imf58_d + untouched_residue(r)


def direct_bw_pli(noisy, f):
    """BW + PLI without EMD: PLI and BW filters in parallel on the noisy ECG (Thakor & Zhu [13])."""
    pli_estimate = noisy - f(noisy, "pli")
    bw_estimate = noisy - f(noisy, "bw")
    return noisy - pli_estimate - bw_estimate


def peaf(imfs, r, f_emd, f_direct):
    """
    Fig. 4(a) / Eq. (2), Parallel EMD Adaptive Filter.

    X' = IMF1' + IMF2 + IMF'38 + IMF'58 + r - (IMF5 + ... + IMF8)
    Y  = MA filter on X' (MA uses no EMD).
    """
    imf1_d = f_emd(imfs[0], "pli")
    imf38_d = f_emd(branch(imfs, r, 3, 8), "em")
    imf58 = branch(imfs, r, 5, 8)
    imf58_d = f_emd(imf58, "bw")
    # IMF5-8 (and the filtered residue) are in both branches: subtract one copy
    x = imf1_d + imfs[1] + imf38_d + imf58_d - imf58 + untouched_residue(r)
    return f_direct(x, "ma")


def seaf(imfs, r, f_emd, f_direct):
    """
    Fig. 4(b) / Eq. (3), Staged EMD Adaptive Filter.

    IMF'58  = BW filter on IMF5 + ... + IMF8
    IMF''38 = EM filter on IMF3 + IMF4 + IMF'58
    X' = IMF1' + IMF2 + IMF''38 + r
    Y  = MA filter on X'.
    """
    imf1_d = f_emd(imfs[0], "pli")
    imf58_d = f_emd(branch(imfs, r, 5, 8), "bw")
    imf38_dd = f_emd(imfs[2] + imfs[3] + imf58_d, "em")
    x = imf1_d + imfs[1] + imf38_dd + untouched_residue(r)
    return f_direct(x, "ma")


def sdaf(noisy, f_direct):
    """
    Fig. 5, Staged Direct Adaptive Filter, no EMD: PLI and BW filters in parallel,
    then the EM filter, then the MA filter.
    """
    x = direct_bw_pli(noisy, f_direct)
    x = f_direct(x, "em")
    return f_direct(x, "ma")


def pdaf(noisy, f_direct):
    """Parallel Direct Adaptive Filter: all noises as one, one filter with the summed reference."""
    return f_direct(noisy, "all")
