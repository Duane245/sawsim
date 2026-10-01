<div align="center">

[中文](https://github.com/Duane245/sawsim/blob/main/README.md) · **English**

# SawSim

**Piezoelectric coupled finite-element solver for SAW resonator unit cells**
Q9 / Hex27 · PML · Bloch periodicity · verified against a reference FEM solution

[![CI](https://github.com/Duane245/sawsim/actions/workflows/ci.yml/badge.svg)](https://github.com/Duane245/sawsim/actions/workflows/ci.yml)
[![DOI v2.0.0](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.22728471-1682D4?logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.22728471)
[![PyPI](https://img.shields.io/pypi/v/sawsim?logo=pypi&logoColor=white)](https://pypi.org/project/sawsim/)
[![Last commit](https://img.shields.io/github/last-commit/Duane245/sawsim)](https://github.com/Duane245/sawsim/commits/main)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

Project name **SawSim**; Python package and command `sawsim`.

</div>

---

## Latest

- **2.1.0 (in development, 2026-10)**: JSON command line, agent guide and local MCP server for AI agents (Claude Code,
  codex, Claude Desktop, Cursor); generic stack `sp_stack` and custom materials from crystal constants; material loss
  of the piezoelectric layer (Rayleigh stiffness damping + dielectric loss) with Q.
- **2.0.2 (2026-09)**: released on PyPI, `pip install sawsim`.

Full history in the [CHANGELOG](https://github.com/Duane245/sawsim/blob/main/CHANGELOG.md).

## Install and use

```bash
pip install sawsim
pip install "sawsim[fast]"     # optional: MKL PARDISO direct solver
```

```python
from sawsim import Model, sweep

r = sweep(Model("sp_double_layer", pitch_um=1.085, points=101), "out/dbl")
r.frequency_ghz, r.admittance, r.peak_frequency_ghz
```

```bash
sawsim templates
sawsim run config.json -o out/dbl
```

**AI agents** (Claude Code, codex, …): every command can print JSON with fr, fa, k²eff and warnings. Run the install command once **on the machine where the agent runs**, in the Python environment that has sawsim, then start a new session and ask in plain language (e.g. "use sawsim to get fr and k² of the TC-SAW cell").

```bash
sawsim guide --install-claude                 # Claude Code: install as a skill (~/.claude/skills/sawsim)
sawsim guide --install-codex                  # codex: add to the global instructions ~/.codex/AGENTS.md
sawsim guide                                  # any other agent: print the full guide
sawsim mcp --print-config claude-desktop     # MCP (Claude Desktop, Cursor, …): print the config snippet
sawsim locate '{"model_id": "sp_tcsaw"}'      # bracket resonance/antiresonance and zoom
sawsim converge '{"model_id": "sp_tcsaw"}'    # mesh-refinement check
```

Headless Linux needs `libglu1-mesa libopengl0` for Gmsh. See [Getting started](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.en.md).

## Capabilities

| | |
|---|---|
| **Models** | 10 unit-cell templates: five 2D (Q9, incl. TC-SAW), four 2.5D periodic slices (Hex27), and the generic stack `sp_stack` (0–6 backing layers + 0–3 coatings) |
| **Physics** | Fully coupled displacement–potential; ME0 plane strain or ME1 out-of-plane extension; anisotropic crystals rotated by intrinsic ZXZ Euler angles |
| **Boundaries** | Bloch periodicity left/right, complex-coordinate-stretched PML at the bottom |
| **Meshing** | Parametric geometry via the Gmsh Python API, quadratic isoparametric elements |
| **Solve** | Real block form of the complex sparse system, MKL PARDISO or SciPy SuperLU, frequency-parallel sweeps |
| **Output** | Y11 admittance (CSV / NPZ / JSON), mesh, displacement and potential field plots, material snapshots and source hashes; every run is fully reproducible |
| **Materials** | Built-in LiNbO₃ (literature), LiTaO₃-type baseline dataset, Si, SiO₂, poly-Si, Si₃N₄, Al, Cu; custom JSON import, or built from crystal-class constants (isotropic / cubic / 6mm / 3m) |
| **Loss and Q** | Rayleigh stiffness damping + dielectric loss of the piezoelectric layer (as in the reference FEM models); resonance / antiresonance quality factors Q_r / Q_a resolved automatically |
| **AI interface** | JSON command line (locate fr/fa, mesh-convergence check, parameter scans, plots), Claude Code / codex guide, local MCP server |

## Validation

Each template is compared with an independent reference FEM solution: the resonance fr and anti-resonance fa of all nine templates agree with the reference within 0.5 MHz (mostly below 0.1 MHz). Peak and valley amplitudes of a lossless model are extremely sensitive to the frequency sampling and are not used as an accuracy measure. Full error table, figures and discussion in [Validation](https://github.com/Duane245/sawsim/blob/main/docs/validation.en.md). `pytest` reproduces the comparison at 5 – 6 frequencies per template.

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Duane245/sawsim/main/docs/figures/readme_validation_dark.png">
  <img alt="SawSim compared with an independent reference FEM" src="https://raw.githubusercontent.com/Duane245/sawsim/main/docs/figures/readme_validation_light.png" width="100%">
</picture>
<sub>Left: admittance of the TC-SAW unit cell, SawSim (line) and reference FEM (circles, every 4th sample). Right: resonance and anti-resonance deviation of all nine templates.</sub>
</div>

## Documentation

- [Getting started](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.en.md) — install, first run, output files, units
- [Models](https://github.com/Duane245/sawsim/blob/main/docs/models.en.md) — the ten templates (incl. the generic stack), parameters, displacement models, boundaries, mesh resolution, known limitations
- [Materials and orientation](https://github.com/Duane245/sawsim/blob/main/docs/materials-and-orientation.en.md) — built-in materials, record format, custom import, ZXZ Euler angles
- [Validation](https://github.com/Duane245/sawsim/blob/main/docs/validation.en.md) — resonance and anti-resonance frequencies against the reference
- [Driving SawSim with AI agents](https://github.com/Duane245/sawsim/blob/main/docs/ai-agents.en.md) — JSON commands, output fields, fr/fa accuracy, agent acceptance results

## Repository layout

```
src/sawsim/        Python package (api, cli, agent, metrics, config, models, solver, saw2d, sp_meshes, sp_hex_meshes, material_library, skill)
examples/          AI-agent acceptance tasks
tests/             regression and API tests; tests/data holds the reference curves
docs/              documentation and figures
matlab/            the v0.x MATLAB + Gmsh implementation (historical, MIT)
```

## License

Python package `sawsim`: **AGPL-3.0-or-later**; `matlab/` directory: MIT. See [LICENSE.md](https://github.com/Duane245/sawsim/blob/main/LICENSE.md). For a commercial license, contact the author via GitHub.

## Citation

Author: Shaoqing Duan.

To cite a specific version use its version DOI (v2.0.0: [10.5281/zenodo.22728471](https://doi.org/10.5281/zenodo.22728471)); to cite the project as a whole use the concept DOI [10.5281/zenodo.20362278](https://doi.org/10.5281/zenodo.20362278), which always resolves to the latest version. See [CITATION.cff](https://github.com/Duane245/sawsim/blob/main/CITATION.cff) for the format.

```bibtex
@software{duan_sawsim,
  author    = {Duan, Shaoqing},
  title     = {{SawSim: An open-source piezoelectric finite-element solver for SAW resonators}},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20362278},
  url       = {https://github.com/Duane245/sawsim}
}
```
