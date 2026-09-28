<div align="center">

# SP 2D TCSAW Demo

**Self-contained 2D single-period (Bloch) temperature-compensated SAW (TC-SAW) simulation**

[简体中文](README.md) · **English**

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## Overview

A self-contained MATLAB demo of a **single-period** (SP) 2D temperature-compensated SAW resonator: one IDT period with Bloch periodic boundaries on the left and right, equivalent to an infinitely long periodic IDT. Substrate is LiNbO₃ with SiO₂ / Si₃N₄ compensation stack and Al electrodes. A complex-coordinate-stretched PML at the bottom absorbs outgoing bulk waves.

For the **finite-device** (FP) counterpart with floating-potential end electrodes — see [`../FP_2D_TCSAW/`](../FP_2D_TCSAW/).

---

## Run

The repo uses a shared top-level [`codes/`](../codes/) and [`mesh/`](../mesh/) — the driver script adds them to MATLAB's path automatically.

```bash
cd SP_2D_TCSAW
matlab -batch "SolveSAW"
```

Or in an interactive MATLAB session:

```matlab
cd SP_2D_TCSAW
SolveSAW
```

**Expected output**

| File / figure | Content |
|---|---|
| `Y11.mat` | `fre` (201 frequency points), `Q`, `Y` |
| Figure 1 | Mesh (coloured by material) |
| Figure 2 | Displacement field |
| Figure 3 | Electric potential |
| Figure 4 | Y₁₁ admittance curve |

The 201-point sweep takes **≈ 4 – 5 minutes** on a typical workstation (single process, no Parallel Computing Toolbox needed).

---

## Parameters

| Item | Value |
|---|---|
| Piezoelectric substrate | LiNbO₃ |
| Compensation stack | SiO₂ + Si₃N₄ |
| Electrode | Al (single IDT period) |
| Pitch | 1.9936 µm |
| Element | Q9 (9-node quadrilateral) |
| Side boundaries | Bloch periodic (left / right) |
| Bottom boundary | PML (complex coordinate stretching) |
| Sweep range | 1.60 – 2.00 GHz |
| Frequency points | 201 |
| Mesh nodes | ≈ 12 500 |

---

## Generating the mesh

The MATLAB mesh `.m` is **not** bundled with this repository (it is large and easy to regenerate). Generate it once from the Gmsh `.py` source:

```bash
# Requires Gmsh (https://gmsh.info) and Python with the gmsh module
python mesh/SAW-PeriodBC1_TC_1.py
# This writes mesh/SAW_PeriodBC1_TC.m which the driver loads via the call
#   SAW_PeriodBC1_TC;   % inside SolveSAW.m
```

If Gmsh / Python are not available on the run machine, you can pre-generate `SAW_PeriodBC1_TC.m` elsewhere and copy it into `mesh/`.

---

## Files

```
SP_2D_TCSAW/
├── SolveSAW.m                          Main driver
├── initial_material_parameters.m       Material parameters (LiNbO3 / Al / SiO2 / Si3N4)
├── initialPML.m                        PML initialization (complex stretching)
├── readGmsh.m                          Mesh reader
└── findSAWBoundary.m                   Boundary-node identification

(plus the shared top-level codes/ and mesh/, see the repo root README)
```

---

## Requirements

- MATLAB R2023a or later
- No additional toolbox required (single-process sequential sweep)
- Gmsh + Python (one-time, only to regenerate the `.m` mesh; see above)

---

## License

Released under the [MIT License](../LICENSE)
