import numpy as np
import pytest

from sawsim import Model, Result, __version__, sweep


def test_version():
    assert __version__.startswith('2.')


def test_templates_listed():
    t = Model.templates()
    assert len(t) == 9 and 'sp_single_layer' in t and 'sp_2p5d_quad_layer' in t


def test_model_defaults_and_repr():
    m = Model('sp_double_layer', points=7)
    assert m.config.points == 7 and m.config.layers and 'sp_double_layer' in repr(m)


def test_invalid_inputs_rejected():
    with pytest.raises(Exception):
        Model('no_such_model')
    with pytest.raises(Exception):
        Model('sp_single_layer', points=1)
    with pytest.raises(Exception):
        Model('sp_single_layer', mesh_um=0.0)


def test_hct_not_in_package(tmp_path):
    from sawsim.solver import run_simulation
    with pytest.raises(ValueError):
        run_simulation({'model_id': 'hct_tcsaw'}, str(tmp_path))


def test_mesh_only(tmp_path):
    r = sweep(Model('sp_single_layer', points=3), tmp_path / 'm', mesh_only=True)
    assert r.metadata.get('nodes', 0) > 100 and r.artifact('mesh.png').exists()


def test_sweep_result_and_save(tmp_path):
    r = sweep(Model('sp_single_layer', points=3), tmp_path / 's')
    assert len(r.frequency_ghz) == 3 and r.admittance.dtype == np.complex128
    assert r.peak_frequency_ghz is not None and r.artifact('Y11.png').exists()
    out = r.save(tmp_path / 'copy')
    assert (out / 'curve.json').exists()
    assert Result(out).magnitude.shape == (3,)
