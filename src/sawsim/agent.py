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
    'layers': 'extra layers [{material_id, thickness_um, euler_*_deg}]; count fixed by the template '
              '(sp_stack: 0-6). Order: backing layers top->bottom under the piezo layer '
              '(sp_tcsaw only: its two coatings, inner->outer). Layer materials must be non-piezoelectric',
    'coatings': 'sp_stack only: 0-3 layers over the electrodes, inner->outer; the first is measured from the '
                'piezo surface and embeds the electrodes (must be thicker than electrode_um)',
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
    'beta_dk': 'Rayleigh stiffness damping of the piezoelectric layer and its PML, K_uu -> K_uu(1 + i beta_dk w), '
               'in s (beta_dK of the reference FEM models; e.g. 1e-13 for TC-SAW, 3e-14 for IHP-SAW); 0 = lossless. 2D templates only',
    'eta_eps': 'dielectric loss factor of the piezoelectric material, eps -> eps(1 - i eta_eps) (eta_epsilonS of the reference models; '
               'e.g. 1.5e-3); other materials stay lossless. 2D templates only',
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

def _count(spec):
    """Layer count of a template: an int, or [min, max] for sp_stack."""
    return spec.get('layer_count_range') or spec['layer_count']


def list_templates() -> dict:
    from sawsim.sp_specs import MODEL_SPECS
    rows = []
    for k, s in MODEL_SPECS.items():
        d = s['defaults']
        rows.append(dict(model_id=k, name=s['name'], dimension='2.5D Hex27' if k.startswith('sp_2p5d_') else '2D Q9',
                         layer_count=_count(s), coating_count=s.get('coating_count_range', [0, 0]),
                         mode_extensions=s['supported_mode_extensions'],
                         default_substrate=d['substrate_material'], default_band_ghz=[d['start_ghz'], d['stop_ghz']]))
    return dict(templates=rows)


def describe_template(model_id: str) -> dict:
    from sawsim.sp_specs import MODEL_SPECS
    if model_id not in MODEL_SPECS:
        return dict(ok=False, error='unknown model_id', known=sorted(MODEL_SPECS))
    s = MODEL_SPECS[model_id]
    ranges = {f['key']: dict(min=f['min'], max=f['max'], step=f['step']) for f in s['numeric_fields']}
    return dict(ok=True, model_id=model_id, name=s['name'], defaults=deepcopy(s['defaults']),
                ranges=ranges, layer_count=_count(s), coating_count=s.get('coating_count_range', [0, 0]),
                layer_role=s['layer_role'],
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


def material_show(material_id: str) -> dict:
    from sawsim.material_library import get_record
    try:
        return dict(ok=True, record=get_record(material_id))
    except (KeyError, ValueError) as e:
        return dict(ok=False, error=str(e).strip("'"))


def material_symmetries() -> dict:
    from sawsim.crystal import SYMMETRIES
    return dict(ok=True, symmetries=SYMMETRIES,
                spec_example=dict(id='user_aln', name='AlN (literature)', symmetry='hexagonal_6mm',
                                  constants=dict(C11=345, C12=125, C13=120, C33=395, C44=118,
                                                 e15=-0.48, e31=-0.58, e33=1.55, eps11=9.21, eps33=10.12),
                                  rho_kg_m3=3260, roles=['substrate', 'layer'],
                                  source='<paper / database citation for every constant>'),
                note='ids must start with user_; records are immutable (bump version to change); '
                     'stored in $SAWSIM_MATERIALS_DIR (default ~/.sawsim/materials)')


def _import(record, dry_run):
    from pydantic import ValidationError
    from sawsim.material_library import import_record
    from sawsim.material_library.schema import MaterialRecord
    try:
        rec = MaterialRecord.model_validate(record).model_dump()
        if not dry_run:
            rec = import_record(rec)
    except ValidationError as e:
        return dict(ok=False, errors=[dict(field='.'.join(str(x) for x in err.get('loc', ())) or None,
                                           message=err.get('msg')) for err in e.errors()])
    except (ValueError, OSError) as e:  # FileExistsError is an OSError
        return dict(ok=False, error='%s: %s' % (type(e).__name__, e))
    return dict(ok=True, imported=not dry_run, id=rec['id'], version=rec['version'], roles=rec['roles'],
                symmetry=rec['symmetry'], rho_kg_m3=rec['rho_kg_m3'],
                usage='use "%s" as substrate_material / electrode_material / layer material_id (per roles)' % rec['id'])


def material_create(spec, *, dry_run: bool = False) -> dict:
    """Build a record from crystal-class constants (see material_symmetries) and import it."""
    from sawsim.crystal import build_record
    s = _load(spec)
    try:
        record = build_record(**s)
    except TypeError as e:
        return dict(ok=False, error='bad spec keys: %s' % e)
    except (ValueError, KeyError) as e:
        return dict(ok=False, error=str(e))
    return _import(record, dry_run)


def material_import(record, *, dry_run: bool = False) -> dict:
    """Import a complete record (C_pa/e_c_m2/eps_f_m in SI, same format as `material_show`)."""
    return _import(_load(record), dry_run)


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
                              coating_count=t['coating_count'],
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

def summarize(result_dir, *, with_curve: bool = False) -> dict:
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
    if not (inp.get('beta_dk') or inp.get('eta_eps')):
        # No material loss: resonances are (nearly) poles; a finite 3 dB width would be a sampling artefact.
        res['q_r'] = res['q_a'] = None
        res['notes'] = [n for n in res['notes'] if not n.startswith('Q not resolved')] + [
            'lossless model (beta_dk = eta_eps = 0): Q not reported; set beta_dk / eta_eps (e.g. 1e-13 / 1.5e-3) '
            'and use locate for a physical Q']
    units = meta.get('units', {})
    config = {k: inp.get(k) for k in ('model_id', 'mode_extension', 'substrate_material', 'electrode_material',
                                      'pitch_um', 'metal_ratio', 'electrode_um', 'substrate_um', 'mesh_um',
                                      'start_ghz', 'stop_ghz', 'points', 'aperture_um', 'beta_dk', 'eta_eps')}
    config['layers'] = [(l['material_id'], l['thickness_um']) for l in inp.get('layers', [])]
    if inp.get('coatings'):
        config['coatings'] = [(l['material_id'], l['thickness_um']) for l in inp['coatings']]
    return dict(ok=True, output_dir=str(d), config=config, **res,
                admittance_unit=units.get('admittance', 'S/m'),
                max_abs_y=float(np.max(np.abs(y))), dofs=meta.get('dofs'), elements=meta.get('elements'),
                elapsed_s=meta.get('elapsed_seconds'),
                artifacts={k: str(d / k) for k in ('Y11.png', 'mesh.png', 'disp_field.png', 'phi_field.png',
                                                   'admittance.csv', 'curve.json') if (d / k).exists()},
                next_steps=_next_steps(res, config),
                **(dict(curve=curve_data(d)) if with_curve else {}))


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


def _band_limits(model_id):
    from sawsim.sp_specs import MODEL_SPECS
    lim = {fl['key']: (fl['min'], fl['max']) for fl in MODEL_SPECS[model_id]['numeric_fields']}
    return lim['start_ghz'][0], lim['stop_ghz'][1]


def quality(config, f_ghz: float, kind: str = 'r', width_ghz: Optional[float] = None, *, points: int = 61,
            final_points: int = 121, max_sweeps: int = 6, on_progress=None) -> dict:
    """Q at the resonance (kind 'r': peak of |Y|^2) or antiresonance ('a': peak of |Z|^2 = 1/|Y|^2) near f_ghz.

    Coarse windows (+/-3 linewidths) re-centre and size the line until it spans >= 8 samples; a final window of
    +/-1.5 linewidths (~40 samples per linewidth) gives Q = f_peak / (3 dB width) with the half-power
    interpolation bias removed by Richardson extrapolation (metrics.peak_quality_extrapolated).
    """
    from sawsim.metrics import peak_quality, peak_quality_extrapolated
    c = _load(config)
    f_lo, f_hi = _band_limits(c.get('model_id', 'sp_single_layer'))
    f0, width = float(f_ghz), float(width_ghz or f_ghz * 2e-3)
    history = []

    def window(half, n, extrapolate=False):
        lo, hi = max(f_lo, f0 - half), min(f_hi, f0 + half)
        s = run(_with(c, start_ghz=round(lo, 7), stop_ghz=round(hi, 7), points=int(n)), on_progress=on_progress)
        if not s.get('ok'):
            return s, None
        f, y, _ = load_curve(s['output_dir'])
        mag2 = np.abs(y) ** 2
        power = mag2 if kind == 'r' else 1.0 / np.maximum(mag2, 1e-300)
        pq = (peak_quality_extrapolated if extrapolate else peak_quality)(f, power)
        history.append(dict(window_ghz=[round(lo, 7), round(hi, 7)], points=int(n),
                            q=pq and round(pq['q'], 3), samples_in_linewidth=pq and pq['samples_in_linewidth'],
                            output_dir=s['output_dir']))
        return s, pq

    for _ in range(max_sweeps):
        s, pq = window(3 * width, points)
        if not s.get('ok'):
            return dict(ok=False, error=s.get('error') or s.get('errors'), history=history)
        if pq is None:                       # half-power point outside the window: widen
            width *= 3
            continue
        f0, width = pq['f0_hz'] * 1e-9, (pq['fh_hz'] - pq['fl_hz']) * 1e-9
        if f0 / width > 1e6:
            return dict(ok=True, q=None, f_ghz=f0, converged=False, history=history,
                        note='Q > 1e6: no resolvable loss (lossless model or radiation-limited only)')
        if pq['samples_in_linewidth'] >= 8:
            break
    else:
        return dict(ok=True, q=None, f_ghz=f0, converged=False, history=history,
                    note='linewidth not resolved within %d windows' % max_sweeps)
    s, pq = window(1.5 * width, final_points, extrapolate=True)
    if not s.get('ok') or pq is None:
        return dict(ok=bool(s.get('ok')), q=None, f_ghz=f0, converged=False, history=history,
                    note='final window failed', error=s.get('error'))
    spread = abs(pq['q_linear'] - pq['q_half']) / pq['q'] if pq.get('q_half') else None
    return dict(ok=True, q=pq['q'], f_ghz=pq['f0_hz'] * 1e-9, linewidth_mhz=(pq['fh_hz'] - pq['fl_hz']) * 1e-6,
                samples_in_linewidth=pq['samples_in_linewidth'], q_linear=pq['q_linear'], q_half=pq.get('q_half'),
                converged=spread is not None and spread < 0.01, history=history)


def _add_quality(result, config, on_progress):
    """Refine fr/fa and add q_r/q_a to a located result (lossy configs)."""
    width = (result['fa_ghz'] - result['fr_ghz']) * 0.03
    qr = quality(config, result['fr_ghz'], 'r', width, on_progress=on_progress)
    qa = quality(config, result['fa_ghz'], 'a', width, on_progress=on_progress)
    for key, q in (('r', qr), ('a', qa)):
        if q.get('ok') and q.get('q'):
            result['q_' + key] = round(q['q'], 2)
            result['f%s_ghz' % key] = round(q['f_ghz'], 7)
    if result.get('fr_ghz') and result.get('fa_ghz'):
        import math
        result['k2eff'] = round(math.pi ** 2 / 4 * (result['fa_ghz'] - result['fr_ghz']) / result['fa_ghz'], 6)
    result['notes'] = [n for n in result.get('notes', []) if not n.startswith('Q not resolved')]
    result['quality'] = dict(method='Q = f_peak / 3 dB width of |Y|^2 (fr) and |Z|^2 (fa); final window +/-1.5 '
                                    'linewidths with ~40 samples per linewidth, interpolation bias removed by '
                                    'Richardson extrapolation; fr/fa are the refined peaks',
                             resonance=qr, antiresonance=qa)
    return result


def locate(config, *, zoom_points: int = 101, with_q: Optional[bool] = None, on_progress=None) -> dict:
    """Coarse sweep -> find fr/fa (widening the band if needed) -> zoomed sweep around them.

    with_q (default: when beta_dk or eta_eps > 0) adds q_r/q_a from resolved windows around fr and fa.
    """
    from sawsim.sp_specs import MODEL_SPECS
    c = _load(config)
    spec = MODEL_SPECS.get(c.get('model_id', 'sp_single_layer'))
    if spec is None:
        return validate(c)
    lim = {fl['key']: (fl['min'], fl['max']) for fl in spec['numeric_fields']}
    f_lo, f_hi = lim['start_ghz'][0], lim['stop_ghz'][1]
    history = []
    s = None
    for _ in range(6):
        s = run(c, on_progress=on_progress)
        if not s.get('ok'):
            return s
        start, stop = s['config']['start_ghz'], s['config']['stop_ghz']
        history.append(dict(band_ghz=[start, stop], fr_ghz=s['fr_ghz'], fa_ghz=s['fa_ghz'],
                            output_dir=s['output_dir']))
        w = ' '.join(s['warnings'])
        span = stop - start
        at_limits = start <= f_lo and stop >= f_hi
        if 'no_resonance_found' in w or ('peak_at_band_edge' in w and at_limits):
            points = s['config']['points']
            if points >= 401:
                break
            c = _with(c, points=min(401, 2 * points + 1))  # weak coupling: sample the fr..fa gap
            continue
        if 'peak_at_band_edge' in w:
            curve = json.loads((Path(s['output_dir']) / 'curve.json').read_text(encoding='utf-8'))
            g = np.asarray(curve['magnitude']) / np.asarray(curve['frequency_ghz'])
            at_low = int(np.argmax(g)) == 0
            c = _with(c, start_ghz=round(max(f_lo, start - span / 2), 4) if at_low else start,
                      stop_ghz=round(min(f_hi, stop + span / 2), 4) if not at_low else stop)
            continue
        if 'antiresonance_not_found' in w and stop < f_hi:
            c = _with(c, stop_ghz=round(min(f_hi, stop + span / 2), 4))
            continue
        break
    if s.get('fr_ghz') is None or s.get('fa_ghz') is None:
        return dict(ok=False, error='could not bracket fr and fa within the template band %s..%s GHz' % (f_lo, f_hi),
                    history=history, last=s)
    coarse = dict(output_dir=s['output_dir'], fr_ghz=s['fr_ghz'], fa_ghz=s['fa_ghz'],
                  band_ghz=[s['config']['start_ghz'], s['config']['stop_ghz']],
                  note='full-band sweep; the top-level result is the zoom around fr..fa. '
                       'Plot both with: sawsim plot <coarse output_dir> <output_dir> -o fig.png')
    z = s
    for _ in range(3):  # zoom; repeat if the fr..fa gap is still under-sampled
        fr, fa = z['fr_ghz'], z['fa_ghz']
        half = max(fa - fr, 2e-3 * z['frequency_step_mhz'])
        zoom = _with(c, start_ghz=round(max(f_lo, fr - half), 6), stop_ghz=round(min(f_hi, fa + half), 6),
                     points=int(zoom_points))
        nz = run(zoom, on_progress=on_progress)
        if not nz.get('ok') or nz.get('fr_ghz') is None or nz.get('fa_ghz') is None:
            break
        z = nz
        history.append(dict(band_ghz=[zoom['start_ghz'], zoom['stop_ghz']], fr_ghz=z['fr_ghz'],
                            fa_ghz=z['fa_ghz'], output_dir=z['output_dir']))
        if not any(x.startswith('coarse_sampling') for x in z['warnings']):
            break
    if z is s:
        return dict(ok=False, error='zoomed sweep lost the resonance; inspect the coarse result', coarse=coarse,
                    history=history, last=nz)
    z['coarse'] = coarse
    z['history'] = history
    if with_q is None:
        with_q = bool(c.get('beta_dk') or c.get('eta_eps'))
    if with_q:
        z = _add_quality(z, c, on_progress)
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
    if base.get('quality'):
        fine = _add_quality(fine, _with(c, mesh_um=fine_mesh), on_progress)
    d = compare(base, fine)
    for key in ('q_r', 'q_a'):
        if base.get(key) and fine.get(key):
            d[key + '_rel_change'] = round((fine[key] - base[key]) / base[key], 5)
    step = base['frequency_step_mhz']
    shift = max(abs(d['fr_diff_mhz'] or 0), abs(d['fa_diff_mhz'] or 0))
    return dict(ok=True, mesh_um=[mesh, fine_mesh],
                coarse=dict(fr_ghz=base['fr_ghz'], fa_ghz=base['fa_ghz'], k2eff=base['k2eff'], dofs=base['dofs'],
                            q_r=base.get('q_r'), q_a=base.get('q_a'), output_dir=base['output_dir']),
                fine=dict(fr_ghz=fine['fr_ghz'], fa_ghz=fine['fa_ghz'], k2eff=fine['k2eff'], dofs=fine['dofs'],
                          q_r=fine.get('q_r'), q_a=fine.get('q_a'), output_dir=fine['output_dir']),
                shift=d, frequency_step_mhz=step, uncertainty_mhz=base['uncertainty_mhz'],
                note=('fr/fa moved %.3f MHz on mesh refinement (sampling uncertainty +/-%.3f MHz). '
                      'Judge convergence against your tolerance; the finer result is the better estimate.'
                      % (shift, step / 2)))


def load_curve(path):
    """(frequency_hz, Y or |Y|, label) from a result directory, admittance/reference CSV or npz.

    CSV: 2 columns f,|Y| or 3+ columns f,Re,Im[,...] (header lines are skipped); frequencies
    below 1e6 are taken as GHz.
    """
    p = Path(path)
    if p.is_dir():
        c = json.loads((p / 'curve.json').read_text(encoding='utf-8'))
        f = np.asarray(c['frequency_ghz']) * 1e9
        return f, np.asarray(c['real']) + 1j * np.asarray(c['imag']), p.name
    if p.suffix == '.npz':
        z = np.load(p)
        f = z['frequency_hz']
        if 'reference_magnitude' in z:
            return np.asarray(z['frequency_hz'], dtype=float), np.asarray(z['reference_magnitude']), p.stem + ' (reference)'
        y = z['admittance']
    else:
        rows = []
        for line in p.read_text(encoding='utf-8').splitlines():
            try:
                rows.append([float(x) for x in line.replace(';', ',').split(',') if x.strip()])
            except ValueError:
                continue  # header / comment
        rows = [r for r in rows if len(r) >= 2]
        if not rows:
            raise ValueError('no numeric rows with at least 2 columns in ' + str(p))
        width = min(len(r) for r in rows)
        a = np.asarray([r[:width] for r in rows])
        f = a[:, 0]
        y = a[:, 1] + 1j * a[:, 2] if a.shape[1] >= 3 else a[:, 1]
    f = np.asarray(f, dtype=float)
    if f.max() < 1e6:
        f = f * 1e9
    return f, np.asarray(y), p.stem


def curve_data(result_dir) -> dict:
    """The sampled admittance of a result as JSON arrays (GHz, S/m)."""
    f, y, _ = load_curve(result_dir)
    r6 = lambda a: [float('%.6g' % v) for v in a]
    return dict(frequency_ghz=[round(v, 7) for v in (f * 1e-9).tolist()], real=r6(np.real(y)), imag=r6(np.imag(y)),
                abs=r6(np.abs(y)))


def compare_curve(result_dir, reference) -> dict:
    """fr/fa/k2 of a run vs a reference |Y| curve (npz, or CSV f,|Y| / f,Re,Im)."""
    s = summarize(result_dir)
    if not s.get('ok'):
        return s
    f, y, _ = load_curve(reference)
    ref = resonances(f, y)
    return dict(ok=True, run=dict(fr_ghz=s['fr_ghz'], fa_ghz=s['fa_ghz'], k2eff=s['k2eff']),
                reference=dict(fr_ghz=ref['fr_ghz'], fa_ghz=ref['fa_ghz'], k2eff=ref['k2eff'],
                               frequency_step_mhz=ref['frequency_step_mhz']),
                deviation=compare(ref, s))


_LABEL_KEYS = ('model_id', 'pitch_um', 'metal_ratio', 'electrode_um', 'substrate_um', 'mesh_um', 'mode_extension',
               'substrate_material', 'electrode_material', 'euler_theta_deg')


def _auto_labels(paths):
    """Label result dirs by the config fields that differ between them."""
    inputs = []
    for p in paths:
        f = Path(p) / 'input.json'
        inputs.append(json.loads(f.read_text(encoding='utf-8')) if Path(p).is_dir() and f.exists() else None)
    runs = [i for i in inputs if i]
    keys = [k for k in _LABEL_KEYS if len({json.dumps(i.get(k)) for i in runs}) > 1]
    for k in ('layers', 'coatings'):
        if len({json.dumps([(l['material_id'], l['thickness_um']) for l in i.get(k, [])]) for i in runs}) > 1:
            keys.append(k)
    if not keys and len(runs) > 1 and len({(i['start_ghz'], i['stop_ghz'], i['points']) for i in runs}) > 1:
        keys = ['band']
    labels = []
    for p, i in zip(paths, inputs):
        if not i:
            labels.append(load_curve(p)[2] if Path(p).suffix == '.npz' else Path(p).stem)
        elif not keys:
            labels.append(i.get('model_id', Path(p).name))
        else:
            parts = []
            for k in keys:
                if k == 'band':
                    parts.append('%g-%g GHz, %d pts' % (i['start_ghz'], i['stop_ghz'], i['points']))
                elif k in ('layers', 'coatings'):
                    parts.append('%s=%s' % (k, '/'.join('%s %g' % (l['material_id'], l['thickness_um']) for l in i[k])))
                else:
                    parts.append('%s=%s' % (k, i.get(k)))
            labels.append(', '.join(parts))
    return labels


def plot(inputs, output, *, labels=None, quantity: str = 'abs', mark: bool = True) -> dict:
    """Overlay admittance curves (result dirs and/or reference files) in one figure, fr/fa marked.

    quantity: 'abs' (|Y|, log axis), 'db' (20 log10 |Y|), 'real', 'imag'. The output format
    follows the file extension (.png, .svg, .pdf).
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if quantity not in ('abs', 'db', 'real', 'imag'):
        return dict(ok=False, error='quantity must be one of abs, db, real, imag')
    paths = [str(x) for x in inputs]
    names = list(labels) if labels else _auto_labels(paths)
    if len(names) != len(paths):
        return dict(ok=False, error='need one label per input')
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
    rows = []
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
    for n, (path, name) in enumerate(zip(paths, names)):
        color = colors[n % len(colors)]
        try:
            f, y, _ = load_curve(path)
        except Exception as e:
            plt.close(fig)
            return dict(ok=False, error='cannot read %s: %s' % (path, e))
        g = f * 1e-9
        v = {'abs': np.abs(y), 'db': 20 * np.log10(np.maximum(np.abs(y), 1e-300)),
             'real': np.real(y), 'imag': np.imag(y)}[quantity]
        ax.plot(g, v, color=color, lw=1.4, label=name)
        r = resonances(f, y)
        rows.append(dict(input=path, label=name, fr_ghz=r['fr_ghz'], fa_ghz=r['fa_ghz'], k2eff=r['k2eff'],
                         band_ghz=[round(float(g.min()), 6), round(float(g.max()), 6)], points=len(g)))
        if mark:
            for key, ls in (('fr_ghz', '--'), ('fa_ghz', ':')):
                if r[key]:
                    ax.axvline(r[key], color=color, ls=ls, lw=.9, alpha=.8)
    if quantity == 'abs':
        ax.set_yscale('log')
    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel({'abs': '|Y| (S/m)', 'db': '20 log10 |Y| (dB S/m)', 'real': 'Re Y (S/m)',
                   'imag': 'Im Y (S/m)'}[quantity])
    ax.grid(True, which='both', alpha=.25)
    ax.legend(fontsize=8, loc='best')
    if mark:
        ax.set_title('dashed: fr   dotted: fa', fontsize=8, loc='right', color='0.4')
    fig.tight_layout()
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return dict(ok=True, output=str(out.resolve()), quantity=quantity, curves=rows)
