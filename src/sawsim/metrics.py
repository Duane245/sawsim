"""Resonator figures of merit from a sampled admittance curve.

fr = |Y| maximum, fa = following |Y| minimum.  Both are refined between samples
with a V-fit (exact for an isolated lossless pole/zero on a smooth background),
so the reported uncertainty is half a frequency step.
k2eff = pi^2/4 * (fa - fr) / fa.
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


MIN_SAMPLES_IN_LINEWIDTH = 8   # a 3 dB width spanning fewer samples is a sampling artefact, not a Q


def peak_quality(f, power):
    """Q of the highest peak of `power` (|Y|^2 for fr, |Z|^2 for fa) in a window that resolves it.

    Peak: parabola through the top three samples. Half-power points: linear interpolation
    of power. Returns None when a half-power crossing lies outside the window.
    """
    f = np.asarray(f, dtype=float)
    p = np.asarray(power, dtype=float)
    i = int(np.argmax(p))
    if i in (0, len(p) - 1):
        return None
    y0, y1, y2 = p[i - 1], p[i], p[i + 1]
    den = y0 - 2 * y1 + y2
    shift = 0.5 * (y0 - y2) / den if den < 0 else 0.0
    h = f[i + 1] - f[i]
    f0 = f[i] + np.clip(shift, -0.5, 0.5) * h
    peak = y1 - 0.25 * (y0 - y2) * np.clip(shift, -0.5, 0.5)
    half = peak / 2
    left = [j for j in range(i, 0, -1) if p[j - 1] <= half < p[j]]
    right = [j for j in range(i, len(p) - 1) if p[j + 1] <= half < p[j]]
    if not left or not right:
        return None
    a, b = left[0], right[0]
    fl = f[a - 1] + (half - p[a - 1]) / (p[a] - p[a - 1]) * (f[a] - f[a - 1])
    fh = f[b] + (p[b] - half) / (p[b] - p[b + 1]) * (f[b + 1] - f[b])
    return dict(f0_hz=float(f0), fl_hz=float(fl), fh_hz=float(fh), q=float(f0 / (fh - fl)),
                samples_in_linewidth=int(b - a + 1), step_hz=float(h))


def peak_quality_extrapolated(f, power):
    """peak_quality with the linear-interpolation bias removed.

    The half-power interpolation error scales as 1/n^2 (n = samples per linewidth), so combining the
    full sampling with every other sample (both offsets averaged) gives Q = Q_n + (Q_n - Q_n/2) / 3.
    """
    full = peak_quality(f, power)
    if full is None:
        return None
    halves = [peak_quality(np.asarray(f)[k::2], np.asarray(power)[k::2]) for k in (0, 1)]
    halves = [h['q'] for h in halves if h]
    if not halves:
        return dict(full, q_linear=full['q'], q_half=None)
    q_half = float(np.mean(halves))
    return dict(full, q=full['q'] + (full['q'] - q_half) / 3, q_linear=full['q'], q_half=q_half)


def _half_power_q(f, mag, i, lo, hi):
    """3 dB Q around a peak of `mag` at index i, searched inside [lo, hi]; None unless well resolved."""
    p = mag ** 2
    half = p[i] / 2
    left = [j for j in range(i - 1, lo - 1, -1) if p[j] <= half]
    right = [j for j in range(i + 1, hi + 1) if p[j] <= half]
    if not left or not right or right[0] - left[0] < MIN_SAMPLES_IN_LINEWIDTH:
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
    # |Y|/f removes the static-capacitance slope (|Y| ~ 2 pi f C0), so weakly coupled
    # resonances appear as a local max (fr) followed by a local min (fa) on a flat background.
    g = mag / f
    inv = 1.0 / np.maximum(g, np.finfo(float).tiny)
    peaks = _local_extrema(g, True)
    pairs = []  # (score, fr index, fa index, next peak index)
    for i, p in enumerate(peaks):
        stop = int(peaks[i + 1]) if i + 1 < len(peaks) else n - 1
        a = int(p) + int(np.argmin(g[p:stop + 1]))
        if a == p:
            continue
        if a != n - 1 and f[a] - f[p] > 0.15 * f[p]:
            continue  # broad hump (bulk-wave region), not a resonator pole/zero pair
        pairs.append(((g[p] - g[a]) / g[p], int(p), a, stop))
    if not pairs:
        if int(np.argmax(g)) in (0, n - 1):
            out['warnings'].append('peak_at_band_edge: the response rises towards the band edge and no resonance '
                                   'is inside the band - widen or shift start_ghz/stop_ghz')
        else:
            out['warnings'].append('no_resonance_found: no resonance/antiresonance pair in band; for weak coupling '
                                   'increase points so the fr..fa gap is sampled')
        return _rounded(out)
    # Main mode: among well-resolved pairs (relative dip >= 0.5, i.e. every strong lossless
    # resonance) the highest |Y|/f peak; weak resonances compete by relative dip.
    score, r, a, stop = max(pairs, key=lambda t: (min(t[0], 0.5), g[t[1]]))
    fr = _vfit(f, inv, r)
    out['fr_ghz'] = fr * 1e-9
    prev_min = _local_extrema(g, False)
    lo = int(prev_min[prev_min < r][-1]) if np.any(prev_min < r) else 0
    out['q_r'] = _half_power_q(f, mag, r, lo, a)
    if a == n - 1:
        out['warnings'].append('antiresonance_not_found: no |Y| minimum after fr inside the band - '
                               'extend stop_ghz')
    else:
        fa = _vfit(f, g, a)
        out['fa_ghz'] = fa * 1e-9
        out['k2eff'] = math.pi ** 2 / 4 * (fa - fr) / fa
        out['points_between_fr_fa'] = int(a - r - 1)
        out['q_a'] = _half_power_q(f, 1.0 / np.maximum(mag, np.finfo(float).tiny), a, r, stop)
        if a - r < 6:
            out['warnings'].append('coarse_sampling: fewer than 5 samples between fr and fa; zoom the band '
                                   'to about [fr - (fa-fr), fa + (fa-fr)] with >= 81 points')
    if max(g[0], g[-1]) > 3 * g[r]:
        out['warnings'].append('stronger_response_at_band_edge: |Y|/f at a band edge exceeds the main peak; '
                               'a stronger resonance may lie just outside the band')
    if out['q_r'] is None:
        out['notes'].append('Q not resolved at this frequency step (3 dB width spans < %d samples); q_r/q_a are '
                            'null - locate with beta_dk/eta_eps > 0 resolves Q' % MIN_SAMPLES_IN_LINEWIDTH)
    for s, p, q, _ in sorted(pairs, key=lambda t: (min(t[0], 0.5), g[t[1]]), reverse=True)[:max_modes]:
        out['modes'].append(dict(fr_ghz=_vfit(f, inv, p) * 1e-9,
                                 fa_ghz=_vfit(f, g, q) * 1e-9 if q != n - 1 else None,
                                 peak_abs_y=float(mag[p]), strength=float(s), is_main=bool(p == r)))
    out['modes'].sort(key=lambda m: m['fr_ghz'])
    if sum(1 for m in out['modes'] if m['strength'] > 0.5 * min(score, 0.5) and m['peak_abs_y'] > 0.1 * mag[r]) > 1:
        out['warnings'].append('multiple_modes: other strong resonances are in band; check that the main pair '
                               '(largest relative dip from fr to fa) is the intended mode')
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
