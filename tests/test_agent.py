"""Agent interface: metrics, JSON operations and the --json CLI contract."""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from conftest import MODELS, load_case
from sawsim import agent
from sawsim.metrics import compare, resonances


def _lorentz_curve(fr, fa, n=201, lo=1.6e9, hi=2.0e9):
    """|Y| of a lossless BVD-like resonator: zero at fa, pole at fr."""
    f = np.linspace(lo, hi, n)
    return f, np.abs(f * (f ** 2 - fa ** 2) / (f ** 2 - fr ** 2))


def test_resonances_synthetic_subgrid():
    f, y = _lorentz_curve(1.7512345e9, 1.8123456e9)
    r = resonances(f, y)
    assert abs(r['fr_ghz'] - 1.7512345) < r['uncertainty_mhz'] * 1e-3
    assert abs(r['fa_ghz'] - 1.8123456) < r['uncertainty_mhz'] * 1e-3
    assert r['k2eff'] == pytest.approx(math.pi ** 2 / 4 * (1.8123456 - 1.7512345) / 1.8123456, rel=1e-2)
    assert not r['warnings']


def test_resonances_weak_coupling_on_capacitive_background():
    """k2 ~ 0.4 %: |Y| keeps rising with f (2 pi f C0), the resonance is a small wiggle."""
    f = np.linspace(2.0e9, 3.0e9, 401)
    fr, fa = 2.47310e9, 2.47685e9
    y = 2j * np.pi * f * 1e-12 * (fa ** 2 - f ** 2) / (fr ** 2 - f ** 2)
    r = resonances(f, y)
    assert abs(r['fr_ghz'] - fr * 1e-9) < 2.5e-3 and abs(r['fa_ghz'] - fa * 1e-9) < 2.5e-3
    assert not any(w.startswith('peak_at_band_edge') for w in r['warnings'])


def test_resonances_band_edge_warning():
    f, y = _lorentz_curve(1.55e9, 1.62e9)
    r = resonances(f, y)
    assert r['fr_ghz'] is None and any(w.startswith('peak_at_band_edge') for w in r['warnings'])


def test_resonances_missing_antiresonance():
    f, y = _lorentz_curve(1.9511e9, 2.2e9)
    r = resonances(f, y)
    assert r['fr_ghz'] is not None and r['fa_ghz'] is None
    assert any(w.startswith('antiresonance_not_found') for w in r['warnings'])


@pytest.mark.parametrize('model', MODELS)
def test_reference_fr_fa_agree(model):
    """fr/fa of the stored solver curve vs the independent reference curve, within 1 MHz."""
    _, z = load_case(model)
    d = compare(resonances(z['frequency_hz'], z['reference_magnitude']),
                resonances(z['frequency_hz'], z['sawsim_magnitude']))
    assert abs(d['fr_diff_mhz']) < 1.0 and abs(d['fa_diff_mhz']) < 1.0


def test_templates_and_schema():
    t = agent.list_templates()['templates']
    assert len(t) == 10 and any(r['model_id'] == 'sp_stack' for r in t)
    s = agent.describe_template('sp_tcsaw')
    assert s['ok'] and s['mode_extensions'] == [0] and 'pitch_um' in s['ranges'] and 'pitch_um' in s['fields']
    assert not agent.describe_template('nope')['ok']


def test_materials_listed():
    m = agent.list_materials()
    ids = {r['id'] for r in m['materials']}
    assert {'sp_baseline', 'linbo3_tc', 'al', 'cu', 'sio2'} <= ids and m['euler_convention']['id'] == 'zxz'


def test_validate_reports_allowed_values():
    ok = agent.validate({'model_id': 'sp_single_layer', 'pitch_um': 1.0})
    assert ok['ok'] and ok['config']['pitch_um'] == 1.0 and len(ok['config_hash']) == 12
    bad = agent.validate({'model_id': 'sp_tcsaw', 'mode_extension': 1})
    assert not bad['ok'] and bad['errors'] and bad['allowed']['mode_extensions'] == [0]
    unknown = agent.validate({'model_id': 'no_such'})
    assert not unknown['ok'] and 'sp_single_layer' in unknown['allowed']['model_id']


def test_run_summarize_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv('SAWSIM_RUNS_DIR', str(tmp_path))
    cfg = {'model_id': 'sp_single_layer', 'points': 21, 'start_ghz': 1.7, 'stop_ghz': 1.95}
    a = agent.run(cfg)
    assert a['ok'] and not a['cached'] and 1.78 < a['fr_ghz'] < 1.83 and a['fa_ghz'] > a['fr_ghz']
    assert a['k2eff'] > 0 and a['artifacts'] and a['next_steps']
    b = agent.run(cfg)
    assert b['cached'] and b['fr_ghz'] == a['fr_ghz'] and b['output_dir'] == a['output_dir']
    assert agent.summarize(a['output_dir'])['fr_ghz'] == a['fr_ghz']


def test_concurrent_identical_runs_share_cache(tmp_path):
    """Two processes asking for the same config must both succeed and end with one result dir."""
    env = dict(__import__('os').environ, SAWSIM_RUNS_DIR=str(tmp_path))
    cmd = [sys.executable, '-m', 'sawsim.cli', 'run', '{"model_id": "sp_single_layer", "points": 5}', '--json', '-q']
    procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
             for _ in range(2)]
    outs = [json.loads(p.communicate()[0]) for p in procs]
    assert all(o['ok'] for o in outs) and outs[0]['output_dir'] == outs[1]['output_dir']
    assert [p.name for p in tmp_path.iterdir()] == [Path(outs[0]['output_dir']).name]


def test_guide_install_codex_is_idempotent(tmp_path):
    target = tmp_path / 'AGENTS.md'
    target.write_text('# my rules\nkeep me\n', encoding='utf-8')
    for _ in range(2):
        p = subprocess.run([sys.executable, '-m', 'sawsim.cli', 'guide', '--install-codex', str(target)],
                           capture_output=True, text=True)
        assert p.returncode == 0
    text = target.read_text(encoding='utf-8')
    assert text.startswith('# my rules\nkeep me\n') and text.count('<!-- sawsim:begin -->') == 1
    assert 'sawsim guide' in text


def _cli(*args):
    p = subprocess.run([sys.executable, '-m', 'sawsim.cli', *args], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)


def test_cli_json_stdout_is_pure(tmp_path):
    rc, out = _cli('templates', '--json')
    assert rc == 0 and len(out['templates']) == 10
    rc, out = _cli('validate', '{"model_id": "sp_tcsaw", "mode_extension": 1}')
    assert rc == 1 and out['ok'] is False
    rc, out = _cli('run', '{"model_id": "sp_single_layer"}', '--set', 'points=5', '--mesh-only', '--json', '-q',
                   '-o', str(tmp_path / 'm'))
    assert rc == 0 and out['ok'] and out['dofs_estimate'] > 100


def test_load_curve_formats(tmp_path):
    f = np.linspace(1.6e9, 2.0e9, 11)
    y = 1j * f * 1e-9
    (tmp_path / 'mag.csv').write_text('f_hz,absY\n' + '\n'.join('%.12g,%.12g' % (a, abs(b)) for a, b in zip(f, y)))
    (tmp_path / 'cplx.csv').write_text('# GHz, Re, Im\n' + '\n'.join('%.12g,%.12g,%.12g' % (a * 1e-9, b.real, b.imag) for a, b in zip(f, y)))
    for name in ('mag.csv', 'cplx.csv'):
        ff, yy, _ = agent.load_curve(tmp_path / name)
        assert np.allclose(ff, f) and np.allclose(np.abs(yy), np.abs(y))
    ff, yy, label = agent.load_curve(Path(__file__).parent / 'data' / 'sp_tcsaw.npz')
    assert len(ff) == 201 and label.endswith('(reference)')


def test_plot_overlay_and_curve_json(tmp_path, monkeypatch):
    monkeypatch.setenv('SAWSIM_RUNS_DIR', str(tmp_path / 'runs'))
    base = {'model_id': 'sp_single_layer', 'points': 21, 'start_ghz': 1.7, 'stop_ghz': 1.95}
    a, b = agent.run(dict(base, metal_ratio=0.4)), agent.run(dict(base, metal_ratio=0.6))
    ref = Path(__file__).parent / 'data' / 'sp_single_layer.npz'
    out = agent.plot([a['output_dir'], b['output_dir'], str(ref)], tmp_path / 'fig.png')
    assert out['ok'] and (tmp_path / 'fig.png').stat().st_size > 10000
    assert [c['label'] for c in out['curves']] == ['metal_ratio=0.4', 'metal_ratio=0.6', 'sp_single_layer (reference)']
    assert all(c['fr_ghz'] for c in out['curves'])
    s = agent.summarize(a['output_dir'], with_curve=True)
    assert len(s['curve']['abs']) == 21 and s['curve']['frequency_ghz'][0] == 1.7
