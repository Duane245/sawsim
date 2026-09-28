"""Command-line interface: sawsim run | templates | serve."""
import argparse, json, sys
from pathlib import Path


def cmd_run(args):
    from sawsim.api import Model, sweep
    data = json.loads(Path(args.config).read_text(encoding="utf-8"))
    model = Model(**data)
    def progress(ev):
        if args.quiet: return
        print(f"\r{ev.get('stage','')} {ev.get('completed',0)}/{ev.get('total',0)}  {ev.get('elapsed_seconds',0):.1f}s", end="", file=sys.stderr, flush=True)
    res = sweep(model, args.output, mesh_only=args.mesh_only, on_progress=progress)
    if not args.quiet: print(file=sys.stderr)
    print(f"output: {res.dir}")
    if not args.mesh_only:
        print(f"points: {len(res.frequency_ghz)}  peak: {res.peak_frequency_ghz} GHz  |Y|max: {res.magnitude.max():.4g}")
    return 0


def cmd_templates(args):
    from sawsim.api import Model
    for k, v in Model.templates().items():
        print(f"{k:24s} {v}")
    return 0


def cmd_serve(args):
    print("`sawsim serve` (local web UI) ships with the web extra in a later step; run the API with:\n"
          "  python -m uvicorn sawsim_web.app:app --port 8765", file=sys.stderr)
    return 2


def main(argv=None):
    p = argparse.ArgumentParser(prog="sawsim", description="SawSim unit-cell piezoelectric FEM")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a sweep from a JSON config")
    r.add_argument("config"); r.add_argument("-o", "--output", required=True)
    r.add_argument("--mesh-only", action="store_true"); r.add_argument("-q", "--quiet", action="store_true")
    r.set_defaults(fn=cmd_run)
    t = sub.add_parser("templates", help="list model templates"); t.set_defaults(fn=cmd_templates)
    s = sub.add_parser("serve", help="start the local web UI"); s.set_defaults(fn=cmd_serve)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
