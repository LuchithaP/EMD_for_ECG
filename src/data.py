"""
Test signals (Sec. IV): MIT-BIH Arrhythmia ECG + MIT-BIH Noise Stress Test noises (BW, EM,
MA) + 60 Hz power line interference (PLI).

A "case" is one noisy ECG: make_case(record, noises, snr) returns the clean ECG, the noisy
ECG and the reference noise of every adaptive filter.
"""
import numpy as np
import wfdb

from src.config import (ECG_CHANNEL, ECG_START, FS, MITDB_DIR, N_SAMPLES, NOISE_CHANNEL,
                        NOISE_PATHS, NSTDB_DIR, PLI_FREQ, PLI_PHASE_SHIFT, PLI_POWER_LIKE,
                        TEST_NOISE_START)

ALL_NOISES = ("bw", "em", "ma", "pli")


def load_ecg(record):
    """10 % of an MIT-BIH record, zero mean and peak |x| = 1."""
    x = wfdb.rdrecord(str(MITDB_DIR / str(record)), sampfrom=ECG_START,
                      sampto=ECG_START + N_SAMPLES, channels=[ECG_CHANNEL]).p_signal[:, 0]
    x = x - x.mean()
    return x / np.abs(x).max()


def load_noise(name, start=TEST_NOISE_START):
    """10 % of an NSTDB noise record ('bw', 'em' or 'ma'), in mV with its mean removed."""
    x = wfdb.rdrecord(str(NSTDB_DIR / name), sampfrom=start, sampto=start + N_SAMPLES,
                      channels=[NOISE_CHANNEL]).p_signal[:, 0]
    return x - x.mean()


def noise_path(reference, name):
    """The noise that reaches the ECG: the reference shifted (delayed) and FIR filtered."""
    path = NOISE_PATHS[name]
    h = np.concatenate([np.zeros(path["delay"]), path["fir"]])
    return np.convolve(reference, h)[: len(reference)]


def pli(power, phase=0.0, n=N_SAMPLES):
    """60 Hz sinusoid with the given power."""
    t = np.arange(n) / FS
    return np.sqrt(2 * power) * np.sin(2 * np.pi * PLI_FREQ * t + phase)


def noise_signals(noises, noise_start=TEST_NOISE_START):
    """
    References and added noises, before the SNR gain: ({name: reference}, {name: added}).

    - BW, EM, MA: the reference is the NSTDB record (mV, natural amplitude); the noise
      added to the ECG is the shifted and filtered reference (noise_path).
    - PLI: the reference is a 60 Hz sinusoid with the power of the BW record; the noise
      added to the ECG is the same sinusoid, phase shifted.
    """
    refs, added = {}, {}
    for name in ("bw", "em", "ma"):
        if name in noises:
            refs[name] = load_noise(name, noise_start)
            added[name] = noise_path(refs[name], name)
    if "pli" in noises:
        power = np.mean(load_noise(PLI_POWER_LIKE, noise_start) ** 2)
        refs["pli"] = pli(power)
        added["pli"] = pli(power, PLI_PHASE_SHIFT)
    return refs, added


def make_case(record, noises, snr, noise_start=TEST_NOISE_START):
    """
    One noisy ECG: the added noises are summed and scaled by ONE gain so that SNRin
    (Eq. 4) equals `snr`, which keeps the natural power ratio between the noises. The
    references are not scaled: like a real reference electrode, their level does not
    depend on SNRin.

    Returns {"clean", "noisy", "refs": {noise: reference}, "record", "snr", "noises"}.
    """
    clean = load_ecg(record)
    refs, added = noise_signals(noises, noise_start)
    total = np.sum(list(added.values()), axis=0)
    gain = np.sqrt(np.sum(clean**2) / (np.sum(total**2) * 10 ** (snr / 10)))
    return {"clean": clean, "noisy": clean + gain * total, "refs": refs,
            "record": record, "snr": snr, "noises": tuple(noises)}


def noise_shares(noises=ALL_NOISES, noise_start=TEST_NOISE_START):
    """{noise: share of the total added noise power}."""
    _, added = noise_signals(noises, noise_start)
    powers = {name: np.mean(x**2) for name, x in added.items()}
    total = sum(powers.values())
    return {name: p / total for name, p in powers.items()}
