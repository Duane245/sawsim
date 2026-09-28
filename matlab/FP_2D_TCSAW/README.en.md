<div align="center">

# FP 2D TCSAW Demo

**Self-contained 2D finite-device temperature-compensated SAW (TC-SAW) simulation**

[简体中文](README.md) · **English**

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## Overview

A self-contained MATLAB demo of a **finite-device** 2D temperature-compensated SAW resonator: a multi-finger interdigital transducer on a LiNbO₃ substrate with SiO₂ / Si₃N₄ compensation stack and Al electrodes. Unlike the [`2DTCSAW/`](../2DTCSAW/) periodic-cell demo, this case models the **entire device** (21 IDT periods, ~48 700 nodes) with floating-potential left/right end electrodes and a complex-coordinate-stretched PML at the bottom — directly matching a real chip layout.

The frequency-domain sweep yields the Y₁₁ admittance curve over the band of interest.

---

## Run

```bash
cd FP_2D_TCSAW
matlab -batch "SolveSAW"
```

Or, inside an interactive MATLAB session:

```matlab
cd FP_2D_TCSAW
SolveSAW
```

**Expected output**

| File / figure | Content |
|---|---|
| `Y11.mat` | `fre` (201 frequency points), `Q`, `Y` |
| Figure 1 | Mesh (coloured by material region) |
| Figure 2 | Displacement field |
| Figure 3 | Electric potential |
| Figure 4 | Y₁₁ admittance curve |

The 201-point sweep takes **≈ 30 – 60 minutes** on a typical workstation (single process, no Parallel Computing Toolbox required). Memory usage peaks around 6–8 GB due to the ~48 700-node mesh.

---

## Parameters

| Item | Value |
|---|---|
| Piezoelectric substrate | LiNbO₃ |
| Compensation stack | SiO₂ + Si₃N₄ |
| Electrode | Al (multi-finger IDT) |
| IDT periods | 21 |
| Pitch | 1.9936 µm |
| Aperture (device length) | 41.866 µm |
| Element | Q9 (9-node quadrilateral) |
| Side boundaries | Free + floating-potential end electrodes (XFL / XFR) |
| Bottom boundary | PML (complex coordinate stretching) |
| PML thickness | 1.9936 µm |
| Sweep range | 1.60 – 2.00 GHz |
| Frequency points | 201 |
| Mesh nodes | ≈ 48 700 |

---

## SP-2D vs FP-2D — Which to Use?

| Aspect | [`2DTCSAW/`](../2DTCSAW/) (SP) | `FP_2D_TCSAW/` (FP, this demo) |
|---|---|---|
| Geometry | Single IDT period | Full 21-period device |
| Side BC | Bloch periodic | Free + floating-potential electrodes |
| Mesh size | ≈ 12 500 nodes | ≈ 48 700 nodes |
| Sweep time | ≈ 4 – 5 min | ≈ 30 – 60 min |
| What it captures | Periodic eigenmode behaviour | Real device response, including end reflections / spurious modes |

Use **SP** for rapid design-space sweeps; use **FP** when the result needs to match a fabricated chip.

---

## Files

```
FP_2D_TCSAW/
├── SolveSAW.m                          Main driver
├── initial_material_parameters.m       Material parameters (LiNbO3 / Al / SiO2 / Si3N4)
├── initialPML.m                        PML initialization (complex stretching)
├── readGmsh.m                          Mesh reader
├── codes/                              Solver core
│   ├── AssemblyKM2D.m                      K / M assembly entry point
│   ├── boundary_idx_2DF.m                  FP boundary indexing
│   ├── findSAWBoundary2DF.m                Floating-potential edge node identification
│   ├── forces.m / solution.m               RHS / linear solve
│   ├── formStiffnessMass2D*.m              Piezoelectric coupling blocks (uu / φφ / uφ)
│   ├── formStiffnessMass2DPML*.m           PML-region assembly (complex stretch)
│   ├── gaussQuadrature.m                   Gauss quadrature
│   ├── shapeFunctionsQ2D.m                 Q9 shape functions
│   ├── Jacobian.m                          Jacobian utilities
│   ├── oulaTransfer.m                      Euler-angle rotation of crystal tensors
│   ├── ComputingC2D.m                      Stiffness tensor construction
│   └── plot_*.m  /  plotY11.m              Visualization helpers
└── mesh/
    ├── SAW_TC_PML3.m                       MATLAB mesh (generated from the .py below)
    └── SAW_TC_PML3.py                      Gmsh parametric geometry script
```

---

## Requirements

- MATLAB R2023a or later
- No additional toolbox required (single-process sequential sweep)
- The MATLAB mesh `.m` file ships with the repo; regenerating it from `.py` requires [Gmsh](https://gmsh.info) and Python

---

## Methodology

- **Unknown fields** `[u₁, u₂, φ]` (displacement + potential) coupled by the piezoelectric constitutive law
- **Assembly** of `K` and `M` in `[u | φ]` block form
- **End electrodes** at the left- and right-most edges are modelled as **floating-potential** equipotential bodies (rows / columns of the system matrix are summed to enforce equal potential without prescribing a value)
- **PML** via complex coordinate stretching `α = 1 + d/(iω)`, attenuating outgoing waves along a polynomial profile `d`; pinned to the upper sweep frequency `ω = 2π · fre(end)`
- **Sweep** solves `(-ω²M + K) x = f` at every frequency, then evaluates `Y₁₁ = |iωQ/V|` from the induced charge `Q` on the signal electrode

---

## Citation

If this demo is useful in your work, please consider citing the repository:

[SawSim citation guide / 引用指南](../CITING.md)

---

## License

Released under the [MIT License](../LICENSE)
