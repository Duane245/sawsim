# AGENTS.md

## Using SawSim to answer simulation questions

Run `sawsim guide` and follow it. In short: `sawsim schema <model_id>` → `sawsim validate`
→ `sawsim locate` (fr/fa/k2eff) → `sawsim converge` (mesh check). Every command prints one
JSON object on stdout. Report fr/fa in GHz, k2eff in %, the uncertainty, the mesh check
and any warnings; state which template defaults you kept.

## Working on this repository

- Package source: `src/sawsim/`. Agent layer: `agent.py` (JSON operations), `metrics.py`
  (fr/fa/k2eff from a curve), `cli.py`; the guide shipped to agents is `src/sawsim/skill/SKILL.md`.
- Solver code (`solver.py`, `saw2d/`, `hex_*`) is validated against `tests/data/`; any numerical
  change must keep `tests/test_templates.py` passing (re-run the full reference comparison).
- Tests: `pytest -q` (2D, ~30 s); `SAWSIM_TEST_ALL=1 pytest -q` adds the 2.5D Hex27 cases (minutes).
  Headless Gmsh needs libGLU (`apt install libglu1-mesa`) or `SAWSIM_VENDOR_LIB_DIR`.
- `matlab/` is the historical MATLAB code (MIT); the Python package is AGPL-3.0.
- Finite-length (HCT) models are intentionally not part of this package.
