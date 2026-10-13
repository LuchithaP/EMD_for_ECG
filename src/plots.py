"""Plots shared by the scripts."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.config import FS


def spectrum(x):
    """One-sided amplitude spectrum: frequencies (Hz) and |X(f)| / N."""
    return np.fft.rfftfreq(len(x), 1 / FS), np.abs(np.fft.rfft(x)) / len(x)


def plot_example(clean, noisy, denoised, title, path, n_show=5000):
    """Figs. 6 / 9: time domain (first n_show samples) and spectrum of the three signals."""
    signals = {"original signal": clean, "signal + noise": noisy, "EMD denoised signal": denoised}
    fig, axes = plt.subplots(3, 2, figsize=(14, 7), constrained_layout=True)
    for row, (name, x) in enumerate(signals.items()):
        axes[row, 0].plot(x[:n_show], lw=0.7)
        axes[row, 0].set_title(name)
        f, a = spectrum(x)
        keep = (f > 0.5) & (f <= 180)  # skip DC so the plot is not dominated by the offset
        axes[row, 1].plot(f[keep], a[keep], lw=0.7)
        axes[row, 1].set_title(name)
    axes[2, 0].set_xlabel("sample")
    axes[2, 1].set_xlabel("f (Hz)")
    fig.suptitle(title)
    fig.savefig(path, dpi=120)
    plt.close(fig)
