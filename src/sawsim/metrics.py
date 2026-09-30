"""Resonator figures of merit from a sampled admittance curve.

fr = |Y| maximum, fa = following |Y| minimum.  Both are refined between samples
with a V-fit (exact for an isolated lossless pole/zero on a smooth background),
so the reported uncertainty is half a frequency step.
k2eff = pi^2/4 * (fa - fr) / fa  (same estimate as the web UI).
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

K2_FORMULA = 'k2eff = pi^2/4 * (fa - fr) / fa'


def _vfit(f, g, i):
    """Vertex of a V through the minimum sample g[i] and its two neighbours."""
    if i <= 0 or i >= len(g) - 1:
        return float(f[i])
    h = 0.5 * (f[i + 1] - f[i - 1])
    s = max(g[i - 1] - g[i], g[i + 1] - g[i]) / h
    if not s > 0:
        return float(f[i])
    v = (g[i - 1] - g[i + 1]) / (2 * s)
    return float(f[i] + np.clip(v, -h / 2, h / 2))


def _local_extrema(y, maxima=True):
    s = y if maxima else -y
    return np.flatnonzero((s[1:-1] > s[:-2]) & (s[1:-1] >= s[2:])) + 1


def _half_power_q(f, mag, i, lo, hi):
    """3 dB Q around a peak of `mag` at index i, searched inside [lo, hi]; None if unresolved."""
    p = mag ** 2
    half = p[i] / 2
    left = [j for j in range(i - 1, lo - 1, -1) if p[j] <= half]
    right = [j for j in range(i + 1, hi + 1) if p[j] <= half]
    if not left or not right or right[0] - left[0] < 4:
        return None
    a, b = left[0], right[0]
    fl = np.interp(half, [p[a], p[a + 1]], [f[a], f[a + 1]])
    fh = np.interp(half, [p[b], p[b - 1]], [f[b], f[b - 1]])
    return float(f[i] / (fh - fl)) if fh > fl else None


def resonances(frequency_hz, admittance, max_modes: int = 5) -> dict:
    """Main resonance/antiresonance pair, other in-band modes and warnings.

    `admittance` may be complex Y or |Y|.  Frequencies in Hz; outputs in GHz/MHz.
    """
    f = np.asarray(frequency_hz, dtype=float)
    mag = np.abs(np.asarray(admittance))
    n = len(f)
    out = dict(fr_ghz=None, fa_ghz=None, k2eff=None, k2_formula=K2_FORMULA, q_r=None, q_a=None,
               frequency_step_mhz=None, uncertainty_mhz=None, points_between_fr_fa=None,
               modes=[], warnings=[], notes=[])
    if n < 5 or not np.all(np.isfinite(mag)):
        out['warnings'].append('curve too short or contains non-finite values')
        return out
    df = float(np.max(np.diff(f)))
    out['frequency_step_mhz'] = df * 1e-6
    out['uncertainty_mhz'] = df * 0.5e-6
    r = int(np.argmax(mag))
    if r in (0, n - 1):
        out['warnings'].append('peak_at_band_edge: the |Y| maximum is at the band edge; the true resonance '
                               'is probably outside the band - widen or shift start_ghz/stop_ghz')
        return out
    peaks = _local_extrema(mag, True)
    nxt = peaks[peaks > r]
    stop = int(nxt[0]) if len(nxt) else n - 1
    a = r + int(np.argmin(mag[r:stop + 1]))
    inv = 1.0 / np.maximum(mag, np.finfo(float).tiny)
    fr = _vfit(f, inv, r)
    out['fr_ghz'] = fr * 1e-9
    prev_min = _local_extrema(mag, False)
    lo = int(prev_min[prev_min < r][-1]) if np.any(prev_min < r) else 0
    out['q_r'] = _half_power_q(f, mag, r, lo, a)
    if a in (r, n - 1):
        out['warnings'].append('antiresonance_not_found: no |Y| minimum after fr inside the band - '
                               'extend stop_ghz')
    else:
        fa = _vfit(f, mag, a)
        out['fa_ghz'] = fa * 1e-9
        out['k2eff'] = math.pi ** 2 / 4 * (fa - fr) / fa
        out['points_between_fr_fa'] = int(a - r - 1)
        out['q_a'] = _half_power_q(f, inv, a, r, stop)
        if a - r < 6:
            out['warnings'].append('coarse_sampling: fewer than 5 samples between fr and fa; zoom the band '
                                   'to about [fr - (fa-fr), fa + (fa-fr)] with >= 81 points')
    if out['q_r'] is None:
        out['notes'].append('Q not resolved at this frequency step (expected: the solver model is lossless, '
                            'so resonances are poles); q_r/q_a are null')
    mins = _local_extrema(mag, False)
    for p in sorted(peaks, key=lambda j: -mag[j])[:max_modes]:
        after = mins[mins > p]
        out['modes'].append(dict(fr_ghz=_vfit(f, inv, int(p)) * 1e-9,
                                 fa_ghz=(_vfit(f, mag, int(after[0])) * 1e-9) if len(after) else None,
                                 peak_abs_y=float(mag[p]), is_main=bool(p == r)))
    out['modes'].sort(key=lambda m: m['fr_ghz'])
    if sum(1 for m in out['modes'] if m['peak_abs_y'] > 0.1 * mag[r]) > 1:
        out['warnings'].append('multiple_modes: other peaks above 10% of the main |Y| peak are in band; '
                               'check that the main pair is the intended mode')
    return _rounded(out)


def _rounded(d):
    """Trim float noise: GHz to 0.1 kHz, MHz to 0.1 kHz, other floats to 6 significant digits."""
    def r(k, v):
        if isinstance(v, float):
            return round(v, 7) if k.endswith('_ghz') else round(v, 4) if k.endswith('_mhz') else float('%.6g' % v)
        if isinstance(v, dict):
            return {kk: r(kk, vv) for kk, vv in v.items()}
        if isinstance(v, list):
            return [r(k, x) for x in v]
        return v
    return r('', d)


def compare(reference: dict, candidate: dict) -> dict:
    """fr/fa/k2 deviation of `candidate` relative to `reference` (both from resonances())."""
    d = {}
    for key in ('fr_ghz', 'fa_ghz'):
        a, b = reference.get(key), candidate.get(key)
        d[key.replace('_ghz', '_diff_mhz')] = None if a is None or b is None else (b - a) * 1e3
        d[key.replace('_ghz', '_diff_ppm')] = None if a is None or b is None else (b - a) / a * 1e6
    a, b = reference.get('k2eff'), candidate.get('k2eff')
    d['k2eff_diff_pct_points'] = None if a is None or b is None else (b - a) * 100
    return _rounded(d)
