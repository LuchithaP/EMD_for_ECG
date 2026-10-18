# ECG denoising with EMD with adaptive filters

Reproduction of B. Dai and W. Bai, *Denoising ECG by Adaptive Filter with Empirical Mode
Decomposition* (`paper.pdf`).

## Run

```bash
pip install -r requirements.txt
python scripts/run_all.py
```

Takes about 20 min on 8 cores. Or run one step at a time (step 2 must run before 3 and 4):

| Script | Paper | Output |
|---|---|---|
| `scripts/01_imf_selection.py` | Sec. III-A: best IMFs for each noise | `results/imf_selection.csv`, `figures/imf_selection_*.png`, `figures/emd_imfs_*.png` |
| `scripts/02_tune_filters.py` | filter settings (not in the paper) | `results/tuned_filter_params.json`, `filter_tuning_scores.csv`, `figures/filter_tuning_*.png` |
| `scripts/03_bw_pli.py` | Sec. IV-A, Figs. 6, 7, 8 | `results/bw_pli.csv`, `figures/fig6_*`, `fig7a_*`, `fig7b_*`, `fig8_*` |
| `scripts/04_four_noises.py` | Sec. IV-B, Figs. 9, 10, 11 | `results/four_noises.csv`, `figures/fig9_*`, `fig10_*`, `fig11_*` |
| `scripts/05_compare_with_paper.py` | all claims | `results/comparison_with_paper.md` |

In every comparison plot, "X ours" is a solid line or filled bar, and "X paper" is a dashed
line or hatched bar in the same color. The paper's numbers (`src/paper_values.py`) were
measured from the PDF figures at 450 dpi (about ±0.2 dB).

Notebooks (they read `results/`, so run the scripts first):

| Notebook | Contents |
|---|---|
| `notebooks/01_signals_emd_imf_selection.ipynb` | noise mix, ECG scaling, EMD of a noisy ECG, Sec. III-A IMF choice |
| `notebooks/02_filter_tuning_bw_pli.ipynb` | tuned filter settings; BW + PLI: Figs. 6, 7, 8 with tables |
| `notebooks/03_four_noises_and_claims.ipynb` | four noises: Figs. 9, 10, 11 with tables; the paper's claims checked |

## Code

| File | Contents |
|---|---|
| `src/config.py` | every setting; `[PAPER]` = from the paper, `[OURS]` = our choice |
| `src/data.py` | MIT-BIH ECG + NSTDB noise + 60 Hz PLI → noisy ECG at a given SNRin |
| `src/emd.py` | EMD with MATLAB `emd()` defaults; results cached in `cache/` |
| `src/filters.py` | LMS, NLMS, RLS noise cancellers (Fig. 1), numba |
| `src/methods.py` | Fig. 2, Eq. (1), PEAF (Eq. 2), SEAF (Eq. 3), SDAF (Fig. 5), PDAF |
| `src/metrics.py` | SNR, RMSE, SNRimp (Eqs. 4–6) |
| `src/tuning.py` | grid search of the filter settings |
| `src/paper_values.py` | numbers read off the paper's figures |
| `src/plots.py`, `src/utils.py` | plot helpers; case loading, parallel runs, saving |

## Taken from the paper

- MIT-BIH Arrhythmia ECG, MIT-BIH Noise Stress Test BW / EM / MA, PLI = 60 Hz sinusoid, fs = 360 Hz.
- The reference for each adaptive filter is the noise itself. The noise added to the ECG is
  "shifted and passed through different filters".
- IMFs per noise (Sec. III-A): **PLI → IMF1, BW → IMF5~8, EM → IMF3~8, MA → whole signal**.
- Structures: Eq. (1) for BW + PLI; PEAF (Eq. 2), SEAF (Eq. 3), SDAF (Fig. 5, Thakor & Zhu
  + an MA stage) and PDAF (all noises as one, one filter) for four noises. MA is filtered last.
- LMS for every method except Fig. 7, which compares LMS / NLMS / RLS.
- Records: Fig. 8 uses 119, 202, 213, 217, 234; Fig. 10 uses 100, 103, 104, 105, 106, 111, 113,
  115, 116, 121, 122, 123, 231. SNRin: Fig. 7 uses −5, 0, 5, 7, 10; Fig. 8 uses 10;
  Fig. 11 uses −5, −2, 0, 3, 6, 10 dB.
- Metrics: Eqs. (4)–(6).

## What the paper does not give (our choices)

| Item | Our choice | Why |
|---|---|---|
| Data length | 10 % of each record (65 000 samples ≈ 3 min), ECG from the start, noise from the start (tuning: from sample 325 000) | records are long |
| ECG scaling | zero mean, peak \|x\| = 1 | In Figs. 6 and 9 the clean ECG sits at baseline ≈ 0 with R ≈ 1 and has no DC in its spectrum. Fig. 7's RMSE and SNRout together imply a clean ECG RMS of ≈ 0.16 (ours: 0.18; raw mV would be ≈ 0.6) |
| Noise scaling | NSTDB records in mV, mean removed, **natural ratio kept** (EM 46.6 %, BW 24.7 %, MA 3.9 % of the noise power), PLI with the power of BW (24.7 %). The sum is scaled by one gain so Eq. (4) gives exactly SNRin | keeps the stress-test noises as recorded |
| References | the noise records themselves, **not** scaled with SNRin (like a real reference electrode) | a step size then means the same at every SNRin |
| "Shift + filter" of the added noise | BW: 5-sample delay, FIR [0.5 0.3 0.2]; EM: 3, [0.6 0.3 0.1]; MA: 2, [0.7 0.2 0.1]; PLI: 45° phase shift | correlated with but not equal to the reference |
| EMD | MATLAB `emd()` defaults: cubic spline envelopes, sifting stops at relative tolerance 0.2 or 100 sifts; 8 IMFs + residue | the paper used MATLAB |
| Filter settings | **tuned**: every filter of every method gets its own (μ, taps) for LMS / NLMS or (λ, taps) for RLS. Coordinate descent over a grid, maximizing mean SNRimp on **held-out** records 101, 112, 117, 201, 220 at −5, 0, 5, 10 dB with another noise segment. One setting per filter for all SNRin. RLS P(0) = 1000·I | not given |
| SDAF parallel stage | PLI and BW LMS filters on the noisy ECG with one shared error | Fig. 5 shows them in parallel |
| Fig. 7 / Fig. 11 records | mean over the Fig. 8 / Fig. 10 records | not stated |
| Fig. 10 SNRin | both −5 dB and 10 dB | the text says 10 dB, but the values (~9–11 dB) match Fig. 11 at −5 dB (Fig. 11 at 10 dB: ~3.5–4.3 dB) |
| Examples (Figs. 6, 9) | record 234 (Fig. 6) and 100 (Fig. 9), SNRin 5 dB | not stated |

Tuned settings (`results/tuned_filter_params.json`):

| Method | PLI | BW | EM | MA |
|---|---|---|---|---|
| EMD+LMS | μ 0.01, 16 taps | μ 3e-4, 8 | | |
| EMD+NLMS | μ 0.03, 16 | μ 1e-3, 64 | | |
| EMD+RLS | λ 1, 4 | λ 1, 8 | | |
| PEAF | μ 0.03, 4 | μ 3e-5, 32 | μ 1e-4, 8 | μ 3e-3, 4 |
| SEAF | μ 0.03, 4 | μ 1e-4, 8 | μ 1e-4, 8 | μ 3e-3, 4 |
| SDAF | μ 3e-3, 16 | μ 1e-4, 8 | μ 1e-4, 8 | μ 3e-3, 4 |
| PDAF | one filter, all references summed: μ 3e-4, 8 taps | | | |

## Results

Full tables: `results/comparison_with_paper.md`.

**Sec. III-A, IMF choice** (each noise alone, mean SNRimp on held-out cases). The paper's
choice is best for PLI (IMF1, 29.0 dB) and MA (no EMD, 13.5 dB). For BW (IMF5~8: 13.9 dB
vs 14.2 dB with no EMD) and EM (IMF3~8: 13.4 dB vs 13.7 dB for IMF1~8) it is within 0.3 dB
of the best, about the size of the differences between neighbouring grid settings. Every
BW range that ends at IMF8 gives ~14 dB. We therefore keep the paper's IMFs.

**BW + PLI (Figs. 7, 8)**, mean SNR output (dB), ours (paper):

| SNRin | −5 | 0 | 5 | 7 | 10 |
|---|---|---|---|---|---|
| EMD+LMS | 13.4 (10.0) | 17.3 (11.0) | 20.1 (12.4) | 20.6 (17.3) | 21.4 (22.2) |
| EMD+RLS | 20.2 (8.2) | 21.0 (9.1) | 23.8 (12.2) | 23.6 (16.6) | 23.6 (21.9) |
| EMD+NLMS | 9.8 (5.1) | 11.7 (7.2) | 12.7 (13.1) | 12.4 (18.6) | 13.3 (24.4) |

- Our EMD + LMS beats the paper's up to 7 dB SNRin and is 0.8 dB below it at 10 dB. Our
  SNRout levels off at high SNRin; the paper's keeps rising.
- RLS (λ = 1) is best for us at every SNRin. The paper finds LMS best at low SNRin and NLMS
  best at high SNRin.
- Fig. 8 (SNRin 10 dB): 24.9 / 19.5 / 23.7 / 20.3 / 18.9 dB vs the paper's
  24.7 / 22.9 / 25.0 / 29.2 / 23.9. Ours beats the best of articles [21, 22, 28] on 2/5 records.

**BW + PLI + EM + MA (Figs. 10, 11)**, mean SNRimp (dB) over 13 records, ours (paper):

| SNRin | −5 | −2 | 0 | 3 | 6 | 10 |
|---|---|---|---|---|---|---|
| PEAF | 12.5 (10.4) | 12.0 (9.6) | 11.5 (9.4) | 10.5 (7.2) | 9.1 (5.6) | 6.5 (4.3) |
| SEAF | 13.3 (10.4) | 12.8 (9.1) | 12.2 (8.8) | 11.1 (6.8) | 9.7 (5.3) | 7.1 (4.1) |
| PDAF | 14.9 (10.3) | 13.9 (9.2) | 13.0 (8.7) | 11.3 (6.6) | 9.2 (4.8) | 5.9 (3.5) |
| SDAF | 13.4 (10.3) | 12.8 (8.8) | 12.3 (8.2) | 11.3 (6.2) | 9.8 (4.5) | 7.2 (3.4) |

- Like the paper: SNRimp falls as SNRin rises, for every method. Our values are 2–5 dB higher.
- Unlike the paper: **PEAF is not the best method**. It is the lowest of the four at 5 of 6
  SNRin and is not the best on any record in Fig. 10 (at −5 or 10 dB). PDAF (one filter, no
  EMD) is best from −5 to 3 dB, SDAF at 6 and 10 dB. SEAF beats PEAF at every SNRin.

**Claims of the paper**: reproduced: PLI → IMF1, MA → no EMD, SNRimp falls with SNRin.
Partly: BW / EM IMF choice, Fig. 8 numbers, beating articles [21, 22, 28], PEAF level.
Not reproduced: LMS best in Fig. 7, PEAF best (Figs. 10, 11), EMD methods beat direct ones.

## Notes on the paper

- Fig. 10: the text says SNRin = 10 dB, but the values match Fig. 11 at −5 dB.
- Fig. 7: the text says LMS is best, but in its own figure NLMS has the highest SNR output at
  5, 7 and 10 dB.
- Fig. 7 vs Fig. 8: at SNRin 10 dB, LMS + EMD is 22.2 dB in Fig. 7 but 22.9–29.2 dB (mean 25.1)
  in Fig. 8; the records of Fig. 7 are not named.
- Sec. III-A calls EM "a high frequency noise", but 73 % of the NSTDB `em` record's power is
  below 0.5 Hz (BW: 98 %, MA: 72 %).
