<div align="center">

# SP_3D_3ceng Demo

**Self-contained 2.5D periodic-cell SAW resonator simulation — 3-layer (LT + SiO₂ + Poly-Si)**

[简体中文](README.md) · **English**

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## Overview

A self-contained MATLAB demo of a **2.5D periodic-cell** SAW resonator using 27-node hexahedral (Hex27) high-order elements: a single IDT period with Bloch periodic boundaries on the left/right and front/back, equivalent to a finite-aperture infinite IDT array. Stack: **LiTaO₃ + SiO₂ + Poly-Si + Al**; complex-coordinate-stretched PML at the bottom.

A frequency-domain sweep yields the Y₁₁ admittance curve.

This demo shares the same solver core with the sibling SP-2.5D demos ([`../SP_3D_1ceng/`](../SP_3D_1ceng/) through [`../SP_3D_4ceng/`](../SP_3D_4ceng/)); only stack composition, pitch, and sweep range differ.

---

## Run

The repo uses a shared top-level [`codes/`](../codes/) and [`mesh/`](../mesh/) — the driver script adds them to MATLAB's path automatically.

```bash
cd SP_3D_3ceng
matlab -batch "Solve3DSAW"
```

Or inside an interactive MATLAB session:

```matlab
cd SP_3D_3ceng
Solve3DSAW
```

**Expected output**

| File / figure | Content |
|---|---|
| `Y11.mat` | `fre` (401 frequency points), `Q`, `Y` |
| Figure 1 | Mesh (coloured by material) |
| Figure 2 | Displacement field |
| Figure 3 | Electric potential |
| Figure 4 | Y₁₁ admittance curve |

The 401-point sweep takes **≈ 15 min+** on a typical workstation (single process, no Parallel Computing Toolbox required). Mesh has ≈ 9 500 Hex27 nodes; memory scales with mesh size.

---

## Parameters

| Item | Value |
|---|---|
| Piezoelectric substrate | LiNbO₃ |
| Stack (substrate → top) | LiTaO₃ + SiO₂ + Poly-Si + Al |
| Electrode | Al (single IDT period) |
| Pitch | 1.085 µm |
| Element | Hex27 (27-node hexahedral high-order) |
| Side boundaries | Bloch periodic (left/right and front/back) |
| Bottom boundary | PML (complex coordinate stretching) |
| Sweep range | 1.60 – 2.00 GHz |
| Frequency points | 401 |
| Mesh nodes | ≈ 9 500 |

---

## Generating the mesh

The MATLAB mesh `.m` is **not** bundled with this repository (it is large and easy to regenerate). Generate it once from the Gmsh `.py` source:

```bash
# Requires Gmsh (https://gmsh.info) and Python with the gmsh module
python mesh/SP_3D_3ceng.py
# This writes mesh/SP_3D_3ceng.m, which the driver loads via
#   SP_3D_3ceng;   % inside Solve3DSAW.m
```

If Gmsh / Python are not available on the run machine, pre-generate `SP_3D_3ceng.m` elsewhere and copy it into `mesh/`.

---

## Files

```
SP_3D_3ceng/
├── Solve3DSAW.m                      Main driver (adds ../codes and ../mesh to path)
├── initial_material_parameters.m     Material parameters
├── initialPML.m                      PML initialization (complex stretching)
└── readGmsh.m                        Mesh reader

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
