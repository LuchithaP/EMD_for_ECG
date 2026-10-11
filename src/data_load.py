from pathlib import Path

import numpy as np
import wfdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MITDB_DIR = PROJECT_ROOT / "data" / "physionet.org" / "files" / "mitdb" / "1.0.0"
NSTDB_DIR = PROJECT_ROOT / "data" / "physionet.org" / "files" / "nstdb" / "1.0.0"

NOISE_TYPES = ("bw", "ma", "em")
PLI_FREQ = 60.0

# Sec. IV: "the noises all have been shifted and passed through different filters to get
# noises that are not equal but correlated to the adaptive filters' reference noises".
# The paper gives no delays or filters, so these are fixed choices: (delay in samples,
# FIR low-pass taps with unit DC gain), a different filter for each noise.
NOISE_PATHS = {
    "bw": (3, [0.6, 0.4]),
    "em": (5, [0.4, 0.3, 0.2, 0.1]),
    "ma": (4, [0.5, 0.3, 0.2]),
}


def record_path(record) -> str:
    """Return the WFDB path of an MIT-BIH record given its number (e.g. 100) or a path."""
    record = str(record)
    if Path(record).parent != Path("."):
        return record
    return str(MITDB_DIR / record)


def load_ecg_data(record_path: str):
    """
    Load ECG data from a WFDB record.

    Parameters:
    - record_path: str, path to the WFDB record (without file extension)

    Returns:
    - ecg_signal: numpy array, the ECG signal
    - fs: int, sampling frequency of the ECG signal
    """
    record = wfdb.rdrecord(record_path)

    # Extract the ECG signal and sampling frequency
    ecg_signal = record.p_signal[:, 0]  # Assuming the first channel is the ECG signal
    fs = record.fs

    return ecg_signal, fs


def load_noise_data(noise_type: str):
    """
    Load noise data based on the specified noise type.

    Parameters:
    - noise_type: str, type of noise ('bw', 'ma', or 'em')

    Returns:
    - noise_signal: numpy array, the noise signal
    - fs: int, sampling frequency of the noise signal
    """
    if noise_type not in NOISE_TYPES:
        raise ValueError("Invalid noise type. Choose from 'bw', 'ma', or 'em'.")

    record = wfdb.rdrecord(str(NSTDB_DIR / noise_type))

    # Extract the noise signal and sampling frequency
    noise_signal = record.p_signal[
        :, 0
    ]  # Assuming the first channel is the noise signal
    fs = record.fs

    return noise_signal, fs


def add_PLI(frequency, ampl, fs, N, phase=0.0):
    """
    Generate a Power Line Interference (PLI) signal.

    Parameters:
    - frequency: float, frequency of the PLI (e.g., 50 or 60 Hz)
    - ampl: float, amplitude of the PLI
    - fs: int, sampling frequency
    - N: int, number of samples
    - phase: float, phase in radians

    Returns:
    - pli_signal: numpy array, the generated PLI signal
    """
    t = np.arange(N) / fs
    pli_signal = ampl * np.sin(2 * np.pi * frequency * t + phase)
    return pli_signal


def scale_SNR(clean_ecg, noise_signal, desired_snr_db):
    """
    Scale the noise signal to achieve the desired SNR with respect to the clean ECG signal.

    Parameters:
    - clean_ecg: numpy array, the clean ECG signal
    - noise_signal: numpy array, the noise signal
    - desired_snr_db: float, desired SNR in dB

    Returns:
    - scaled_noise: numpy array, the scaled noise signal
    """
    return noise_signal * snr_scale_factor(clean_ecg, noise_signal, desired_snr_db)


def snr_scale_factor(clean_ecg, noise_signal, desired_snr_db):
    """Gain that brings noise_signal to desired_snr_db relative to clean_ecg (Eq. 4)."""
    return np.sqrt(np.sum(clean_ecg**2) / (np.sum(noise_signal**2) * 10 ** (desired_snr_db / 10)))


def shift_and_filter(reference, delay, taps):
    """Noise reaching the ECG: the reference delayed by `delay` samples and FIR filtered."""
    h = np.concatenate([np.zeros(delay), taps])
    return np.convolve(reference, h)[: len(reference)]


def make_noisy_ecg(record, noises=("bw", "em", "ma"), pli=True, snr_db=10.0):
    """
    Build one test case as described in Sec. IV of the paper.

    - Clean ECG: the whole MIT-BIH Arrhythmia record (channel 0), not preprocessed.
    - BW, EM, MA: the whole MIT-BIH Noise Stress Test records at their recorded
      amplitudes. The reference noise is the record itself; the noise added to the ECG
      is the shifted and filtered reference (NOISE_PATHS).
    - PLI: a 60 Hz sinusoid with the same power as the BW noise. The paper shifts and
      filters only BW, EM and MA, so the PLI reference equals the added PLI.
    - The total noise is scaled so that the input SNR (Eq. 4) equals snr_db. References
      are scaled by the same gain.

    Returns a dict with:
    - clean, noisy, noise: clean ECG, clean + noise, total added noise
    - components: {name: noise component added to the ECG}
    - references: {name: reference noise given to that noise's adaptive filter}
    - fs: sampling frequency
    """
    clean, fs = load_ecg_data(record_path(record))
    n = len(clean)

    components, references = {}, {}
    for name in noises:
        ref, fs_noise = load_noise_data(name)
        if fs_noise != fs:
            raise ValueError("Sampling frequencies of clean ECG and noise do not match.")
        ref = ref[:n]
        references[name] = ref
        components[name] = shift_and_filter(ref, *NOISE_PATHS[name])
    if pli:
        bw = shift_and_filter(load_noise_data("bw")[0][:n], *NOISE_PATHS["bw"])
        amplitude = np.sqrt(2 * np.mean(bw**2))
        references["pli"] = components["pli"] = add_PLI(PLI_FREQ, amplitude, fs, n)

    total = sum(components.values())
    gain = snr_scale_factor(clean, total, snr_db)
    components = {k: v * gain for k, v in components.items()}
    references = {k: v * gain for k, v in references.items()}
    noise = total * gain

    return {
        "clean": clean,
        "noisy": clean + noise,
        "noise": noise,
        "components": components,
        "references": references,
        "fs": fs,
    }


def load_noisy_ecg_data(
    record_path: str, snr_db: float = 10, multiple_noises: list = None, PLI=False
):
    """
    Load clean ECG data and noise data, ensuring they have the same length.

    Used by the earlier notebooks. The returned noise is the exact noise that was
    added. Use make_noisy_ecg for the paper's setup.

    Parameters:
    - record_path: str, path to the WFDB record for clean ECG (without file extension)
    - snr_db: float, desired SNR in dB
    - multiple_noises: list of str, types of noise to add ('bw', 'ma', or 'em')
    - PLI: bool, whether to add 60 Hz power line interference

    Returns:
    - clean_ecg: numpy array, the clean ECG signal
    - noise_signal: numpy array, the noise signal
    - noisy_ecg: numpy array, clean_ecg + noise_signal
    - fs: int, sampling frequency of the signals
    - pli: numpy array or None, the unscaled PLI signal
    """
    clean_ecg, fs_clean = load_ecg_data(record_path)

    noise_signal = np.zeros_like(clean_ecg)
    for noise_type in multiple_noises or []:
        noise, fs_noise = load_noise_data(noise_type)
        if fs_clean != fs_noise:
            raise ValueError("Sampling frequencies of clean ECG and noise do not match.")
        N = min(len(noise_signal), len(noise))
        noise_signal = noise_signal[:N] + noise[:N]

    pli = None
    if PLI:
        # Amplitude of PLI is set to 10% of the max amplitude of the clean ECG
        pli = add_PLI(PLI_FREQ, max(clean_ecg) * 0.1, fs_clean, len(noise_signal))
        noise_signal = noise_signal + pli

    if not np.any(noise_signal):
        raise ValueError("Select at least one noise type or PLI=True.")

    N = min(len(clean_ecg), len(noise_signal))
    clean_ecg = clean_ecg[:N]
    noise_signal = scale_SNR(clean_ecg, noise_signal[:N], snr_db)
    noisy_ecg = clean_ecg + noise_signal

    return clean_ecg, noise_signal, noisy_ecg, fs_clean, pli
