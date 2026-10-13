# ECG denoising with EMD + adaptive filters

Reproduction of Dai & Bai, *Denoising ECG by Adaptive Filter with Empirical Mode
Decomposition* (`paper.pdf`).

## Run

```bash
pip install -r requirements.txt
python scripts/run_all.py
```

or one step at a time (step 1 must run first; ~15 min in total on 4 cores):

| Script | What it does | Output |
|---|---|---|
| `scripts/01_tune_lms.py` | finds the optimum LMS step size and taps for every filter | `results/lms_params.json`, `lms_tuning*.csv`, `figures/lms_tuning_*.png` |
| `scripts/02_bw_pli.py` | BW + PLI, Eq. (1), LMS vs NLMS vs RLS (Figs. 6, 7, 8) | `results/bw_pli.csv`, `figures/fig6-8_*.png` |
| `scripts/03_four_methods.py` | BW + PLI + EM + MA, PEAF / SEAF / PDAF / SDAF (Figs. 9, 10, 11) | `results/four_methods.csv`, `figures/fig9-11_*.png` |
| `scripts/04_ecg_norm_check.py` | raw vs normalized ECG | `results/ecg_norm_check.csv`, `figures/ecg_norm_check.png` |

Every figure exists twice: `*_raw.png` (ECG as recorded) and `*_norm.png` (ECG normalized).

Notebooks (read `results/`, run the scripts first):

| Notebook | Contents |
|---|---|
| `notebooks/01_data_and_emd.ipynb` | one noisy ECG, its IMFs, and which IMFs each noise lands in (computed live) |
| `notebooks/02_lms_tuning.ipynb` | chosen LMS step size and taps per filter, tuning heatmaps |
| `notebooks/03_bw_pli.ipynb` | BW + PLI: tables and Figs. 6, 7, 8 |
| `notebooks/04_four_methods.ipynb` | BW + PLI + EM + MA: tables and Figs. 9, 10, 11 |
| `notebooks/05_ecg_normalization.ipynb` | raw vs normalized ECG, DC offset of each record |
| `notebooks/06_paper_claims.ipynb` | every claim of the paper with our numbers and a Yes / Partly / No verdict |

`python -m src.claims` prints the same claims table in the terminal.

## Code

| File | Contents |
|---|---|
| `src/config.py` | every setting: records, SNRs, IMFs per noise, LMS grid, data length |
| `src/data.py` | MIT-BIH ECG + NSTDB noise + 60 Hz PLI -> noisy ECG at a given SNR |
| `src/emd.py` | PyEMD decomposition into 8 IMFs + residue |
| `src/filters.py` | LMS, NLMS, RLS noise cancellers (Fig. 1) |
| `src/methods.py` | Fig. 2, Eq. (1), PEAF, SEAF, SDAF, PDAF |
| `src/metrics.py` | SNR, RMSE, SNRimp (Eqs. 4-6) |
| `src/claims.py` | the paper's claims, checked against `results/` |
| `src/plots.py`, `src/utils.py` | example plot; case lists, parallel run, saving |

## Setup

- First 10 % of each record (65 000 samples, 3.6 min at 360 Hz).
- Noise: NSTDB `bw`, `em`, `ma` (shifted and filtered before being added, as in Sec. IV) + 60 Hz
  PLI with the power of BW; total scaled to SNRin.
- IMFs per noise, as in the paper (Sec. III-A): **PLI -> IMF1, BW -> IMF5-8, EM -> IMF3-8,
  MA -> whole signal (no EMD)**.
- EMD: PyEMD with 10 sifting iterations per IMF (`EMD_SIFTINGS`). PyEMD's default stopping rule
  over-sifts these signals: its IMF8 is still at ~7 Hz, so all of BW (~0.3 Hz) lands in the
  residue and the paper's IMF5-8 BW filter cannot remove anything (SNRimp 0 dB). With 10 sifts
  the IMFs are about one octave apart (IMF1 ~70 Hz ... IMF8 ~0.2 Hz), as the paper assumes.
- **Residue filtering (`FILTER_RESIDUE = True`, a change from the paper).** Even with good IMFs,
  about 35 % of the BW noise and 12 % of the EM noise is slower than IMF8 and sits in the EMD
  residue, which the paper adds back unfiltered (Eqs. 1-3). With a least-squares "oracle"
  filter (the best any linear filter could do), the paper's IMF5-8 branch can remove at most
  ~9 dB of BW, against ~32 dB for a filter on the whole signal. So the BW branch filters
  IMF5-8 + residue and the EM branch IMF3-8 + residue (the residue's mean, i.e. the ECG's DC
  offset, is left out of the filter and added back). Set `FILTER_RESIDUE = False` for the
  paper's exact equations.

## LMS parameters (the main fix)

Problems in the old code:
1. The reference noise was scaled with the SNR, so a fixed step size acted ~30x larger at
   -5 dB than at 10 dB. **Fix:** each reference is scaled to unit power inside the filter.
2. One step size and tap count for all filters. **Fix:** every filter has its own setting.
3. The settings were picked on the same records they were tested on. **Fix:** tuning uses
   held-out records (101, 112, 117, 201, 220) and a different part of the noise records.

Chosen settings (mean SNRimp over the tuning cases at -5, 0, 5, 10 dB; `results/lms_params.json`):

| Filter | Input | raw ECG: mu, taps | normalized ECG: mu, taps |
|---|---|---|---|
| PLI | IMF1 | 0.01, 8 | 0.01, 4 |
| BW | IMF5-8 + residue | 3e-4, 4 | 1e-4, 4 |
| EM | IMF3-8 + residue | 1e-4, 8 | 3e-5, 16 |
| MA | whole signal | 3e-5, 8 | 1e-4, 8 |
| PLI / BW / EM (SDAF, no EMD) | whole signal | 0.01, 1 / 1e-5, 16 / 3e-5, 8 | 0.01, 1 / 3e-4, 2 / 3e-5, 16 |
| all noises (PDAF) | whole signal | 3e-4, 1 | 1e-4, 8 |

mu is for a unit-power reference. The best mu still drops with rising SNRin (the ECG itself
disturbs the LMS update), but one setting per filter loses at most 2.7 dB against the
per-SNR best (`results/lms_params_summary.csv`, `figures/lms_tuning_vs_snr_*.png`).

## Results

Mean SNRimp (dB) over the records. "paper eqs" = `FILTER_RESIDUE = False`, "+ residue" = `True`.

**BW + PLI, EMD + LMS (Eq. 1)**

| SNRin | -5 | 0 | 5 | 7 | 10 |
|---|---|---|---|---|---|
| raw ECG, paper eqs | 11.0 | 11.0 | 10.8 | 10.3 | 8.7 |
| raw ECG, + residue | 20.3 | 17.9 | 14.2 | 12.2 | 9.5 |
| raw ECG, LMS without EMD | 15.6 | 15.2 | 14.4 | 13.8 | 12.6 |
| norm ECG, + residue | 18.5 | 17.3 | 15.1 | 13.6 | 11.5 |
| norm ECG, LMS without EMD | 18.5 | 17.1 | 14.6 | 13.3 | 11.0 |

Fig. 8 (SNRout at 10 dB, raw ECG, records 119 / 202 / 213 / 217 / 234):
paper 24.6 / 22.6 / 25.0 / 29.2 / 23.9; ours EMD + RLS 30.2 / 20.0 / 24.7 / 24.7 / 19.7;
EMD + LMS 24.0 / 16.8 / 22.1 / 19.0 / 15.7.

**BW + PLI + EM + MA (Fig. 11)**

| SNRin | -5 | -2 | 0 | 3 | 6 | 10 |
|---|---|---|---|---|---|---|
| PEAF, paper | 10.2 | 9.5 | 9.4 | 7.0 | 5.6 | 4.3 |
| raw: PEAF / SEAF, paper eqs | 10.4 / 11.0 | 9.7 / 10.3 | 9.2 / 9.8 | 8.3 / 8.8 | 7.2 / 7.7 | 5.1 / 5.5 |
| raw: PEAF / SEAF, + residue | 8.5 / 10.5 | 8.2 / 10.2 | 7.9 / 9.8 | 7.1 / 8.8 | 6.0 / 7.5 | 3.7 / 4.9 |
| norm: PEAF / SEAF, + residue | 11.2 / 12.3 | 10.5 / 11.6 | 9.8 / 10.8 | 8.5 / 9.3 | 6.7 / 7.5 | 3.8 / 4.3 |
| raw: PDAF / SDAF | 11.3 / 12.9 | 11.2 / 12.4 | 11.1 / 11.9 | 10.7 / 10.9 | 10.0 / 9.4 | 8.6 / 6.7 |
| norm: PDAF / SDAF | 14.3 / 11.4 | 13.8 / 10.7 | 13.2 / 10.0 | 12.1 / 8.7 | 10.6 / 6.9 | 7.9 / 3.9 |

- Filtering the residue makes EMD worthwhile for BW + PLI: EMD + LMS gains up to 9 dB and, with
  the normalized ECG, beats LMS without EMD at 4 of 5 SNRin levels. EMD + RLS comes close to the
  paper's Fig. 8 numbers.
- With all four noises the paper's ranking is still not reproduced: PDAF (one filter, no EMD)
  is best on all 13 records at 10 dB (Fig. 10). SEAF beats PEAF. Residue filtering helps PEAF
  and SEAF with the normalized ECG (+1 to +2 dB at low SNRin) but costs PEAF ~2 dB with the raw
  ECG. Filtering the residue only in the BW branch was also tried: worse (PEAF 6.0 dB at -5 dB).
- NLMS with MATLAB's default step 0.1 is worst in every case; RLS beats LMS (Fig. 7).

## Does normalizing the ECG help?

It depends on the method (`scripts/04_ecg_norm_check.py`). Mean change in SNRimp, normalized
minus raw: PEAF +1.6 dB, PDAF +1.5 dB, SEAF +0.7 dB, EMD + LMS +0.4 dB, RLS -1.2 dB,
NLMS -2.0 dB, SDAF -2.1 dB. Scaling the ECG alone changes nothing (LMS is linear in its
input); the difference comes from removing the DC offset. The raw MIT-BIH ECG has a large
offset (up to 92 % of its power, record 121), which Eq. (4) counts as signal, so at a given
SNRin the raw ECG gets more noise relative to its waveform. Normalizing gives a fairer SNR
definition and helps the paper's proposed methods (PEAF, SEAF) with residue filtering.
