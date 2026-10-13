"""
Test signals (Sec. IV of the paper): MIT-BIH Arrhythmia ECG + MIT-BIH Noise Stress Test
noises (BW, EM, MA) + 60 Hz power line interference (PLI).
"""
import numpy as np
import wfdb

from src.config import (FS, MITDB_DIR, N_SAMPLES, NOISE_PATHS, NSTDB_DIR, PLI_FREQ,
                        TEST_NOISE_START)


def load_ecg(record, mode="raw"):
    """First N_SAMPLES of channel 0 of an MIT-BIH record. mode "norm": zero mean, unit std."""
    x = wfdb.rdrecord(str(MITDB_DIR / str(record)), sampto=N_SAMPLES).p_signal[:, 0]
    if mode == "norm":
        x = (x - x.mean()) / x.std()
    return x


def load_noise(name, start=TEST_NOISE_START):
    """N_SAMPLES of an NSTDB noise record ('bw', 'em' or 'ma'), from sample `start`."""
    rec = wfdb.rdrecord(str(NSTDB_DIR / name), sampfrom=start, sampto=start + N_SAMPLES)
    return rec.p_signal[:, 0]


def make_pli(amplitude, n=N_SAMPLES):
    """60 Hz sinusoid."""
    t = np.arange(n) / FS
    return amplitude * np.sin(2 * np.pi * PLI_FREQ * t)


def shift_and_filter(reference, delay, taps):
    """The noise that reaches the ECG: the reference delayed and FIR filtered."""
    h = np.concatenate([np.zeros(delay), taps])
    return np.convolve(reference, h)[: len(reference)]


def snr_gain(clean, noise, snr_db):
    """Gain that makes 10 log10(sum clean^2 / sum (gain * noise)^2) equal snr_db (Eq. 4)."""
    return np.sqrt(np.sum(clean**2) / (np.sum(noise**2) * 10 ** (snr_db / 10)))


def make_case(record, noises, snr_db, ecg_mode="raw", noise_start=TEST_NOISE_START):
    """
    One noisy ECG.

    noises: any of "bw", "em", "ma", "pli".
    - BW, EM, MA: the reference is the NSTDB record; the noise added to the ECG is the
      shifted and filtered reference (NOISE_PATHS).
    - PLI: 60 Hz sinusoid with the same power as the BW noise; its reference is the
      PLI itself (the paper shifts and filters only BW, EM and MA).
    The total noise is scaled so that the input SNR (Eq. 4) equals snr_db.

    Returns a dict: clean, noisy, refs ({noise name: reference}).
    """
    clean = load_ecg(record, ecg_mode)
    added, refs = [], {}
    for name in ("bw", "em", "ma"):
        if name in noises:
            refs[name] = load_noise(name, noise_start)
            added.append(shift_and_filter(refs[name], *NOISE_PATHS[name]))
    if "pli" in noises:
        bw = shift_and_filter(load_noise("bw", noise_start), *NOISE_PATHS["bw"])
        refs["pli"] = make_pli(np.sqrt(2 * np.mean(bw**2)))
        added.append(refs["pli"])

    total = sum(added)
    noisy = clean + total * snr_gain(clean, total, snr_db)
    return {"clean": clean, "noisy": noisy, "refs": refs}
