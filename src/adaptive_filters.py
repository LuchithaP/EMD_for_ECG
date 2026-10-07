import numpy as np
import matplotlib.pyplot as plt
import padasip as pa


def LMS_filter(noisy_signal, reference_signal, mu, filter_order, N):
    """
    Apply LMS adaptive filtering to remove noise from a signal.

    Parameters:
    noisy_signal (numpy.ndarray): The noisy input signal (desired signal d).
    reference_signal (numpy.ndparray): The reference noise signal.
    mu (float): The step size for the LMS algorithm.
    filter_order (int): The order of the adaptive filter (number of taps).
    N (int): The number of samples in the signal.

    Returns:
    numpy.ndarray: The filtered output signal (error signal e).
    """
    # 1. Prepare the reference signal as a delay-embedded matrix (input matrix X)
    X = pa.input_from_history(reference_signal, filter_order)

    # 2. Align the desired signal (noisy_signal) to match the length of X
    # padasip input_from_history shortens the array length by (filter_order - 1)
    d = noisy_signal[filter_order - 1 :]

    # 3. Initialize the adaptive filter
    lms = pa.filters.FilterLMS(n=filter_order, mu=mu)

    # 4. Apply the LMS filter
    y, e, w = lms.run(d, X)

    denoised_signal = e  # The error signal represents the denoised output

    return denoised_signal


def NLMS_filter(noisy_signal, reference_signal, mu, filter_order, N):
    """
    Apply NLMS adaptive filtering to remove noise from a signal.

    Parameters:
    noisy_signal (numpy.ndarray): The noisy input signal.
    reference_signal (numpy.ndarray): The reference signal (noise).
    mu (float): The step size for the NLMS algorithm.
    filter_order (int): The order of the adaptive filter.
    N (int): The number of samples in the signal.

    Returns:
    numpy.ndarray: The filtered output signal.
    """

    # Initialize the adaptive filter
    nlms = pa.filters.FilterNLMS(n=filter_order, mu=mu, eps=1e-6)

    # Prepare the input signals
    X = pa.input_from_history(reference_signal, filter_order)
    d = noisy_signal[filter_order - 1 :]  # Desired signal

    # Apply the NLMS filter
    y, e, w = nlms.run(d, X)

    denoised_signal = e  # The error signal is the denoised output

    return denoised_signal


def RLS_filter(noisy_signal, reference_signal, mu=0.99, filter_order=32, eps=0.01, N=0):
    """
    RLS adaptive noise cancellation.

    Parameters:
    noisy_signal : (np.ndarray)Noisy ECG signal. This is the desired signal d(n).
    reference_signal : (np.ndarray)Reference noise signal correlated with the noise
        present in noisy_signal.
    mu : (float ) RLS forgetting factor. Usually close to 1.
    filter_order : (int)Number of adaptive filter taps.
    eps : (float)Initialisation parameter for the RLS covariance matrix.

    Returns:
    denoised_signal : (np.ndarray)
        Error signal e(n) = d(n) - y(n).

    """

    noisy_signal = noisy_signal[:N]
    reference_signal = reference_signal[:N]

    # Construct tapped-delay reference input

    X = pa.input_from_history(reference_signal, filter_order)
    d = noisy_signal[filter_order - 1 :]

    # Create RLS filter

    rls = pa.filters.FilterRLS(n=filter_order, mu=mu, eps=eps, w="zeros")

    # Run adaptive filter

    estimated_noise, error, weights = rls.run(d, X)

    # error = desired signal - estimated noise
    denoised_signal = error

    return denoised_signal


def evaluate_filter_performance(clean_signal, denoised_signal, noise_signal):
    """
    Evaluate denoising performance over the samples produced by the filter.

    Parameters:
    clean_signal (numpy.ndarray): The original clean signal.
    denoised_signal (numpy.ndarray): The denoised signal after filtering.
    noise_signal (numpy.ndarray): The noise signal.

    Returns:
    tuple: SNR, RMSE, and SNR improvement.
    """
    denoised_length = len(denoised_signal)
    if denoised_length == 0:
        raise ValueError("denoised_signal must contain at least one sample.")
    if len(clean_signal) < denoised_length or len(noise_signal) < denoised_length:
        raise ValueError(
            "clean_signal and noise_signal must be at least as long as denoised_signal."
        )

    # Adaptive filters omit their initial filter_order - 1 samples.
    clean_signal = clean_signal[-denoised_length:]
    noise_signal = noise_signal[-denoised_length:]

    signal_power = np.sum(clean_signal**2)
    error_power = np.sum((clean_signal - denoised_signal) ** 2)
    noise_power = np.sum(noise_signal**2)

    SNR = 10 * np.log10(signal_power / error_power)

    RMSE = np.sqrt(np.mean((clean_signal - denoised_signal) ** 2))

    # SNR improvement (SNR_OUT - SNR_IN)
    SNR_impr = 10 * np.log10(noise_power / error_power)
    return SNR, RMSE, SNR_impr
