"""
Tuning of the adaptive filter settings (not given in the paper).

Every filter of every method gets its own setting: (mu, taps) for LMS / NLMS, (lambda,
taps) for RLS. A method's filters are tuned together by coordinate descent: starting from
"all filters off", each filter in turn gets the grid setting with the highest mean SNRimp
over the tuning cases while the others stay fixed; this is repeated TUNING_PASSES times.
A setting that makes the output diverge in any case is never chosen.
"""
import hashlib
from collections import OrderedDict

import numpy as np

from src.config import (LMS_MUS, LMS_TAPS, NLMS_MUS, RLS_LAMBDAS, RLS_TAPS, TUNING_PASSES)
from src.filters import diverged
from src.methods import METHODS, FilterBank
from src.metrics import snr_imp


def grid(algorithm):
    """All settings searched for one filter."""
    if algorithm == "RLS":
        return [{"lam": lam, "taps": t} for lam in RLS_LAMBDAS for t in RLS_TAPS]
    mus = NLMS_MUS if algorithm == "NLMS" else LMS_MUS
    return [{"mu": mu, "taps": t} for mu in mus for t in LMS_TAPS]


def start_setting(algorithm):
    """Starting point of the search: LMS / NLMS off (mu = 0), RLS with one tap."""
    return {"lam": 1.0, "taps": 1} if algorithm == "RLS" else {"mu": 0.0, "taps": 1}


class CachedFilterBank(FilterBank):
    """FilterBank that remembers its last few outputs, so filters whose input and setting
    did not change are not run again during the grid search."""

    def __init__(self, algorithm, refs, params, cache, size=16):
        super().__init__(algorithm, refs, params)
        self.cache, self.size = cache, size

    def __call__(self, d, noise):
        digest = hashlib.blake2b(np.ascontiguousarray(d).tobytes(), digest_size=16).digest()
        key = (noise, tuple(sorted(self.params[noise].items())), digest)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        out = super().__call__(d, noise)
        self.cache[key] = out
        if len(self.cache) > self.size:
            self.cache.popitem(last=False)
        return out


def mean_snr_imp(name, cases, params, caches):
    """Mean SNRimp of method `name` over the cases; -inf if it diverges in any case."""
    m = METHODS[name]
    scores = []
    for (case, imfs, r), cache in zip(cases, caches):
        f = CachedFilterBank(m.algorithm, case["refs"], params, cache)
        y = m.function(case["noisy"], imfs, r, f)
        if diverged(case["noisy"], y):
            return -np.inf
        scores.append(snr_imp(case["clean"], case["noisy"], y))
    return float(np.mean(scores))


def tune(name, cases):
    """
    cases: list of (case, imfs, r). Returns (params, rows): the chosen setting of every
    filter, and one row per evaluated setting (pass, filter, setting, mean SNRimp).
    """
    m = METHODS[name]
    params = {f: start_setting(m.algorithm) for f in m.filters}
    caches = [OrderedDict() for _ in cases]
    rows = []
    for p in range(TUNING_PASSES):
        for filt in m.filters:
            best, best_score = params[filt], -np.inf
            for setting in grid(m.algorithm):
                score = mean_snr_imp(name, cases, {**params, filt: setting}, caches)
                rows.append({"method": name, "pass": p + 1, "filter": filt, **setting,
                             "mean_SNRimp_dB": score})
                if score > best_score:
                    best, best_score = setting, score
            params[filt] = best
    return params, rows
