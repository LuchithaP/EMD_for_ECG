import wfdb
import numpy as np


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
    if noise_type == "bw":
        record_path = r"C:\Users\Luchitha\Documents\Python\EMD_for_ECG\data\physionet.org\files\nstdb\1.0.0\bw"
    elif noise_type == "ma":
        record_path = r"C:\Users\Luchitha\Documents\Python\EMD_for_ECG\data\physionet.org\files\nstdb\1.0.0\ma"
    elif noise_type == "em":
        record_path = r"C:\Users\Luchitha\Documents\Python\EMD_for_ECG\data\physionet.org\files\nstdb\1.0.0\em"
    else:
        raise ValueError("Invalid noise type. Choose from 'bw', 'ma', or 'em'.")

    record = wfdb.rdrecord(record_path)

    # Extract the noise signal and sampling frequency
    noise_signal = record.p_signal[
        :, 0
    ]  # Assuming the first channel is the noise signal
    fs = record.fs

    return noise_signal, fs


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
    # Calculate the power of the clean ECG signal
    power_clean = np.mean(clean_ecg**2)

    # Calculate the desired power of the noise signal based on the desired SNR
    desired_power_noise = power_clean / (10 ** (desired_snr_db / 10))

    # Calculate the current power of the noise signal
    power_noise = np.mean(noise_signal**2)

    # Calculate the scaling factor for the noise signal
    scaling_factor = np.sqrt(desired_power_noise / power_noise)

    # Scale the noise signal
    scaled_noise = noise_signal * scaling_factor

    return scaled_noise


def load_noisy_ecg_data(
    record_path: str, snr_db: float = 10, multiple_noises: list = None
):
    """
    Load clean ECG data and noise data, ensuring they have the same length.

    Parameters:
    - record_path: str, path to the WFDB record for clean ECG (without file extension)
    - snr_db: float, desired SNR in dB
    - multiple_noises: list of str, types of noise to add ('bw', 'ma', or 'em')

    Returns:
    - clean_ecg: numpy array, the clean ECG signal
    - noise_signal: numpy array, the noise signal
    - fs: int, sampling frequency of the signals
    """
    clean_ecg, fs_clean = load_ecg_data(record_path)
    noise_signal = np.zeros_like(clean_ecg)  # Initialize noise signal with zeros
    if multiple_noises is not None:
        for noise_type in multiple_noises:
            noise, fs_noise = load_noise_data(noise_type)
            noise_signal = noise_signal + noise
    # noise_signal, fs_noise = load_noise_data(noise_type)
    scaled_noise_signal = scale_SNR(clean_ecg, noise_signal, snr_db)

    # Ensure both signals have the same sampling frequency
    if fs_clean != fs_noise:
        raise ValueError("Sampling frequencies of clean ECG and noise do not match.")

    # Truncate both signals to the same length
    N = min(len(clean_ecg), len(scaled_noise_signal))

    noisy_ecg = clean_ecg[:N] + scaled_noise_signal[:N]
    clean_ecg = clean_ecg[:N]
    noise_signal = scaled_noise_signal[:N]

    return clean_ecg, noise_signal, noisy_ecg, fs_clean
