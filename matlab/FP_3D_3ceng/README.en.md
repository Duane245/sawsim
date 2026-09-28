<div align="center">

# FP_3D_3ceng Demo

**Self-contained 2.5D finite-device SAW resonator simulation — LT + Al + SiO₂ + Poly-Si**

[简体中文](README.md) · **English**

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## Overview

A self-contained MATLAB demo simulating a 2.5D **finite-device** (FP) SAW resonator: a 21-period IDT with reflectors, discretized with 27-node hexahedral (Hex27) high-order elements. Floating-potential boundaries on the left/right device ends; Bloch periodic boundaries front/back to model the infinite-aperture limit. Stack: **LiTaO₃ + Al + SiO₂ + Poly-Si**. Left, right and bottom complex-coordinate-stretched PMLs absorb outgoing waves.

A frequency sweep produces the Y₁₁ admittance curve.

This demo shares the solver core with sibling demos (`FP_3D_1ceng/` … `FP_3D_4ceng/`); only the stack, pitch, and sweep range differ.

---

## Run

The repo uses shared top-level [`codes/`](../codes/) and [`mesh/`](../mesh/); the driver auto-adds them to the MATLAB path.

```bash
cd FP_3D_3ceng
matlab -batch "Solve3DSAW"
```

Or interactively in MATLAB:

```matlab
cd FP_3D_3ceng
Solve3DSAW
```

**Outputs**

| File / Figure | Content |
|---|---|
| `Y11.mat` | `fre` (401 frequency points), `Q`, `Y` |
| Fig. 1 | Mesh (colored by material region) |
| Fig. 2 | Displacement field |
| Fig. 3 | Electric potential |
| Fig. 4 | Y₁₁ admittance curve |

A 401-point sweep takes **several hours** on a typical workstation (single process, no Parallel Computing Toolbox required); Hex27 node count ≈ 207 K.

---

## Geometry & physical parameters

| Item | Value |
|---|---|
| Stack (substrate → top) | LiTaO₃ + Al + SiO₂ + Poly-Si |
| Electrode | Al (21-period multi-finger IDT) |
| Pitch | 1.0 µm |
| Element | Hex27 (27-node high-order hexahedron) |
| Boundary | Floating potential (L/R ends) + Bloch periodic (F/B) |
| Outer absorption | PML (complex-coordinate-stretched, L/R/bottom) |
| Sweep range | 1.60 – 2.00 GHz |
| Number of frequency points | 401 |
| Mesh node count | ≈ 207 K |

---

## Mesh generation

The MATLAB mesh `.m` file is large and easy to regenerate, so it is **not shipped** with the repo. Generate it once via the Gmsh `.py` source:

```bash
# Requires Gmsh (https://gmsh.info) and Python with the gmsh module
python mesh/FP_3D_3ceng.py
# This script produces mesh/FP_3D_3ceng.m, which the driver loads via
#   FP_3D_3ceng;
```

If the run machine lacks Gmsh / Python, generate `FP_3D_3ceng.m` elsewhere and copy it into `mesh/`.

---

## Files

```
FP_3D_3ceng/
├── Solve3DSAW.m                      Main driver (auto-adds ../codes, ../mesh to path)
├── initial_material_parameters.m     Material parameters
├── initialPML.m                      PML initialization (complex-stretched)
└── readmesh.m                        Mesh reader
```

(Shared top-level [`codes/`](../codes/) and [`mesh/`](../mesh/) — see the repo root README.)

---

## Requirements

- MATLAB R2023a or later
- No additional toolboxes (single-process sequential sweep)
- Gmsh + Python (one-off, only to regenerate the `.m` mesh; see above)

---

## License

Released under the [MIT License](../LICENSE)
