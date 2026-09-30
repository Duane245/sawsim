<div align="center">

[中文](https://github.com/Duane245/sawsim/blob/main/README.md) · **English**

# SawSim

**Piezoelectric coupled finite-element solver for SAW resonator unit cells**
Q9 / Hex27 · PML · Bloch periodicity · verified against a reference FEM solution

[![CI](https://github.com/Duane245/sawsim/actions/workflows/ci.yml/badge.svg)](https://github.com/Duane245/sawsim/actions/workflows/ci.yml)
[![DOI v2.0.0](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.22728471-1682D4?logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.22728471)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

Project name **SawSim**; Python package and command `sawsim`.

</div>

---

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
| **Materials** | Built-in LiNbO₃ (literature), Si, SiO₂, poly-Si, Si₃N₄, Al, Cu; custom JSON import, or built from crystal-class constants (isotropic / cubic / 6mm / 3m) |

## Validation

Each template is compared point by point with an independent reference FEM solution; the resonance fr and anti-resonance fa of all nine templates agree with the reference within 0.5 MHz (mostly below 0.1 MHz), amplitude errors around the main resonance are 0.1 – 2 %, and 2D multilayers deviate above 2.4 GHz in the higher-order mode region. Full error table, figures and discussion in [Validation](https://github.com/Duane245/sawsim/blob/main/docs/validation.en.md). `pytest` reproduces the comparison at 5 – 6 frequencies per template.

<div align="center">
<img src="https://raw.githubusercontent.com/Duane245/sawsim/main/docs/figures/compare_2p5d_double.png" width="640"><br>
<sub>2.5D SP double layer (LiTaO₃ 0.6 µm / Si 6.51 µm), 251 points. Dashed: sawsim, solid: reference; relative L2 error of |Y| 0.15 %.</sub>
</div>

## Documentation

- [Getting started](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.en.md) — install, first run, output files, units
- [Models](https://github.com/Duane245/sawsim/blob/main/docs/models.en.md) — the ten templates (incl. the generic stack), parameters, displacement models, boundaries, mesh resolution, known limitations
- [Materials and orientation](https://github.com/Duane245/sawsim/blob/main/docs/materials-and-orientation.en.md) — built-in materials, record format, custom import, ZXZ Euler angles
- [Validation](https://github.com/Duane245/sawsim/blob/main/docs/validation.en.md) — point-by-point comparison with the reference and how to read it
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

The Python package `sawsim` is released under **AGPL-3.0-or-later** (it links the GPL-licensed Gmsh library through its Python API). The historical MATLAB implementation under `matlab/` stays MIT. Contact the author for other licensing arrangements.

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
