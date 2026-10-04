"""Local MCP server for SawSim (stdio, newline-delimited JSON-RPC 2.0).

Started by an AI client as `sawsim mcp`; runs unit-cell simulations on this machine through
the same operations as the JSON CLI (sawsim.agent). No network access, no finite-length (HCT)
models. Dependency-free so it works on every Python the package supports.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import traceback
from copy import deepcopy
from pathlib import Path

PROTOCOL_VERSIONS = ('2025-06-18', '2025-03-26', '2024-11-05')

INSTRUCTIONS = """SawSim simulates one periodic IDT cell of a SAW resonator (piezoelectric FEM, lossless by default)
and returns the admittance Y(f) with resonance fr, antiresonance fa and k2eff. Finite-length devices (HCT) are
not part of SawSim.
Workflow: list_templates -> describe_template -> validate_config -> locate_resonance (fr/fa/k2eff) ->
check_convergence (mesh check) -> plot_curves to show curves. Call get_guide once for template choice,
material conventions (pre-rotated linbo3_tc: Euler 0; sp_tcsaw: mode_extension 0), custom materials and
pitfalls. Report fr/fa in GHz, k2eff in %, the uncertainty, the mesh check and any warnings, and say which
template defaults you kept."""


# ---------------------------------------------------------------- tool schemas

def _config_schema():
    from sawsim.agent import FIELD_DOCS
    from sawsim.config import SimulationConfig
    from sawsim.sp_specs import MODEL_SPECS
    s = deepcopy(SimulationConfig.model_json_schema())
    s['properties'].pop('material_snapshots', None)
    for key, doc in FIELD_DOCS.items():
        if key in s['properties']:
            s['properties'][key]['description'] = doc
    s['properties']['model_id']['enum'] = sorted(MODEL_SPECS)
    s['description'] = ('Simulation config. Only model_id is needed; every other field defaults to the template '
                        '(see describe_template). Lengths um, frequencies GHz, angles deg.')
    s.pop('title', None)
    return s


def _tools():
    from sawsim.sp_specs import MODEL_SPECS
    cfg = _config_schema()
    obj = lambda props, req=(): dict(type='object', properties=props, required=list(req))
    return [
        dict(name='get_guide', description='Full SawSim usage guide for agents: workflow, templates, output fields, '
             'warnings, material/orientation conventions, custom materials, pitfalls. Read once before modelling.',
             inputSchema=obj({})),
        dict(name='list_templates', description='Unit-cell templates (2D Q9, 2.5D Hex27, generic stack) with layer '
             'counts, supported mode_extension and default band.', inputSchema=obj({})),
        dict(name='describe_template', description='Defaults, allowed ranges and field meanings of one template.',
             inputSchema=obj({'model_id': dict(type='string', enum=sorted(MODEL_SPECS))}, ['model_id'])),
        dict(name='list_materials', description='Material library (ids, roles, reference frames) and the ZXZ Euler '
             'convention.', inputSchema=obj({})),
        dict(name='show_material', description='Full record (C, e, eps tensors) of one material.',
             inputSchema=obj({'material_id': dict(type='string')}, ['material_id'])),
        dict(name='create_material', description='Build a material from crystal-class constants (isotropic: E_gpa, nu, '
             'eps_r; cubic: C11 C12 C44 eps_r; hexagonal_6mm: C11 C12 C13 C33 C44 e15 e31 e33 eps11 eps33; '
             'trigonal_3m: + C14 e22; GPa, C/m^2, relative permittivity) and import it. id must start with user_; '
             'cite the source of every constant. Only substrates may be piezoelectric.',
             inputSchema=obj({'spec': dict(type='object', properties=dict(
                 id=dict(type='string'), name=dict(type='string'),
                 symmetry=dict(type='string', enum=['isotropic', 'cubic', 'hexagonal_6mm', 'trigonal_3m']),
                 constants=dict(type='object'), rho_kg_m3=dict(type='number'),
                 roles=dict(type='array', items=dict(type='string', enum=['substrate', 'electrode', 'layer'])),
                 source=dict(type='string'), description=dict(type='string'), version=dict(type='string')),
                 required=['id', 'name', 'symmetry', 'constants', 'rho_kg_m3', 'roles', 'source']),
                 'dry_run': dict(type='boolean', description='validate only, do not save')}, ['spec'])),
        dict(name='validate_config', description='Check a config without running; on failure returns the errors and '
             "the template's allowed values.", inputSchema=obj({'config': cfg}, ['config'])),
        dict(name='run_sweep', description='Run one frequency sweep exactly as configured (cached by config hash) and '
             'return fr, fa, k2eff, warnings, next_steps and artifact paths. Prefer locate_resonance for fr/fa.',
             inputSchema=obj({'config': cfg, 'mesh_only': dict(type='boolean')}, ['config'])),
        dict(name='locate_resonance', description='Coarse sweep, widen the band if needed, then zoom around fr..fa '
             'until resolved. Use this for any fr / fa / k2eff answer. The result is the zoomed sweep; '
             'coarse.output_dir holds the full-band sweep.',
             inputSchema=obj({'config': cfg, 'zoom_points': dict(type='integer', minimum=21, maximum=401),
                              'with_q': dict(type='boolean', description='resolve Q_r/Q_a (default: when beta_dk or '
                                             'eta_eps > 0)')}, ['config'])),
        dict(name='check_convergence', description='Repeat locate with a finer mesh (mesh_um x factor, clamped to the '
             'template minimum) and report the fr/fa shift in MHz and ppm.',
             inputSchema=obj({'config': cfg, 'factor': dict(type='number', exclusiveMinimum=0, maximum=0.95)}, ['config'])),
        dict(name='scan_parameter', description='One sweep per value of a config field; table of fr/fa/k2eff. '
             'locate_each=true gives precise fr/fa per value (slower).',
             inputSchema=obj({'config': cfg, 'param': dict(type='string'), 'values': dict(type='array'),
                              'locate_each': dict(type='boolean')}, ['config', 'param', 'values'])),
        dict(name='summarize_result', description='Metrics of an existing result directory; with_curve adds the '
             'sampled admittance arrays (GHz, Re, Im, |Y| in S/m).',
             inputSchema=obj({'result_dir': dict(type='string'), 'with_curve': dict(type='boolean')}, ['result_dir'])),
        dict(name='plot_curves', description='Overlay admittance curves of result directories and/or reference files '
             '(CSV f,|Y| or f,Re,Im; npz) in one figure with fr (dashed) and fa (dotted). Returns the image.',
             inputSchema=obj({'inputs': dict(type='array', items=dict(type='string'), minItems=1),
                              'output': dict(type='string', description='figure path (.png/.svg/.pdf); default '
                                             '~/.sawsim/plots/plot_<time>.png'),
                              'labels': dict(type='array', items=dict(type='string')),
                              'quantity': dict(type='string', enum=['abs', 'db', 'real', 'imag'])}, ['inputs'])),
        dict(name='compare_with_reference', description='fr/fa/k2eff deviation of a result from a reference curve '
             '(CSV f,|Y| or f,Re,Im; npz).',
             inputSchema=obj({'result_dir': dict(type='string'), 'reference': dict(type='string')},
                             ['result_dir', 'reference'])),
    ]


def _guide():
    return dict(ok=True, guide=(Path(__file__).with_name('skill') / 'SKILL.md').read_text(encoding='utf-8'))


def _call(name, a, progress):
    from sawsim import agent
    if name == 'get_guide':
        return _guide()
    if name == 'list_templates':
        return agent.list_templates()
    if name == 'describe_template':
        return agent.describe_template(a['model_id'])
    if name == 'list_materials':
        return agent.list_materials()
    if name == 'show_material':
        return agent.material_show(a['material_id'])
    if name == 'create_material':
        return agent.material_create(a['spec'], dry_run=bool(a.get('dry_run')))
    if name == 'validate_config':
        return agent.validate(a['config'])
    if name == 'run_sweep':
        return agent.run(a['config'], mesh_only=bool(a.get('mesh_only')), on_progress=progress)
    if name == 'locate_resonance':
        return agent.locate(a['config'], zoom_points=int(a.get('zoom_points', 101)), with_q=a.get('with_q'),
                            on_progress=progress)
    if name == 'check_convergence':
        return agent.converge(a['config'], factor=float(a.get('factor', 0.5)), on_progress=progress)
    if name == 'scan_parameter':
        return agent.scan(a['config'], a['param'], a['values'], locate_each=bool(a.get('locate_each')),
                          on_progress=progress)
    if name == 'summarize_result':
        return agent.summarize(a['result_dir'], with_curve=bool(a.get('with_curve')))
    if name == 'plot_curves':
        out = a.get('output') or str(Path.home() / '.sawsim' / 'plots' / ('plot_%d.png' % int(time.time() * 1000)))
        return agent.plot(a['inputs'], out, labels=a.get('labels'), quantity=a.get('quantity', 'abs'))
    if name == 'compare_with_reference':
        return agent.compare_curve(a['result_dir'], a['reference'])
    raise KeyError(name)


# ---------------------------------------------------------------- JSON-RPC loop

class Server:
    def __init__(self, out):
        self.out = out
        self.tools = None

    def send(self, msg):
        self.out.write(json.dumps(msg, ensure_ascii=False, default=str) + '\n')
        self.out.flush()

    def reply(self, mid, result=None, error=None):
        msg = dict(jsonrpc='2.0', id=mid)
        if error is not None:
            msg['error'] = error
        else:
            msg['result'] = result
        self.send(msg)

    def handle(self, msg):
        if not isinstance(msg, dict) or msg.get('jsonrpc') != '2.0' or 'method' not in msg:
            if isinstance(msg, dict) and 'id' in msg and 'method' not in msg:
                return  # a response to a server request; we send none
            return self.reply(msg.get('id') if isinstance(msg, dict) else None,
                              error=dict(code=-32600, message='invalid request'))
        method, mid, params = msg['method'], msg.get('id'), msg.get('params') or {}
        if mid is None:  # notification: initialized, cancelled, ...
            return
        try:
            if method == 'initialize':
                from sawsim import __version__
                asked = params.get('protocolVersion')
                return self.reply(mid, dict(
                    protocolVersion=asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
                    capabilities=dict(tools=dict(listChanged=False)),
                    serverInfo=dict(name='sawsim', version=__version__), instructions=INSTRUCTIONS))
            if method == 'ping':
                return self.reply(mid, {})
            if method == 'tools/list':
                if self.tools is None:
                    self.tools = _tools()
                return self.reply(mid, dict(tools=self.tools))
            if method == 'tools/call':
                return self.reply(mid, self.call_tool(params))
            return self.reply(mid, error=dict(code=-32601, message='method not found: %s' % method))
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
            return self.reply(mid, error=dict(code=-32603, message='%s: %s' % (type(e).__name__, e)))

    def call_tool(self, params):
        name, args = params.get('name'), params.get('arguments') or {}
        token = (params.get('_meta') or {}).get('progressToken')
        step = [0]

        def progress(ev):
            if token is None:
                return
            step[0] += 1
            self.send(dict(jsonrpc='2.0', method='notifications/progress', params=dict(
                progressToken=token, progress=step[0],
                message='%s %s/%s' % (ev.get('stage', ''), ev.get('completed', 0), ev.get('total', 0)))))

        try:
            result = _call(name, args, progress)
        except KeyError as e:
            if name not in {t['name'] for t in (self.tools or _tools())}:
                return dict(content=[dict(type='text', text='unknown tool: %s' % name)], isError=True)
            result = dict(ok=False, error='missing argument: %s' % e)
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
            result = dict(ok=False, error='%s: %s' % (type(e).__name__, e))
        result = json.loads(json.dumps(result, default=str))
        content = [dict(type='text', text=json.dumps(result, ensure_ascii=False, indent=1))]
        if name == 'plot_curves' and result.get('ok') and str(result.get('output', '')).lower().endswith('.png'):
            data = base64.b64encode(Path(result['output']).read_bytes()).decode('ascii')
            content.append(dict(type='image', mimeType='image/png', data=data))
        return dict(content=content, structuredContent=result, isError=result.get('ok') is False)


def serve():
    """Run until stdin closes. Protocol on the original stdout; fd 1 becomes stderr for everything else."""
    proto = os.fdopen(os.dup(1), 'w', encoding='utf-8', newline='\n')
    sys.stdout.flush()
    os.dup2(2, 1)  # Gmsh, solver workers and stray prints can never corrupt the protocol stream
    os.environ.setdefault('SAWSIM_RUNS_DIR', str(Path.home() / '.sawsim' / 'runs'))
    server = Server(proto)
    for raw in sys.stdin.buffer:
        line = raw.decode('utf-8', 'replace').strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            server.reply(None, error=dict(code=-32700, message='parse error'))
            continue
        for m in (msg if isinstance(msg, list) else [msg]):
            server.handle(m)
    return 0
