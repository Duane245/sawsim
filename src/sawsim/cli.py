"""Command-line interface.

Human use:   sawsim run cfg.json -o out/        sawsim templates
Agent use:   every command below with --json prints exactly one JSON object on stdout
             (progress goes to stderr); exit code 0 = ok, 1 = error reported in the JSON.
"""
import argparse, json, os, sys
from pathlib import Path


def _progress(quiet):
    def cb(ev):
        if quiet: return
        print(f"\r{ev.get('stage','')} {ev.get('completed',0)}/{ev.get('total',0)}  {ev.get('elapsed_seconds',0):.1f}s",
              end="", file=sys.stderr, flush=True)
    return cb


class _StdoutToStderr:
    """Keep stdout clean for the JSON reply: send fd 1 (incl. Gmsh / worker processes) to stderr."""
    def __enter__(self):
        sys.stdout.flush()
        self.saved = os.dup(1)
        os.dup2(2, 1)
        return self

    def __exit__(self, *exc):
        sys.stdout.flush()
        os.dup2(self.saved, 1)
        os.close(self.saved)
        return False


def _emit(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1, default=str))
    return 0 if obj.get('ok', True) else 1


def _call(fn, *a, **kw):
    """Run an agent operation with stdout diverted, then print its JSON result."""
    try:
        with _StdoutToStderr():
            out = fn(*a, **kw)
    except Exception as e:
        out = dict(ok=False, error='%s: %s' % (type(e).__name__, e))
    return _emit(out)


def _config(args):
    """Config from a JSON file path, or inline JSON, plus --set key=value overrides."""
    text = args.config
    data = json.loads(text) if text.lstrip().startswith('{') else json.loads(Path(text).read_text(encoding='utf-8'))
    for item in getattr(args, 'set', None) or []:
        k, _, v = item.partition('=')
        try:
            data[k] = json.loads(v)
        except json.JSONDecodeError:
            data[k] = v
    return data


def cmd_run(args):
    if args.json:
        from sawsim import agent
        return _call(agent.run, _config(args), args.output, mesh_only=args.mesh_only, on_progress=_progress(args.quiet))
    from sawsim.api import Model, sweep
    if not args.output:
        print("error: -o/--output is required without --json", file=sys.stderr)
        return 2
    model = Model(**_config(args))
    res = sweep(model, args.output, mesh_only=args.mesh_only, on_progress=_progress(args.quiet))
    if not args.quiet: print(file=sys.stderr)
    print(f"output: {res.dir}")
    if not args.mesh_only:
        print(f"points: {len(res.frequency_ghz)}  peak: {res.peak_frequency_ghz} GHz  |Y|max: {res.magnitude.max():.4g}")
    return 0


def cmd_templates(args):
    if args.json:
        from sawsim import agent
        return _call(agent.list_templates)
    from sawsim.api import Model
    for k, v in Model.templates().items():
        print(f"{k:24s} {v}")
    return 0


def cmd_schema(args):
    from sawsim import agent
    return _call(agent.describe_template, args.model_id)


def _json_arg(text):
    return json.loads(text) if text.lstrip().startswith('{') else json.loads(Path(text).read_text(encoding='utf-8'))


def cmd_materials(args):
    from sawsim import agent
    if args.show:
        return _call(agent.material_show, args.show)
    if args.symmetries:
        return _call(agent.material_symmetries)
    if args.create:
        return _call(agent.material_create, _json_arg(args.create), dry_run=args.dry_run)
    if args.import_file:
        return _call(agent.material_import, _json_arg(args.import_file), dry_run=args.dry_run)
    return _call(agent.list_materials)


def cmd_validate(args):
    from sawsim import agent
    return _call(agent.validate, _config(args))


def cmd_summarize(args):
    from sawsim import agent
    return _call(agent.summarize, args.result_dir)


def cmd_locate(args):
    from sawsim import agent
    return _call(agent.locate, _config(args), zoom_points=args.points, on_progress=_progress(args.quiet))


def cmd_scan(args):
    from sawsim import agent
    values = [json.loads(v) for v in args.values.split(',')]
    return _call(agent.scan, _config(args), args.param, values, locate_each=args.locate, on_progress=_progress(args.quiet))


def cmd_converge(args):
    from sawsim import agent
    return _call(agent.converge, _config(args), factor=args.factor, on_progress=_progress(args.quiet))


def cmd_compare(args):
    from sawsim import agent
    return _call(agent.compare_curve, args.result_dir, args.reference)


def cmd_guide(args):
    """Print the agent guide, or install it as a Claude Code skill."""
    src = Path(__file__).with_name("skill") / "SKILL.md"
    if args.install_claude:
        target = Path(args.install_claude).expanduser() / "sawsim" / "SKILL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"installed: {target}", file=sys.stderr)
        return 0
    sys.stdout.write(src.read_text(encoding="utf-8"))
    return 0


def cmd_serve(args):
    print("`sawsim serve` (local web UI) ships with the web extra in a later step; run the API with:\n"
          "  python -m uvicorn sawsim_web.app:app --port 8765", file=sys.stderr)
    return 2


def main(argv=None):
    p = argparse.ArgumentParser(prog="sawsim", description="SawSim unit-cell piezoelectric FEM. "
                                "AI agents: run `sawsim guide` first; add --json, or use the JSON-only commands "
                                "schema/materials/validate/locate/scan/converge/compare.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def config_args(sp):
        sp.add_argument("config", help="config JSON file, or inline JSON starting with '{'")
        sp.add_argument("--set", action="append", metavar="KEY=VALUE", help="override a field (JSON value), repeatable")
        sp.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")

    r = sub.add_parser("run", help="run one sweep")
    config_args(r)
    r.add_argument("-o", "--output", help="output directory (with --json: default cached $SAWSIM_RUNS_DIR/<model>_<hash>)")
    r.add_argument("--mesh-only", action="store_true")
    r.add_argument("--json", action="store_true", help="print a JSON summary with fr/fa/k2eff/warnings")
    r.set_defaults(fn=cmd_run)

    t = sub.add_parser("templates", help="list model templates")
    t.add_argument("--json", action="store_true")
    t.set_defaults(fn=cmd_templates)

    s = sub.add_parser("schema", help="[JSON] defaults, allowed ranges and field meanings of one template")
    s.add_argument("model_id"); s.set_defaults(fn=cmd_schema)

    m = sub.add_parser("materials", help="[JSON] material library + Euler convention; show / create / import records")
    mg = m.add_mutually_exclusive_group()
    mg.add_argument("--show", metavar="ID", help="full record (tensors) of one material")
    mg.add_argument("--symmetries", action="store_true", help="crystal classes and constants accepted by --create")
    mg.add_argument("--create", metavar="SPEC", help="build + import from crystal constants (JSON file or inline)")
    mg.add_argument("--import", dest="import_file", metavar="RECORD", help="import a complete record (JSON file or inline)")
    m.add_argument("--dry-run", action="store_true", help="validate --create/--import without saving")
    m.set_defaults(fn=cmd_materials)

    v = sub.add_parser("validate", help="[JSON] check a config without running")
    config_args(v); v.set_defaults(fn=cmd_validate)

    su = sub.add_parser("summarize", help="[JSON] fr/fa/k2eff/warnings of an existing result directory")
    su.add_argument("result_dir"); su.set_defaults(fn=cmd_summarize)

    lo = sub.add_parser("locate", help="[JSON] coarse sweep, bracket fr/fa, then a zoomed sweep around them")
    config_args(lo); lo.add_argument("--points", type=int, default=101, help="points of the zoomed sweep")
    lo.set_defaults(fn=cmd_locate)

    sc = sub.add_parser("scan", help="[JSON] one sweep per value of a parameter")
    config_args(sc)
    sc.add_argument("--param", required=True); sc.add_argument("--values", required=True, help="comma-separated JSON values")
    sc.add_argument("--locate", action="store_true", help="use locate (zoomed, precise fr/fa) for every value")
    sc.set_defaults(fn=cmd_scan)

    cv = sub.add_parser("converge", help="[JSON] fr/fa shift when mesh_um is refined (default halved)")
    config_args(cv); cv.add_argument("--factor", type=float, default=0.5)
    cv.set_defaults(fn=cmd_converge)

    cp = sub.add_parser("compare", help="[JSON] compare a result with a reference |Y| curve (npz or CSV f_hz,|Y|)")
    cp.add_argument("result_dir"); cp.add_argument("reference"); cp.set_defaults(fn=cmd_compare)

    g = sub.add_parser("guide", help="print the AI-agent guide (workflow, fields, pitfalls)")
    g.add_argument("--install-claude", nargs="?", const="~/.claude/skills", metavar="SKILLS_DIR",
                   help="install the guide as a Claude Code skill (default ~/.claude/skills)")
    g.set_defaults(fn=cmd_guide)

    se = sub.add_parser("serve", help="start the local web UI"); se.set_defaults(fn=cmd_serve)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
