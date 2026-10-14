"""
Numbers of the paper's result figures, measured from the PDF rendered at 450 dpi
(bar tops / line points against the gridlines; about +-0.2 dB, +-0.001 RMSE).
"""

# Fig. 7: LMS / NLMS / RLS with EMD, BW + PLI, at SNRin = -5, 0, 5, 7, 10 dB
FIG7_SNRS = [-5, 0, 5, 7, 10]
FIG7_SNR_OUT = {
    "EMD+LMS": [10.0, 11.0, 12.4, 17.3, 22.2],
    "EMD+RLS": [8.2, 9.1, 12.2, 16.6, 21.9],
    "EMD+NLMS": [5.1, 7.2, 13.1, 18.6, 24.4],
}
FIG7_RMSE = {
    "EMD+LMS": [0.050, 0.046, 0.039, 0.022, 0.012],
    "EMD+RLS": [0.063, 0.057, 0.040, 0.024, 0.013],
    "EMD+NLMS": [0.092, 0.072, 0.036, 0.019, 0.009],
}

# Fig. 8: SNR output at SNRin = 10 dB on records 119, 202, 213, 217, 234
FIG8_RECORDS = [119, 202, 213, 217, 234]
FIG8_SNR_OUT = {
    "EMD+LMS": [24.7, 22.9, 25.0, 29.2, 23.9],
    "Article [28]": [18.0, 23.0, 20.0, 26.0, 20.5],
    "Article [21]": [16.5, 20.5, 18.0, 24.0, 19.0],
    "Article [22]": [14.0, 18.9, 16.0, 23.1, 18.6],
}

# Fig. 10: SNRimp per record (text: SNRin = 10 dB; the values match Fig. 11 at -5 dB)
FIG10_RECORDS = [100, 103, 104, 105, 106, 111, 113, 115, 116, 121, 122, 123, 231]
FIG10_SNR_IMP = {
    "PEAF": [10.95, 10.65, 10.25, 9.5, 10.6, 9.95, 9.25, 10.95, 9.35, 9.85, 10.0, 10.15, 9.55],
    "SEAF": [10.2, 10.0, 10.0, 9.0, 9.75, 9.4, 8.2, 10.6, 8.75, 8.15, 9.35, 9.95, 8.6],
    "PDAF": [10.25, 9.9, 9.8, 8.65, 9.7, 8.75, 7.1, 10.15, 8.7, 6.4, 8.75, 9.95, 8.9],
    "SDAF": [9.75, 9.6, 9.4, 8.45, 9.25, 8.45, 6.9, 10.15, 8.2, 6.35, 8.3, 9.65, 8.25],
}

# Fig. 11: SNRimp vs SNRin
FIG11_SNRS = [-5, -2, 0, 3, 6, 10]
FIG11_SNR_IMP = {
    "PEAF": [10.35, 9.55, 9.35, 7.15, 5.55, 4.3],
    "SEAF": [10.4, 9.1, 8.8, 6.8, 5.3, 4.1],
    "PDAF": [10.25, 9.2, 8.7, 6.6, 4.75, 3.45],
    "SDAF": [10.25, 8.75, 8.15, 6.15, 4.5, 3.4],
}

# Sec. III-A: best IMFs for each noise
IMF_CHOICE = {"pli": "IMF1", "bw": "IMF5~8", "em": "IMF3~8", "ma": "no EMD"}
