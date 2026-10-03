"""Every template reproduces (a) its own published curve and (b) the independent reference FEM."""
import numpy as np
import pytest

from conftest import HEX, MODELS, load_case
from sawsim import Model, sweep


def _params():
    return [pytest.param(m, marks=pytest.mark.slow) if m in HEX else m for m in MODELS]


@pytest.mark.parametrize('model', _params())
def test_template(model, tmp_path):
    meta, d = load_case(model)
    cfg = dict(meta['config'])
    f_all = d['frequency_hz']
    idx = np.array(meta['test_indices'])
    cfg.update(points=meta['test_points'], start_ghz=f_all[idx[0]] / 1e9, stop_ghz=f_all[idx[-1]] / 1e9)

    res = sweep(Model(**cfg), tmp_path / model)
    f = res.frequency_ghz * 1e9
    assert np.allclose(f, f_all[idx], rtol=0, atol=1.0), 'sweep grid must land on the report frequencies'
    mag = res.magnitude
    if meta.get('compare_raw_slice_admittance'):
        # 2.5D reports compare the total slice admittance (S), curve.json is per unit aperture (S/m)
        mag = mag * float(res.metadata['aperture_m'])

    # (a) regression against this solver's own published curve
    own = d['sawsim_magnitude'][idx]
    diff = np.max(np.abs(mag - own) / np.abs(own))
    assert diff <= meta['regression_rtol'], f'{model}: max rel diff vs published curve {diff:.2e}'

    # (b) agreement with the independent reference (sp_triple_layer: below 2.35 GHz only)
    ref = d['reference_magnitude'][idx]
    fmax = meta['reference_fmax_hz']
    mask = np.ones_like(ref, dtype=bool) if fmax is None else f <= fmax
    err = np.max(np.abs(mag[mask] - ref[mask]) / np.abs(ref[mask]))
    assert err <= meta['reference_rtol'], f'{model}: max rel error vs reference {err:.3g} > {meta["reference_rtol"]:.3g}'
