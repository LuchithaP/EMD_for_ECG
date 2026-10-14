# Comparison with the paper

Each cell: **ours (paper)**. Paper values were measured from the PDF figures (about +-0.2 dB). See README.md for the settings the paper does not give.

Noise power shares in the four-noise experiments (NSTDB natural ratio, PLI = BW power): BW 24.7 %, EM 46.6 %, MA 3.9 %, PLI 24.7 %.

## Sec. III-A: IMFs for each noise (each noise alone, held-out cases)

| noise | best IMFs (ours) | SNRimp | paper's IMFs | SNRimp | no EMD SNRimp |
|---|---|---|---|---|---|
| PLI | IMF1 | 28.98 | IMF1 | 28.98 | 27.31 |
| BW | no EMD | 14.22 | IMF5~8 | 13.88 | 14.22 |
| EM | IMF1~8 | 13.69 | IMF3~8 | 13.45 | 13.57 |
| MA | no EMD | 13.47 | no EMD | 13.47 | 13.47 |

## Tuned filter settings

- **EMD+LMS**: PLI mu=0.01, taps=16; BW mu=0.0003, taps=8
- **EMD+NLMS**: PLI mu=0.03, taps=16; BW mu=0.001, taps=64
- **EMD+RLS**: PLI lam=1, taps=4; BW lam=1, taps=8
- **PEAF**: PLI mu=0.03, taps=4; BW mu=3e-05, taps=32; EM mu=0.0001, taps=8; MA mu=0.003, taps=4
- **SEAF**: PLI mu=0.03, taps=4; BW mu=0.0001, taps=8; EM mu=0.0001, taps=8; MA mu=0.003, taps=4
- **PDAF**: ALL mu=0.0003, taps=8
- **SDAF**: PLI mu=0.003, taps=16; BW mu=0.0001, taps=8; EM mu=0.0001, taps=8; MA mu=0.003, taps=4

## Fig. 7: SNR output (dB), BW + PLI, mean over records [119, 202, 213, 217, 234]

| SNRin | -5 dB | 0 dB | 5 dB | 7 dB | 10 dB |
|---|---|---|---|---|---|
| EMD+LMS | 13.43 (10) | 17.33 (11) | 20.11 (12.4) | 20.62 (17.3) | 21.42 (22.2) |
| EMD+RLS | 20.18 (8.2) | 21.04 (9.1) | 23.81 (12.2) | 23.55 (16.6) | 23.62 (21.9) |
| EMD+NLMS | 9.75 (5.1) | 11.72 (7.2) | 12.72 (13.1) | 12.42 (18.6) | 13.32 (24.4) |

## Fig. 7: RMSE, BW + PLI, mean over records [119, 202, 213, 217, 234]

| SNRin | -5 dB | 0 dB | 5 dB | 7 dB | 10 dB |
|---|---|---|---|---|---|
| EMD+LMS | 0.04 (0.05) | 0.02 (0.046) | 0.02 (0.039) | 0.02 (0.022) | 0.02 (0.012) |
| EMD+RLS | 0.02 (0.063) | 0.02 (0.057) | 0.01 (0.04) | 0.01 (0.024) | 0.01 (0.013) |
| EMD+NLMS | 0.06 (0.092) | 0.05 (0.072) | 0.04 (0.036) | 0.04 (0.019) | 0.04 (0.009) |

## Fig. 8: SNR output at SNRin = 10 dB, BW + PLI

| record | 119 | 202 | 213 | 217 | 234 |
|---|---|---|---|---|---|
| EMD+LMS | 24.85 (24.7) | 19.45 (22.9) | 23.70 (25) | 20.26 (29.2) | 18.86 (23.9) |
| Article [28] (paper) | 18 | 23 | 20 | 26 | 20.5 |
| Article [21] (paper) | 16.5 | 20.5 | 18 | 24 | 19 |
| Article [22] (paper) | 14 | 18.9 | 16 | 23.1 | 18.6 |

## Fig. 10: SNRimp per record, ours at SNRin = -5 dB

| record | PEAF | SEAF | PDAF | SDAF | best (ours) |
|---|---|---|---|---|---|
| 100 | 12.96 (10.95) | 13.66 (10.2) | 15.97 (10.25) | 13.77 (9.75) | PDAF |
| 103 | 13.23 (10.65) | 14.05 (10) | 16.26 (9.9) | 14.09 (9.6) | PDAF |
| 104 | 12.61 (10.25) | 13.24 (10) | 14.91 (9.8) | 13.51 (9.4) | PDAF |
| 105 | 12.99 (9.5) | 13.81 (9) | 16.18 (8.65) | 13.99 (8.45) | PDAF |
| 106 | 12.88 (10.6) | 13.83 (9.75) | 15.65 (9.7) | 13.94 (9.25) | PDAF |
| 111 | 10.82 (9.95) | 12.27 (9.4) | 13.32 (8.75) | 12.19 (8.45) | PDAF |
| 113 | 11.64 (9.25) | 12.30 (8.2) | 13.62 (7.1) | 12.43 (6.9) | PDAF |
| 115 | 11.92 (10.95) | 12.47 (10.6) | 14.00 (10.15) | 12.63 (10.15) | PDAF |
| 116 | 13.03 (9.35) | 13.60 (8.75) | 15.95 (8.7) | 13.61 (8.2) | PDAF |
| 121 | 12.25 (9.85) | 13.04 (8.15) | 14.52 (6.4) | 12.96 (6.35) | PDAF |
| 122 | 12.51 (10) | 13.42 (9.35) | 14.67 (8.75) | 13.51 (8.3) | PDAF |
| 123 | 12.85 (10.15) | 13.00 (9.95) | 12.40 (9.95) | 13.01 (9.65) | SDAF |
| 231 | 13.14 (9.55) | 13.81 (8.6) | 15.65 (8.9) | 14.02 (8.25) | PDAF |

## Fig. 10: SNRimp per record, ours at SNRin = 10 dB

| record | PEAF | SEAF | PDAF | SDAF | best (ours) |
|---|---|---|---|---|---|
| 100 | 9.01 (10.95) | 9.42 (10.2) | 9.60 (10.25) | 9.57 (9.75) | PDAF |
| 103 | 10.36 (10.65) | 10.99 (10) | 12.01 (9.9) | 11.27 (9.6) | PDAF |
| 104 | 7.10 (10.25) | 7.27 (10) | 5.40 (9.8) | 7.56 (9.4) | SDAF |
| 105 | 10.21 (9.5) | 11.03 (9) | 10.34 (8.65) | 11.58 (8.45) | SDAF |
| 106 | 8.52 (10.6) | 9.44 (9.75) | 7.80 (9.7) | 9.58 (9.25) | SDAF |
| 111 | 0.90 (9.95) | 2.21 (9.4) | 1.15 (8.75) | 2.30 (8.45) | SDAF |
| 113 | 2.80 (9.25) | 3.16 (8.2) | 1.84 (7.1) | 3.35 (6.9) | SDAF |
| 115 | 2.84 (10.95) | 2.98 (10.6) | 2.67 (10.15) | 3.03 (10.15) | SDAF |
| 116 | 9.40 (9.35) | 9.46 (8.75) | 9.74 (8.7) | 9.85 (8.2) | SDAF |
| 121 | 4.13 (9.85) | 4.83 (8.15) | 4.21 (6.4) | 4.83 (6.35) | SDAF |
| 122 | 6.34 (10) | 7.37 (9.35) | 4.56 (8.75) | 7.35 (8.3) | SEAF |
| 123 | 2.20 (10.15) | 2.56 (9.95) | -0.59 (9.95) | 2.53 (9.65) | SEAF |
| 231 | 10.74 (9.55) | 11.02 (8.6) | 8.13 (8.9) | 11.14 (8.25) | SDAF |

## Fig. 11: SNRimp vs SNRin, mean over 13 records

| SNRin | -5 dB | -2 dB | 0 dB | 3 dB | 6 dB | 10 dB |
|---|---|---|---|---|---|---|
| PEAF | 12.53 (10.35) | 12.04 (9.55) | 11.52 (9.35) | 10.46 (7.15) | 9.10 (5.55) | 6.50 (4.3) |
| SEAF | 13.27 (10.4) | 12.77 (9.1) | 12.22 (8.8) | 11.12 (6.8) | 9.72 (5.3) | 7.06 (4.1) |
| PDAF | 14.86 (10.25) | 13.85 (9.2) | 12.96 (8.7) | 11.27 (6.6) | 9.19 (4.75) | 5.91 (3.45) |
| SDAF | 13.36 (10.25) | 12.83 (8.75) | 12.32 (8.15) | 11.26 (6.15) | 9.80 (4.5) | 7.23 (3.4) |

## Claims of the paper

| claim | ours | reproduced |
|---|---|---|
| Sec. III-A: IMF1 is the best input for PLI | best: IMF1 28.98 dB; paper's IMF1 28.98 dB | Yes |
| Sec. III-A: IMF5~8 is the best input for BW | best: no EMD 14.22 dB; paper's IMF5~8 13.88 dB | Partly |
| Sec. III-A: IMF3~8 is the best input for EM | best: IMF1~8 13.69 dB; paper's IMF3~8 13.45 dB | Partly |
| Sec. III-A: no EMD is the best input for MA | best: no EMD 13.47 dB; paper's no EMD 13.47 dB | Yes |
| Fig. 7: LMS is better and more stable than NLMS and RLS | LMS has the best SNRout at 0/5 SNRin (winners: EMD+RLS, EMD+RLS, EMD+RLS, EMD+RLS, EMD+RLS) | No |
| Fig. 8: EMD + LMS beats articles [28, 21, 22] (their values as reported) | ours better than the best article on 2/5 records | Partly |
| Fig. 8: our EMD + LMS SNR output matches the paper's | mean difference -3.72 dB, mean |difference| 3.78 dB | Partly |
| Fig. 10 (SNRin -5 dB): PEAF is best on every record | PEAF best on 0/13 records; mean SNRimp PEAF 12.53, SEAF 13.27, PDAF 14.86, SDAF 13.36 | No |
| Fig. 10 (SNRin 10 dB): PEAF is best on every record | PEAF best on 0/13 records; mean SNRimp PEAF 6.50, SEAF 7.06, PDAF 5.91, SDAF 7.23 | No |
| Fig. 11: PEAF is best at every SNRin | PEAF best at 0/6 SNRin (winners: PDAF, PDAF, PDAF, PDAF, SDAF, SDAF) | No |
| Figs. 10-11: EMD + adaptive filter beats adaptive filter only | best EMD method (PEAF/SEAF) beats best direct method (PDAF/SDAF) at 0/6 SNRin | No |
| Fig. 11: SNRimp falls as SNRin rises | true for 4/4 methods (PEAF, SEAF, PDAF, SDAF) | Yes |
| Fig. 11: our PEAF SNRimp matches the paper's | mean difference +2.65 dB, mean |difference| 2.65 dB | Partly |
