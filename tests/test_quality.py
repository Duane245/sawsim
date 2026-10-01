"""Material loss, passive admittance sign and Q extraction."""
import json
import os

import numpy as np
import pytest

from sawsim import agent
from sawsim.metrics import peak_quality, peak_quality_extrapolated


def _resonator(f, fr, qr, fa, qa):
    """BVD-like lossy admittance with poles/zeros fr(1 + i/2Q)."""
    pr, pa = fr * (1 + 0.5j / qr), fa * (1 + 0.5j / qa)
    return 1j * f * (f ** 2 - pa ** 2) / (f ** 2 - pr ** 2)


@pytest.mark.parametrize('per_linewidth', [13, 26, 45])
def test_extrapolated_q_recovers_true_q(per_linewidth):
    fr, q = 1.75e9, 900.0
    lw = fr / q
    f = np.linspace(fr - 1.5 * lw, fr + 1.5 * lw, 3 * per_linewidth + 1)
    y = _resonator(f, fr, q, 1.82e9, 900.0)
    r = peak_quality_extrapolated(f, np.abs(y) ** 2)
    assert abs(r['q'] / q - 1) < 4e-3 and abs(r['f0_hz'] / fr - 1) < 1e-5
    assert abs(r['q'] - q) <= abs(r['q_linear'] - q) + 1e-9      # extrapolation never makes it worse here


def test_peak_quality_needs_both_half_power_points():
    f = np.linspace(1.7e9, 1.71e9, 41)
    y = _resonator(f, 1.7097e9, 900, 1.8e9, 900)                 # right half-power point beyond the window
    assert peak_quality(f, np.abs(y) ** 2) is None


def test_lossy_run_is_passive(tmp_path, monkeypatch):
    monkeypatch.setenv('SAWSIM_RUNS_DIR', str(tmp_path))
    cfg = dict(model_id='sp_single_layer', points=9, start_ghz=1.78, stop_ghz=1.84, beta_dk=1e-13, eta_eps=1.5e-3)
    s = agent.run(cfg)
    c = json.loads((tmp_path / os.path.basename(s['output_dir']) / 'curve.json').read_text())
    assert s['ok'] and min(c['real']) > 0                         # passive port: conductance >= 0
    meta = json.loads((tmp_path / os.path.basename(s['output_dir']) / 'metadata.json').read_text())
    assert meta['loss']['beta_dk'] == 1e-13 and meta['loss']['eta_eps'] == 1.5e-3 and meta['admittance_convention'].startswith('passive')


def test_loss_rejected_for_2p5d():
    assert not agent.validate(dict(model_id='sp_2p5d_single_layer', beta_dk=1e-13))['ok']


@pytest.mark.slow
@pytest.mark.skipif(not os.environ.get('SAWSIM_TEST_ALL'), reason='lossy locate with Q windows, minutes')
def test_lossy_locate_q_tcsaw(tmp_path, monkeypatch):
    """Reference-model TC-SAW loss settings. Reference: 401-point brute-force sweep across fr gives Q_r = 1639.12."""
    monkeypatch.setenv('SAWSIM_RUNS_DIR', str(tmp_path))
    r = agent.locate(dict(model_id='sp_tcsaw', beta_dk=1e-13, eta_eps=1.5e-3))
    assert r['ok'] and abs(r['q_r'] / 1639.12 - 1) < 2e-3 and abs(r['q_a'] / 1651.82 - 1) < 3e-3
    assert abs(r['fr_ghz'] - 1.7588447) < 2e-5 and abs(r['fa_ghz'] - 1.8183068) < 2e-5
