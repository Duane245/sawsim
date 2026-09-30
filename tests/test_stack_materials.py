"""Generic sp_stack template and custom-material creation."""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

from conftest import load_case
from sawsim import agent
from sawsim.crystal import EPS0, tensors
from sawsim.material_library import get_record
from sawsim.metrics import compare, resonances

QUAD = [{'material_id': 'sio2', 'thickness_um': 0.5}, {'material_id': 'polysi', 'thickness_um': 1.0},
        {'material_id': 'si_isotropic', 'thickness_um': 7.83}]


def test_stack_validation_rules():
    ok = agent.validate({'model_id': 'sp_stack', 'layers': QUAD * 2,
                         'coatings': [{'material_id': 'sio2', 'thickness_um': 0.3}]})
    assert ok['ok'], ok
    assert not agent.validate({'model_id': 'sp_stack', 'layers': QUAD * 2 + QUAD[:1]})['ok']       # 7 layers
    assert not agent.validate({'model_id': 'sp_stack', 'coatings': [{'material_id': 'sio2', 'thickness_um': 0.1}]})['ok']
    assert not agent.validate({'model_id': 'sp_quad_layer', 'layers': QUAD,
                               'coatings': [{'material_id': 'sio2', 'thickness_um': 0.3}]})['ok']
    assert not agent.validate({'model_id': 'sp_stack', 'layers': [{'material_id': 'sp_baseline', 'thickness_um': 1}]})['ok']
    assert not agent.validate({'model_id': 'sp_stack', 'substrate_material': 'linbo3_tc', 'mode_extension': 1})['ok']
    t = agent.describe_template('sp_stack')
    assert t['layer_count'] == [0, 6] and t['coating_count'] == [0, 3]


def test_stack_mesh_with_layers_and_coatings(tmp_path):
    out = agent.run({'model_id': 'sp_stack', 'substrate_um': 0.6, 'layers': QUAD,
                     'coatings': [{'material_id': 'sio2', 'thickness_um': 0.4}, {'material_id': 'sin', 'thickness_um': 0.05}]},
                    tmp_path / 'm', mesh_only=True)
    assert out['ok'] and out['nodes'] > 500


@pytest.mark.parametrize('model', ['sp_single_layer', 'sp_double_layer', 'sp_triple_layer', 'sp_quad_layer',
                                   'sp_tcsaw', 'sp_stack'])
def test_at_least_8_elements_per_wavelength_across(model, tmp_path):
    """Lateral resolution: >= 8 Q9 elements per wavelength (2 x pitch) even at the coarsest allowed mesh_um."""
    coarsest = agent.describe_template(model)['ranges']['mesh_um']['max']
    out = agent.run({'model_id': model, 'mesh_um': coarsest}, tmp_path / 'm', mesh_only=True)
    z = np.load(tmp_path / 'm' / 'mesh.npz')
    P, Q, T = z['position_m'], z['quads'], z['material_tags']
    y_surface = P[Q[T == 15].ravel(), 1].min()
    xs = np.unique(np.round(P[np.abs(P[:, 1] - y_surface) < 1e-12, 0], 15))
    assert out['ok'] and (len(xs) - 1) // 2 >= 8


def test_stack_matches_single_layer_reference(tmp_path, monkeypatch):
    """sp_stack with no layers = the sp_single_layer stack; fr/fa vs the independent reference within 1 MHz."""
    monkeypatch.setenv('SAWSIM_RUNS_DIR', str(tmp_path))
    meta, z = load_case('sp_single_layer')
    ref = resonances(z['frequency_hz'], z['reference_magnitude'])
    cfg = {k: v for k, v in meta['config'].items() if k != 'material_snapshots'}
    s = agent.locate(dict(cfg, model_id='sp_stack', points=41))
    d = compare(ref, s)
    assert s['ok'] and abs(d['fr_diff_mhz']) < 1 and abs(d['fa_diff_mhz']) < 1


def test_trigonal_builder_reproduces_literature_record():
    r = get_record('linbo3_bouchy_2022')
    C, e, eps = np.array(r['C_pa']), np.array(r['e_c_m2']), np.array(r['eps_f_m'])
    k = dict(C11=C[0, 0] / 1e9, C12=C[0, 1] / 1e9, C13=C[0, 2] / 1e9, C14=C[0, 3] / 1e9, C33=C[2, 2] / 1e9,
             C44=C[3, 3] / 1e9, e15=e[0, 4], e22=e[1, 1], e31=e[2, 0], e33=e[2, 2],
             eps11=eps[0, 0] / EPS0, eps33=eps[2, 2] / EPS0)
    C2, e2, eps2 = (np.array(x) for x in tensors('trigonal_3m', k))
    assert np.allclose(C2, C, rtol=0, atol=1e-3) and np.allclose(e2, e) and np.allclose(eps2, eps)


def test_isotropic_builder_matches_library_sio2():
    r = get_record('sio2')   # E = 70 GPa, nu = 0.17, eps_r = 4.2
    C, _, eps = tensors('isotropic', dict(E_gpa=70, nu=0.17, eps_r=4.2))
    assert np.allclose(C, r['C_pa'], rtol=1e-6) and np.allclose(eps, r['eps_f_m'], rtol=1e-3)


def _cli(args, env):
    p = subprocess.run([sys.executable, '-m', 'sawsim.cli', *args], capture_output=True, text=True, env=env)
    return p.returncode, json.loads(p.stdout)


def test_material_create_import_and_use(tmp_path):
    env = dict(os.environ, SAWSIM_MATERIALS_DIR=str(tmp_path / 'mats'))
    spec = dict(id='user_test_iso', name='test layer', symmetry='isotropic', constants=dict(E_gpa=100, nu=0.25, eps_r=5),
                rho_kg_m3=3000, roles=['layer'], source='unit test')
    rc, out = _cli(['materials', '--create', json.dumps(spec), '--dry-run'], env)
    assert rc == 0 and out['ok'] and not out['imported']
    rc, out = _cli(['materials', '--create', json.dumps(spec)], env)
    assert rc == 0 and out['imported'] and out['id'] == 'user_test_iso'
    rc, out = _cli(['materials', '--create', json.dumps(spec)], env)
    assert rc == 1 and 'exists' in out['error']
    rc, out = _cli(['validate', json.dumps({'model_id': 'sp_stack', 'layers': [{'material_id': 'user_test_iso',
                                                                                 'thickness_um': 2}]})], env)
    assert rc == 0 and out['ok']
    bad = dict(spec, id='user_bad', symmetry='hexagonal_6mm')
    rc, out = _cli(['materials', '--create', json.dumps(bad)], env)
    assert rc == 1 and 'missing constants' in out['error']
