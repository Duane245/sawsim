"""JSON-in / JSON-out operations for AI agents (used by `sawsim ... --json`).

Every public function takes plain dicts/strings and returns a JSON-serialisable dict,
so an agent can drive the whole workflow from a shell without reading Python.
Runs are cached by config hash under $SAWSIM_RUNS_DIR (default ./sawsim_runs).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from sawsim.metrics import compare, resonances

FIELD_DOCS = {
    'model_id': 'template id (see `sawsim templates`); fixes geometry family and layer count',
    'mode_extension': '0 = in-plane (ux, uy) Rayleigh-type; 1 = adds out-of-plane uz (SH/leaky). '
                      'sp_tcsaw supports only 0; 2.5D templates only 1',
    'substrate_material': 'piezoelectric substrate material id (see `sawsim materials`)',
    'electrode_material': 'electrode material id',
    'layers': 'extra layers [{material_id, thickness_um, euler_*_deg}]; count fixed by template. '
              'Order: backing layers top->bottom under the substrate, or coatings inner->outer for sp_tcsaw',
    'euler_phi_deg': 'intrinsic ZXZ Euler alpha applied to the substrate tensor, deg',
    'euler_theta_deg': 'intrinsic ZXZ Euler beta, deg',
    'euler_psi_deg': 'intrinsic ZXZ Euler gamma, deg',
    'aperture_um': 'slab width of 2.5D Hex27 templates only, um (must be null for 2D)',
    'pitch_um': 'electrode period p, um; resonance frequency scales roughly as 1/p',
    'electrode_um': 'electrode thickness, um',
    'substrate_um': 'thickness of the main piezoelectric layer, um',
    'metal_ratio': 'electrode width / pitch',
    'mesh_um': 'target element size, um; halve it to check mesh convergence',
    'start_ghz': 'sweep start frequency, GHz',
    'stop_ghz': 'sweep stop frequency, GHz',
    'points': 'number of frequency points (3..1201); cost is linear in points',
    'voltage': 'drive voltage, V (admittance is independent of it)',
}


def _runs_dir() -> Path:
    return Path(os.environ.get('SAWSIM_RUNS_DIR', 'sawsim_runs'))


def _load(config):
    if isinstance(config, (str, Path)):
        return json.loads(Path(config).read_text(encoding='utf-8'))
    return deepcopy(dict(config))


def _validated(config):
    from sawsim.config import SimulationConfig
    return SimulationConfig.model_validate(_load(config))


def config_hash(cfg) -> str:
    text = json.dumps(cfg.model_dump(), sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:12]


# ---------------------------------------------------------------- discovery

def list_templates() -> dict:
    from sawsim.sp_specs import MODEL_SPECS
    rows = []
    for k, s in MODEL_SPECS.items():
        d = s['defaults']
        rows.append(dict(model_id=k, name=s['name'], dimension='2.5D Hex27' if k.startswith('sp_2p5d_') else '2D Q9',
                         layer_count=s['layer_count'], mode_extensions=s['supported_mode_extensions'],
                         default_substrate=d['substrate_material'], default_band_ghz=[d['start_ghz'], d['stop_ghz']]))
    return dict(templates=rows)


def describe_template(model_id: str) -> dict:
    from sawsim.sp_specs import MODEL_SPECS
    if model_id not in MODEL_SPECS:
        return dict(ok=False, error='unknown model_id', known=sorted(MODEL_SPECS))
    s = MODEL_SPECS[model_id]
    ranges = {f['key']: dict(min=f['min'], max=f['max'], step=f['step']) for f in s['numeric_fields']}
    return dict(ok=True, model_id=model_id, name=s['name'], defaults=deepcopy(s['defaults']),
                ranges=ranges, layer_count=s['layer_count'], layer_role=s['layer_role'],
                layer_thickness_um=[s['layer_thickness_min_um'], s['layer_thickness_max_um']],
                mode_extensions=s['supported_mode_extensions'], notes=s['notes'], fields=FIELD_DOCS)


def list_materials() -> dict:
    from sawsim.material_catalog import EULER_CONVENTION, get_material_catalog
    cat = get_material_catalog()
    seen, rows = set(), []
    for group in ('substrates', 'electrodes', 'layers'):
        for r in cat[group]:
            if r['id'] in seen:
                continue
            seen.add(r['id'])
            rows.append(dict(id=r['id'], name=r['name'], roles=r['roles'], status=r.get('status'),
                             rho_kg_m3=r.get('rho_kg_m3'), description=r.get('description'),
                             reference_frame=r.get('reference_frame'), source=r.get('source')))
    return dict(materials=rows, euler_convention=dict(id=EULER_CONVENTION['id'],
                                                      description=EULER_CONVENTION['description'],
                                                      formula=EULER_CONVENTION['formula']))


def _invalid(config, errors):
    """Validation failure plus the template's allowed values, so an agent can fix everything in one pass."""
    out = dict(ok=False, errors=errors)
    try:
        mid = _load(config).get('model_id', 'sp_single_layer')
    except Exception:
        return out
    t = describe_template(mid) if isinstance(mid, str) else dict(ok=False)
    if t.get('ok'):
        out['allowed'] = dict(mode_extensions=t['mode_extensions'], layer_count=t['layer_count'],
                              layer_thickness_um=t['layer_thickness_um'], ranges=t['ranges'],
                              aperture_um='required' if mid.startswith('sp_2p5d_') else 'must be null')
    else:
        out['allowed'] = dict(model_id=t.get('known'))
    return out


def validate(config) -> dict:
    from pydantic import ValidationError
    try:
        cfg = _validated(config)
    except ValidationError as e:
        errs = [dict(field='.'.join(str(x) for x in err.get('loc', ())) or None,
                     message=err.get('msg'), input=err.get('input') if not isinstance(err.get('input'), dict) else None)
                for err in e.errors()]
        return _invalid(config, json.loads(json.dumps(errs, default=str)))
    except (ValueError, OSError) as e:
        return _invalid(config, [dict(field=None, message=str(e))])
    c = cfg.model_dump()
    c.pop('material_snapshots', None)
    return dict(ok=True, config=c, config_hash=config_hash(cfg))


# ---------------------------------------------------------------- running

def summarize(result_dir) -> dict:
    d = Path(result_dir)
    def load(name):
        p = d / name
        return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    curve, meta, inp = load('curve.json'), load('metadata.json'), load('input.json')
    if not curve.get('frequency_ghz'):
        return dict(ok=False, output_dir=str(d), error='no curve.json in this directory (mesh-only or failed run)')
    f = np.asarray(curve['frequency_ghz']) * 1e9
    y = np.asarray(curve['real']) + 1j * np.asarray(curve['imag'])
    res = resonances(f, y)
    units = meta.get('units', {})
    config = {k: inp.get(k) for k in ('model_id', 'mode_extension', 'substrate_material', 'electrode_material',
                                      'pitch_um', 'metal_ratio', 'electrode_um', 'substrate_um', 'mesh_um',
                                      'start_ghz', 'stop_ghz', 'points', 'aperture_um')}
    config['layers'] = [(l['material_id'], l['thickness_um']) for l in inp.get('layers', [])]
    return dict(ok=True, output_dir=str(d), config=config, **res,
                admittance_unit=units.get('admittance', 'S/m'),
                max_abs_y=float(np.max(np.abs(y))), dofs=meta.get('dofs'), elements=meta.get('elements'),
                elapsed_s=meta.get('elapsed_seconds'),
                artifacts={k: str(d / k) for k in ('Y11.png', 'mesh.png', 'disp_field.png', 'phi_field.png',
                                                   'admittance.csv', 'curve.json') if (d / k).exists()},
                next_steps=_next_steps(res, config))


def _next_steps(res, config):
    steps = []
    w = ' '.join(res['warnings'])
    if 'peak_at_band_edge' in w:
        steps.append('widen the band (start_ghz/stop_ghz) and rerun, or call `sawsim locate`')
    elif 'antiresonance_not_found' in w:
        steps.append('increase stop_ghz so fa is inside the band')
    elif 'coarse_sampling' in w:
        steps.append('call `sawsim locate` (or zoom the band around fr..fa) for sub-MHz fr/fa')
    else:
        steps.append('for a converged answer run `sawsim converge` (halves mesh_um)')
    return steps


def run(config, output_dir=None, *, mesh_only=False, on_progress: Optional[Callable] = None) -> dict:
    """Validate, run (or reuse a cached identical run) and summarise."""
    v = validate(config)
    if not v['ok']:
        return v
    from sawsim.api import sweep
    cfg = _validated(config)
    h = config_hash(cfg)
    out = Path(output_dir) if output_dir else _runs_dir() / ('%s_%s%s' % (cfg.model_id, h, '_mesh' if mesh_only else ''))
    done = (out / 'metadata.json').exists() and (out / ('mesh.npz' if mesh_only else 'curve.json')).exists()
    if done:
        prev = json.loads((out / 'input.json').read_text(encoding='utf-8')) if (out / 'input.json').exists() else {}
        from sawsim.config import SimulationConfig
        try:
            same = config_hash(SimulationConfig.model_validate(prev)) == h
        except Exception:
            same = False
        if not same:
            return dict(ok=False, error='output_dir already holds a different run; choose another directory',
                        output_dir=str(out))
    t = time.time()
    if not done:
        if output_dir and out.exists() and any(out.iterdir()):
            return dict(ok=False, error='output_dir is not empty and holds no finished run; choose another directory',
                        output_dir=str(out))
        # Cached runs are computed in a private directory and renamed into place, so concurrent
        # agents asking for the same config never write into each other's files.
        work = out if output_dir else out.with_name('.tmp_%s_%d_%d' % (out.name, os.getpid(), time.time_ns()))
        try:
            sweep(cfg, work, mesh_only=mesh_only, on_progress=on_progress)
        except Exception as e:  # solver/mesher failure -> structured error
            if work != out:
                shutil.rmtree(work, ignore_errors=True)
            return dict(ok=False, error='%s: %s' % (type(e).__name__, e), output_dir=str(out))
        if work != out:
            if (out / 'metadata.json').exists():  # another process finished the same run first
                shutil.rmtree(work, ignore_errors=True)
                done = True
            else:
                if out.exists():
                    shutil.rmtree(out, ignore_errors=True)  # partial dir left by an interrupted run
                try:
                    os.replace(work, out)
                except OSError:  # lost a race with an identical run: keep theirs
                    shutil.rmtree(work, ignore_errors=True)
                    done = True
    if mesh_only:
        meta = json.loads((out / 'metadata.json').read_text(encoding='utf-8'))
        return dict(ok=True, cached=done, output_dir=str(out), config_hash=h,
                    nodes=meta.get('nodes'), elements=meta.get('elements'),
                    dofs_estimate=(meta['nodes'] * (meta.get('displacement_components', 2) + 1)
                                   if meta.get('nodes') else None),
                    mesh_png=str(out / 'mesh.png'))
    s = summarize(out)
    s.update(cached=done, config_hash=h, wall_s=round(time.time() - t, 2))
    return s


def _with(config, **changes):
    c = _load(config)
    c.update(changes)
    return c


def locate(config, *, zoom_points: int = 101, on_progress=None) -> dict:
    """Coarse sweep -> find fr/fa (widening the band if needed) -> zoomed sweep around them."""
    c = _load(config)
    history = []
    s = None
    for _ in range(4):
        s = run(c, on_progress=on_progress)
        if not s.get('ok'):
            return s
        start, stop = s['config']['start_ghz'], s['config']['stop_ghz']
        history.append(dict(band_ghz=[start, stop], fr_ghz=s['fr_ghz'], fa_ghz=s['fa_ghz'],
                            output_dir=s['output_dir']))
        w = ' '.join(s['warnings'])
        span = stop - start
        if 'peak_at_band_edge' in w:
            mag = json.loads((Path(s['output_dir']) / 'curve.json').read_text(encoding='utf-8'))['magnitude']
            at_low = int(np.argmax(mag)) == 0
            c = _with(c, start_ghz=round(max(0.5, start - span / 2), 4) if at_low else start,
                      stop_ghz=round(min(5.0, stop + span / 2), 4) if not at_low else stop)
            continue
        if 'antiresonance_not_found' in w:
            c = _with(c, stop_ghz=round(min(5.0, stop + span / 2), 4))
            continue
        break
    if s.get('fr_ghz') is None or s.get('fa_ghz') is None:
        return dict(ok=False, error='could not bracket fr and fa within 0.5..5 GHz', history=history, last=s)
    fr, fa = s['fr_ghz'], s['fa_ghz']
    gap = fa - fr
    zoom = _with(c, start_ghz=round(fr - gap, 6), stop_ghz=round(fa + gap, 6), points=int(zoom_points))
    z = run(zoom, on_progress=on_progress)
    if z.get('ok'):
        z['coarse'] = dict(output_dir=s['output_dir'], fr_ghz=fr, fa_ghz=fa)
        z['history'] = history
    return z


def scan(config, param: str, values, *, locate_each: bool = False, on_progress=None) -> dict:
    """Run one sweep per value of `param`; tabulate fr/fa/k2eff."""
    rows = []
    for val in values:
        c = _with(config, **{param: val})
        s = locate(c, on_progress=on_progress) if locate_each else run(c, on_progress=on_progress)
        rows.append(dict(value=val, ok=s.get('ok'), fr_ghz=s.get('fr_ghz'), fa_ghz=s.get('fa_ghz'),
                         k2eff=s.get('k2eff'), uncertainty_mhz=s.get('uncertainty_mhz'),
                         warnings=s.get('warnings', []), error=s.get('error'), output_dir=s.get('output_dir')))
    return dict(ok=all(r['ok'] for r in rows), param=param, rows=rows)


def converge(config, *, factor: float = 0.5, on_progress=None) -> dict:
    """Locate fr/fa at mesh_um and at factor*mesh_um on the same zoomed band; report the shift."""
    from sawsim.sp_specs import MODEL_SPECS
    c = _load(config)
    base = locate(c, on_progress=on_progress)
    if not base.get('ok'):
        return base
    mesh = base['config']['mesh_um']
    lo = {f['key']: f['min'] for f in MODEL_SPECS[base['config']['model_id']]['numeric_fields']}['mesh_um']
    fine_mesh = max(lo, round(mesh * factor, 6))
    if fine_mesh >= mesh:
        return dict(ok=False, error='mesh_um already at the template minimum %.3g um; cannot refine' % lo, base=base)
    band = dict(start_ghz=base['config']['start_ghz'], stop_ghz=base['config']['stop_ghz'], points=base['config']['points'])
    fine = run(_with(c, mesh_um=fine_mesh, **band), on_progress=on_progress)
    if not fine.get('ok'):
        return fine
    d = compare(base, fine)
    step = base['frequency_step_mhz']
    shift = max(abs(d['fr_diff_mhz'] or 0), abs(d['fa_diff_mhz'] or 0))
    return dict(ok=True, mesh_um=[mesh, fine_mesh],
                coarse=dict(fr_ghz=base['fr_ghz'], fa_ghz=base['fa_ghz'], k2eff=base['k2eff'], dofs=base['dofs'],
                            output_dir=base['output_dir']),
                fine=dict(fr_ghz=fine['fr_ghz'], fa_ghz=fine['fa_ghz'], k2eff=fine['k2eff'], dofs=fine['dofs'],
                          output_dir=fine['output_dir']),
                shift=d, frequency_step_mhz=step, uncertainty_mhz=base['uncertainty_mhz'],
                note=('fr/fa moved %.3f MHz on mesh refinement (sampling uncertainty +/-%.3f MHz). '
                      'Judge convergence against your tolerance; the finer result is the better estimate.'
                      % (shift, step / 2)))


def compare_curve(result_dir, reference_npz_or_csv) -> dict:
    """Compare a run with a reference |Y| curve (npz with frequency_hz + reference_magnitude, or CSV f_hz,|Y|)."""
    s = summarize(result_dir)
    if not s.get('ok'):
        return s
    p = Path(reference_npz_or_csv)
    if p.suffix == '.npz':
        z = np.load(p)
        f, m = z['frequency_hz'], z['reference_magnitude']
    else:
        a = np.loadtxt(p, delimiter=',', comments='#')
        f, m = a[:, 0], a[:, 1]
    ref = resonances(f, m)
    return dict(ok=True, run=dict(fr_ghz=s['fr_ghz'], fa_ghz=s['fa_ghz'], k2eff=s['k2eff']),
                reference=dict(fr_ghz=ref['fr_ghz'], fa_ghz=ref['fa_ghz'], k2eff=ref['k2eff'],
                               frequency_step_mhz=ref['frequency_step_mhz']),
                deviation=compare(ref, s))
