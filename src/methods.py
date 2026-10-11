"""
Denoising structures from Dai & Bai, "Denoising ECG by adaptive filter with empirical
mode decomposition".

Each method takes the noisy ECG and a dict of reference noises keyed by noise name
('pli', 'bw', 'em', 'ma'). af(desired, reference) -> error is the adaptive filter;
the paper uses LMS with MATLAB's default parameters for every method. The EMD-based
methods also take the IMFs and residue of the noisy ECG (see src.EMD.emd_decompose).
"""
from src.adaptive_filters import LMS_filter, NLMS_filter, RLS_filter
from src.EMD import imf_sum

FILTERS = {"LMS": LMS_filter, "NLMS": NLMS_filter, "RLS": RLS_filter}


def denoise_imf_combination(noisy, reference, imfs, first, last, af=LMS_filter):
    """
    Fig. 2: adaptive-filter only the sum IMF<first>..IMF<last>, then add back the
    unused IMFs and the residue.

    first=last=None filters the whole signal without EMD.
    """
    if first is None:
        return af(noisy, reference)
    used = imf_sum(imfs, first, last)
    return noisy - used + af(used, reference)


def emd_bw_pli(refs, imfs, residue, af=LMS_filter):
    """Fig. 3 / Eq. (1): Y = IMF1' + sum(IMF2..IMF4) + IMF'58 + r."""
    imf1_d = af(imfs[0], refs["pli"])
    imf58_d = af(imf_sum(imfs, 5, 8), refs["bw"])
    return imf1_d + imf_sum(imfs, 2, 4) + imf58_d + residue


def peaf(refs, imfs, residue, af=LMS_filter):
    """
    Fig. 4(a) / Eq. (2), Parallel EMD Adaptive Filter.

    X' = IMF1' + IMF2 + IMF'38 + IMF'58 + r - sum(IMF5..IMF8), then an MA filter on X'.
    """
    imf1_d = af(imfs[0], refs["pli"])
    imf38_d = af(imf_sum(imfs, 3, 8), refs["em"])
    imf58_d = af(imf_sum(imfs, 5, 8), refs["bw"])
    x_prime = imf1_d + imfs[1] + imf38_d + imf58_d + residue - imf_sum(imfs, 5, 8)
    return af(x_prime, refs["ma"])


def seaf(refs, imfs, residue, af=LMS_filter):
    """
    Fig. 4(b) / Eq. (3), Staged EMD Adaptive Filter.

    BW filter on IMF5..8 -> IMF'58; EM filter on IMF3 + IMF4 + IMF'58 -> IMF''38;
    X' = IMF1' + IMF2 + IMF''38 + r, then an MA filter on X'.
    """
    imf1_d = af(imfs[0], refs["pli"])
    imf58_d = af(imf_sum(imfs, 5, 8), refs["bw"])
    imf38_dd = af(imfs[2] + imfs[3] + imf58_d, refs["em"])
    x_prime = imf1_d + imfs[1] + imf38_dd + residue
    return af(x_prime, refs["ma"])


def sdaf(noisy, refs, af=LMS_filter):
    """
    Fig. 5, Staged Direct Adaptive Filter (Thakor & Zhu [13] plus an MA layer), no EMD.

    PLI and BW filters run in parallel on the noisy ECG and both noise estimates are
    subtracted. The result then goes through the EM filter and the MA filter.
    """
    pli_estimate = noisy - af(noisy, refs["pli"])
    bw_estimate = noisy - af(noisy, refs["bw"])
    x = noisy - pli_estimate - bw_estimate
    x = af(x, refs["em"])
    return af(x, refs["ma"])


def pdaf(noisy, refs, af=LMS_filter):
    """
    Parallel Direct Adaptive Filter: all noises treated as one noise, one adaptive
    filter on the noisy ECG (Fig. 1) with the sum of the reference noises.
    """
    return af(noisy, sum(refs.values()))


def run_all_four(noisy, refs, imfs, residue, af=LMS_filter):
    """Run PEAF, SEAF, PDAF and SDAF on one signal; returns {name: denoised}."""
    return {
        "PEAF": peaf(refs, imfs, residue, af),
        "SEAF": seaf(refs, imfs, residue, af),
        "PDAF": pdaf(noisy, refs, af),
        "SDAF": sdaf(noisy, refs, af),
    }
