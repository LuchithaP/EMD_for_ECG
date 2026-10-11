# Reproduction of Dai & Bai, "Denoising ECG by Adaptive Filter with EMD"

Regenerate everything with `python experiments/reproduce_paper.py` (about 15 min on 8 cores). Then open
`notebooks/01`–`04`. Each notebook checks the paper's claims automatically.

## Test setup (same as the paper)

| Item | Setting |
|---|---|
| Clean ECG | MIT-BIH Arrhythmia DB, channel 0, 5000-sample segments, high-passed at 0.5 Hz (the records have their own baseline) |
| Noise | NSTDB `bw`, `em`, `ma` + 60 Hz PLI, equal power per noise, total scaled to SNRin |
| Reference noise | Shifted + filtered copies of the added noise ("correlated but not equal", Sec. IV) |
| Records / SNRin | Fig. 8: 119, 202, 213, 217, 234 · Fig. 10: 13 records at 10 dB · Fig. 11: −5, −2, 0, 3, 6, 10 dB |
| Filter | LMS, 32 taps, for every method (as in the paper). Step sizes tuned per noise on **held-out** records 101, 108, 109, 112, 114 |
| Averaging | 3 random segments/noise offsets per point |

## Claim-by-claim result

| # | Paper claim | Reproduced? | Our numbers |
|---|---|---|---|
| 1 | PLI: filter IMF1 only (Fig. 2) | **Yes** | IMF1 17.9 dB vs whole signal 17.2 dB. IMF1 also tolerates a 3× larger step size |
| 2 | BW: filter IMF5–8 (Fig. 2) | **No** | IMF5–8 0.1 dB. BW is below IMF8 (≈0.7 Hz) and sits in the residue. IMF5–8 + r gives 9.0 dB, the same as no EMD (9.05 dB) |
| 3 | EM: filter IMF3–8 (Fig. 2) | **No** | IMF3–8 2.3 dB vs no EMD 6.8 dB; IMF3–8 + r 6.75 dB |
| 4 | MA: no EMD (Fig. 2) | **Yes** | no EMD 7.1 dB is the best input |
| 5 | LMS beats NLMS and RLS (Fig. 7) | **No** | RLS is best at −5, 0 and 5 dB; LMS ≈ RLS at 10 dB |
| 6 | EMD+LMS beats direct LMS for BW+PLI (Fig. 8) | **No** | as written −3.5 dB vs direct; with residue −0.2 dB (2 of 5 records better) |
| 7 | PEAF best on every record at 10 dB (Fig. 10) | **No** | PDAF best on 13/13 records. Mean SNRimp: PDAF 6.7, SDAF 3.0, SEAF 2.7, PEAF 2.7 dB |
| 8 | PEAF best at every SNRin (Fig. 11) | **No** | PDAF best at 4 of 6 levels; SDAF/SEAF+r best at −5/−2 dB |
| 9 | SNRimp falls as SNRin rises (Fig. 11) | **Yes** | true for PEAF, SEAF, SDAF; PDAF is almost flat |
| 10 | SNRimp magnitude | Partly | 8–9 dB at −5 dB matches Fig. 11; at 10 dB we get 2.7–6.7 dB (paper: ≈4 dB in Fig. 11 but ≈10 dB in Fig. 10, which is inconsistent within the paper) |

## Why the EMD advantage does not appear

EMD helps an adaptive noise canceller in one way: the filter's input then contains less ECG, so the
ECG perturbs the weights less. That only pays off if the selected IMFs hold most of the noise
**and** little of the ECG:

* **PLI (60 Hz)** sits almost entirely in IMF1, where the ECG is weak, so EMD helps (claim 1).
* **BW** lies below IMF8, so most of it is in the residue, which Eqs. (1)–(3) add back unfiltered.
  Putting the residue in the BW branch fixes that, but IMF5–8 also contain much of the ECG (1–10 Hz),
  so the result only matches direct filtering.
* **EM and MA** are broadband. Any IMF subset leaves part of the noise unfiltered.
* With 4 cascaded or parallel filters, PEAF and SEAF accumulate each filter's misadjustment and
  convergence lag. PDAF has a single filter.

## Things tested that do *not* explain the gap

| Hypothesis | Test | Outcome |
|---|---|---|
| The paper used MATLAB default (large) step sizes | LMS μ = 0.01 … 0.3 on raw amplitudes, records 100/105/116/123 | All methods degrade together. PDAF stays ≥ PEAF/SEAF; μ ≥ 0.1 diverges at 0 dB |
| The residue should be filtered | "residue in BW/EM branch" variant everywhere | Brings EMD to parity with direct filtering, not above it |
| Step sizes favour one family | Separate tuning for EMD inputs and whole-signal inputs, on held-out records | Already applied in all results |

## Details the paper does not give (needed to match it exactly)

1. EMD implementation and stopping criteria. MATLAB `emd` and PyEMD split IMFs differently, so "IMF5–8" may hold different frequencies.
2. How the reference noises were shifted and filtered (delays, filters, any added sensor noise).
3. Relative amplitudes of BW/EM/MA/PLI before SNR scaling.
4. Segment length, step sizes and RLS/NLMS settings ("default parameters in MATLAB").
5. Whether SNR is measured after removing the convergence transient.

Matching the paper's numbers would need these from the authors. Choosing them after the fact to force
the paper's ranking would not be a valid reproduction.
