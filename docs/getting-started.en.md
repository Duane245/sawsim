[中文](getting-started.md) · **English**

# Getting started

## Install

```bash
pip install sawsim      # development version: pip install git+https://github.com/Duane245/sawsim
pip install "sawsim[fast]"                                # optional: pypardiso (MKL PARDISO direct solver)
```

Python ≥ 3.8. numpy, scipy, matplotlib, gmsh and pydantic are installed automatically.

On **headless Linux** (servers, CI, Docker) Gmsh needs two system libraries:

```bash
sudo apt install libglu1-mesa libopengl0        # Debian / Ubuntu
```

Without root, point `SAWSIM_VENDOR_LIB_DIR` at a directory containing `libGLU.so.1` and `libOpenGL.so.0`.

## First run

```python
from sawsim import Model, sweep

m = Model("sp_double_layer", pitch_um=1.085, electrode_um=0.17, points=101)
r = sweep(m, "out/double_layer")

r.frequency_ghz          # (101,) frequencies
r.admittance             # (101,) complex Y11
r.magnitude              # |Y11|
r.peak_frequency_ghz     # frequency of the largest sampled |Y|
```

Command-line equivalent:

```bash
sawsim templates                              # list the 9 templates
sawsim run config.json -o out/double_layer    # config.json below
```

```json
{"model_id": "sp_double_layer", "pitch_um": 1.085, "electrode_um": 0.17, "points": 101}
```

Omitted parameters take the template defaults. `Model.templates()` or `sawsim templates` lists the template ids; default geometry, frequency band and layer stack of each template are in [Models](models.en.md).

## Output directory

| File | Content |
|---|---|
| `input.json` | Complete effective input incl. material snapshots; re-runnable as is |
| `curve.json`, `admittance.csv`, `admittance.npz` | Frequency, Y11 real / imaginary / magnitude |
| `metadata.json` | Nodes, DOFs, peak frequency, timing, solver backend, versions and source hashes |
| `mesh.npz`, `mesh.png` | Mesh and mesh plot |
| `fields.npz`, `disp_field.png`, `phi_field.png` | Displacement and potential fields at the peak frequency |
| `material_snapshot.json`, `material_data.npz` | Material records used, hashes, rotation matrices and rotated tensors |
| `manifest.json` | Artifact list |

To check the geometry only: `sweep(m, "out/x", mesh_only=True)` or `sawsim run --mesh-only`.

## Units

- Lengths are entered in µm and frequencies in GHz; internally and in all output files everything is SI.
- **2D templates** (Q9): admittance per unit out-of-plane aperture, in S/m.
- **2.5D templates** (Hex27 periodic slice): the main curve in `curve.json` is likewise normalised to S/m; `admittance.npz` additionally holds `raw_admittance_s`, the total admittance of the slice in S, and `aperture_m`, the slice width. When comparing total admittance with other software use `raw_admittance_s`, or `magnitude × aperture_m`.

## Progress callback and parallelism

```python
def on_progress(event):            # {'stage','completed','total','elapsed_seconds',...}
    print(event["stage"], event["completed"], "/", event["total"])

sweep(m, "out/x", on_progress=on_progress)
```

Sweeps with more than 41 points run frequency points in parallel processes (up to 8 by default, `SAW_SWEEP_WORKERS` overrides); each process uses single-threaded BLAS. With pypardiso installed the linear solver is MKL PARDISO, otherwise SciPy SuperLU; the two agree to about 1e-4 relative.

## Custom materials

Built-in materials are read-only. User records are stored in `~/.sawsim/materials/` (override with `SAWSIM_MATERIALS_DIR`); format and import are described in [Materials and orientation](materials-and-orientation.en.md).
