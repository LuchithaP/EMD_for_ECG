"""
Plot helpers. Every comparison uses the same convention: "<name> ours" (solid line or
filled bar) next to "<name> paper" (dashed line or hatched bar) in the same color.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.config import EXAMPLE_SAMPLES, FIGURES_DIR, FS

COLORS = {
    "EMD+LMS": "#2a9d3c", "EMD+RLS": "#d62728", "EMD+NLMS": "#1f9fe0",
    "PEAF": "#1f2f6b", "SEAF": "#a89a4f", "PDAF": "#d62728", "SDAF": "#2bb39a",
    "Article [28]": "#7b3fa0", "Article [21]": "#e8590c", "Article [22]": "#868e96",
}


def save(fig, name):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / name, dpi=130)
    plt.close(fig)
    print(f"  wrote results/figures/{name}")


def amplitude_spectrum(x):
    """One-sided amplitude spectrum 2|X(f)|/N (a sinusoid of amplitude A shows as A)."""
    return np.fft.rfftfreq(len(x), 1 / FS), 2 * np.abs(np.fft.rfft(x)) / len(x)


def plot_example(clean, noisy, denoised, method, title, name):
    """Figs. 6, 9: (a) first EXAMPLE_SAMPLES samples, (b) spectra, of clean / noisy / denoised."""
    signals = {"original signal": clean, "signal + noise": noisy,
               f"denoised signal ({method} ours)": denoised}
    fig, axes = plt.subplots(3, 2, figsize=(15, 7), constrained_layout=True)
    for row, (label, x) in enumerate(signals.items()):
        axes[row, 0].plot(x[:EXAMPLE_SAMPLES], lw=0.6)
        axes[row, 0].set_title(label)
        f, a = amplitude_spectrum(x)
        axes[row, 1].plot(f, a, lw=0.6)
        axes[row, 1].set_xlim(0, FS / 2)
        axes[row, 1].set_title(label)
    axes[2, 0].set_xlabel("sample")
    axes[2, 1].set_xlabel("f (Hz)")
    axes[0, 0].text(0.5, 1.25, "(a) time domain", transform=axes[0, 0].transAxes, ha="center")
    axes[0, 1].text(0.5, 1.25, "(b) frequency domain", transform=axes[0, 1].transAxes, ha="center")
    fig.suptitle(title)
    save(fig, name)


def lines_ours_vs_paper(ax, x, ours, paper):
    """ours / paper: {name: values at x}. Ours solid with circles, paper dashed with squares."""
    for name, values in ours.items():
        ax.plot(x, values, "o-", color=COLORS[name], lw=2, label=f"{name} ours")
    for name, values in paper.items():
        ax.plot(x, values, "s--", color=COLORS[name], lw=1.3, alpha=0.8, ms=4,
                label=f"{name} paper")
    ax.grid(alpha=0.3)


def bars_ours_vs_paper(ax, groups, ours, paper):
    """Grouped bars: per group, for each name a filled bar (ours) and a hatched bar (paper)."""
    names = list(ours)
    width = 0.8 / (2 * len(names))
    x = np.arange(len(groups))
    for i, name in enumerate(names):
        offset = (2 * i - len(names) + 0.5) * width
        ax.bar(x + offset, ours[name], width, color=COLORS[name], label=f"{name} ours")
        ax.bar(x + offset + width, paper[name], width, color="white", edgecolor=COLORS[name],
               hatch="///", label=f"{name} paper")
    ax.set_xticks(x, groups)
    ax.grid(axis="y", alpha=0.3)
