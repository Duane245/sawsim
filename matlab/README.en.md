<div align="center">

# SawSim

Formerly known as **SAW-FEM-MATLAB**. An open-source solver for surface acoustic wave simulation.

**A MATLAB + Gmsh piezoelectric finite-element solver**
for the frequency-domain simulation and design of Surface Acoustic Wave (SAW) resonators and filters

[简体中文](README.md) · **English**

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a-EE6B27?logo=mathworks&logoColor=white)
![Gmsh](https://img.shields.io/badge/Mesh-Gmsh-4B8BBE)
![Python](https://img.shields.io/badge/Postprocess-Python%20%2F%20matplotlib-3776AB?logo=python&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![Cases](https://img.shields.io/badge/Case%20library-17%20models-2E8B57)
[![Demo](https://img.shields.io/badge/Demo-2D%20TCSAW-FF6F00)](SP_2D_TCSAW/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![Changelog](https://img.shields.io/badge/Changelog-keepachangelog-E05735)](CHANGELOG.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20362278.svg)](https://doi.org/10.5281/zenodo.20362278)

</div>

[Cite this software: version DOIs, recommended reference and BibTeX](CITING.md)

---

## 📑 Contents

- [Overview](#intro)
- [Project Status](#status)
- [Capabilities](#capability)
- [Methodology](#method)
- [Worked Example](#showcase)
- [Model Library](#library) · [SP-2D](#sp2d) · [SP-2.5D](#sp25d) · [FP-2D](#fp2d) · [FP-2.5D](#fp25d)
- [Tech Stack](#stack)
- [Code Demos](#demo)
- [Contact & Collaboration](#contact)

---

<a id="intro"></a>

## 📖 Overview

Surface Acoustic Wave (SAW) resonators are the core building block of RF front-end filters, widely deployed in mobile communications, IoT and sensing. This project implements a piezoelectric finite-element (FEM) solver covering the piezoelectric constitutive law and crystal tensor handling, complex-coordinate-stretched PML, vectorized FE assembly, `parfor` parallel frequency sweeps and Y11 post-processing — for the frequency-domain (harmonic) analysis of SAW resonators.

Under interdigital-transducer (IDT) excitation, the solver jointly solves the structural-mechanics displacement field `u` and the electrostatic potential field `φ` of the piezoelectric coupling equations, sweeps over a specified band, and outputs the **Y11 admittance curve** of the device — the key indicator used to evaluate SAW resonator / filter performance (resonant frequency, electromechanical coupling coefficient, quality factor).

| | |
|---|---|
| 🧩 **Piezoelectric multiphysics** | Fully coupled displacement–potential analysis with anisotropic piezoelectric single crystals such as LiNbO₃ and LiTaO₃ |
| 🌊 **Perfectly Matched Layer (PML)** | Complex coordinate stretching absorbs outgoing waves and accurately mimics a semi-infinite substrate, suppressing bulk-wave reflection |
| 📐 **Parametric modelling** | Parametric Gmsh meshes — all key geometric dimensions are scripted parameters and can be adjusted in a single edit |
| ⚡ **Parallel frequency sweep** | `parfor` multi-core parallelism (801-point 2-D case ≈ 8 s) |

---

<a id="status"></a>

## 🔴 Project Status

| | |
|---|---|
| **Current version** | v0.4.0 (2026-06-10) |
| **Open-sourced demos** | 10 / 17 — `SP_2D_TCSAW`, `FP_2D_TCSAW`, `SP_3D_1ceng` ~ `4ceng`, `FP_3D_1ceng` ~ `4ceng` |
| **Maintenance** | 🟢 Active — under iterative development |
| **DOI** | [10.5281/zenodo.20362278](https://doi.org/10.5281/zenodo.20362278) (concept) |

**Roadmap**

- **v0.5.0** — SP-2D `*ceng` series: `SP_2D_1ceng` / `2ceng` / `3ceng` / `4ceng` (4 cases, Q9 multi-layer stacks under periodic BC)
- **Long term** — `pysaw_fem`: zero-license Python rewrite (NumPy / SciPy / scikit-fem)

---

<a id="capability"></a>

## 🎯 Capabilities

| Dimension | Supported scope |
|---|---|
| **Spatial dimension** | 2D / 2.5D (9-node quadrilateral Q9, 27-node hexahedral Hex27 high-order elements) |
| **Device model** | Single-period unit cell (Bloch periodic BC); finite device (free / floating-potential BC) |
| **Stack** | Single up to multilayer (1–4 layers) of piezoelectric / dielectric stacks |
| **Special process** | Temperature-compensated SAW (TC-SAW) with SiO₂ / Si₃N₄ compensation layers |
| **Analysis mode** | Plane-strain analysis; 2.5D mode-extension analysis |
| **Materials** | Arbitrary-cut anisotropic piezoelectric single crystals (Euler-angle rotation) + metal electrodes |
| **Problem size** | 2D ~10⁴ DOFs; 2.5D up to **~10⁶ DOFs** |

---

<a id="method"></a>

## 🔬 Methodology

### ① Piezoelectric coupling model

In a SAW device, mechanical vibration is strongly coupled to the electric field through the **piezoelectric effect**. The solver works in the frequency domain and jointly solves for the **structural displacement field `u`** and the **electrostatic potential field `φ`** — the two are coupled through the piezoelectric constitutive law, with material properties described by the density `ρ`, elastic stiffness tensor `C`, piezoelectric coupling tensor `e` and permittivity tensor `ε`. Anisotropic piezoelectric single crystals such as LiNbO₃ and LiTaO₃ have their crystal tensors **rotated by Euler angles** from the crystallographic frame into the device frame to match the actual wafer cut.

### ② Parametric mesh generation

Geometry and meshing are driven by **Gmsh**. The IDT pitch, acoustic wavelength, electrode thickness, metallization ratio, PML thickness and mesh seeding are all scripted parameters, so a new design can be remeshed in a single edit. Mesh entities are tagged into physical groups so that the piezoelectric body, electrodes, functional sublayers, PML regions and the various boundaries are picked up automatically.

<div align="center">
<img src="docs/images/mesh.png" width="300"><br>
<sub><b>Fig. 1</b> · Finite-element mesh of a SAW resonator periodic cell — coloured by material to show the piezoelectric substrate, IDT electrodes (Al) and bottom PML absorber</sub>
</div>

### ③ FE discretization and PML absorbing boundary

The computational domain is discretized with **high-order elements** — 9-node quadrilaterals (Q9) in 2D and 27-node hexahedra (Hex27) in 2.5D. DOFs are ordered as `[displacement u | potential φ]`; the mass matrix `M` and stiffness matrix `K` are assembled to form the fully coupled displacement–potential FE system.

**Matrix assembly is implemented in a vectorized fashion.** A conventional element-by-element `for` loop is doubly penalised in an interpreted language such as MATLAB: first, the interpreter re-enters the loop body once per element, accumulating overhead with the element count; second, every element accumulates into the sparse matrix by indexed assignment (`K(dof,dof) = K(dof,dof) + Ke`), and each such insertion triggers a re-layout and re-allocation of the sparse structure — particularly costly for the 2.5D models that exceed one million DOFs. The solver replaces this with **batch vectorized assembly**: it computes the Jacobians, strain–displacement matrices and per-element contributions for all elements at once, aggregates them into global `(i, j, v)` triplets, then calls `sparse()` once to materialise `K / M`. By eliminating both the explicit loop and the repeated insertions, assembly time drops dramatically — this is the enabler that makes million-DOF simulations tractable.

A **Perfectly Matched Layer (PML)** is placed at the bottom and the lateral sides of the device. Through complex coordinate stretching, outgoing bulk waves are attenuated along a prescribed profile inside the PML — equivalent to a semi-infinite substrate — so that energy leakage and the resonance Q-factor are captured accurately.

### ④ Frequency-domain sweep

The solver supports two boundary-condition flavours: the **finite-device model (FP)** mimics a real, finite multi-finger IDT — fixed at the bottom, free on the sides — and corresponds directly to the actual chip layout; the **single-period model (SP)** takes a single unit cell with Bloch periodic boundaries on the left and right, equivalent to an infinitely long periodic array at a tiny fraction of the cost.

Within the specified band, every frequency point is solved in turn: a dynamic matrix is built, boundary conditions and the IDT-voltage excitation are applied, the coupled piezoelectric linear system is solved for displacement and potential, and the induced charge `Q` on the signal electrode is integrated to give the admittance `Y₁₁ = |iωQ/V|`. The frequency points are independent of one another and are evaluated in parallel via `parfor`.

```mermaid
flowchart LR
    A["① Material parameters<br/>Crystal-tensor rotation"] --> B["② Mesh import<br/>Region tagging"]
    B --> C["③ Boundary conditions<br/>PML initialisation"]
    C --> D["④ Vectorized K / M assembly<br/>Mass · Stiffness matrices"]
    D --> E["⑤ parfor frequency sweep<br/>Solve (-ω²M+K)·x = f"]
    E --> F["⑥ Extract charge Q<br/>Admittance Y = |iωQ/V|"]
```

---

<a id="showcase"></a>

## 📊 Worked Example: 2-D Periodic Unit Cell

A 2-D periodic-cell model is used here to illustrate the full physical fields produced by the solver. Under AC IDT excitation, the solver simultaneously delivers the displacement and electric-potential fields inside the device.

<div align="center">
<img src="docs/images/displacement.png" width="262">
&nbsp;&nbsp;
<img src="docs/images/potential.png" width="262">
<br>
<sub><b>Fig. 2</b> · Displacement-field magnitude at resonance (f_r ≈ 1.81 GHz) — energy concentrated near the surface and damped to zero inside the PML &nbsp;|&nbsp; <b>Fig. 3</b> · Potential field — positive/negative electrodes set up the field that, via the piezoelectric effect, launches the acoustic wave</sub>
</div>

The admittance is computed from the induced charge `Q` on the signal electrode: **`Y = |iωQ / V|`**. **Peaks** on the admittance curve mark the **resonance** (low impedance) and **troughs** mark the **anti-resonance** (high impedance); the spacing between them reflects the electromechanical coupling strength of the device.

<div align="center">
<img src="docs/images/admittance.png" width="560"><br>
<sub><b>Fig. 4</b> · Y11 admittance curve — the resonance peak f_r and the anti-resonance trough f_a are clearly resolved, characterising the harmonic response of the device</sub>
</div>

---

<a id="library"></a>

## 📚 Model Library

The solver ships with a **library of 17 SAW cases** spanning 2D / 2.5D, single-period (SP) / finite-device (FP), single up to multilayer stacks and the temperature-compensated (TC-SAW) variant. Each family includes a model-spec table, structural / field visualisations and a composite Y11 plot. The ordering below is "SP before FP, 2D before 2.5D".

<a id="sp2d"></a>

### 🔹 SP-2D — 2-D Periodic Unit Cell

A single periodic unit cell with Bloch periodic boundaries on the left and right, equivalent to an infinitely long periodic IDT. Covers 1- to 4-layer stacks; one further case is a **temperature-compensated SAW (TC-SAW)** that stacks SiO₂ / Si₃N₄ compensation layers on top of the piezoelectric film to suppress the temperature drift of the resonant frequency.

| Case | Stack (substrate → top) | Nodes | Sweep (GHz) | f_r (GHz) |
|:---|:---:|---:|:---:|---:|
| `SP_2D_1ceng` | LiTaO₃ | 1,563 | 1.50 – 2.70 | 1.81 |
| `SP_2D_2ceng` | LiTaO₃ / Si | 1,465 | 1.50 – 2.70 | 1.82 |
| `SP_2D_3ceng` | LiTaO₃ / SiO₂ / Poly-Si | 1,465 | 1.50 – 2.70 | 1.76 |
| `SP_2D_4ceng` | LiTaO₃ / SiO₂ / Poly-Si / Si | 1,601 | 1.50 – 2.70 | 1.76 |
| `SP_2D_TCSAW` | LiNbO₃ / SiO₂ / Si₃N₄ (TC) | 12,565 | 1.60 – 2.00 | 1.76 |

<div align="center">
<img src="docs/images/mesh_SP2D.png" width="100%"><br>
<sub><b>Fig. 5</b> · SP-2D periodic-cell meshes — coloured by material to show the piezoelectric layer, functional sublayers, electrodes and PML</sub>
<br><br>
<img src="docs/images/admittance_SP2D.png" width="100%"><br>
<sub><b>Fig. 6</b> · Y11 admittance curves of the SP-2D series</sub>
</div>

<a id="sp25d"></a>

### 🔹 SP-2.5D — 2.5-D Periodic Unit Cell

2.5-D periodic-cell models discretized with 27-node hexahedral (Hex27) high-order elements; periodic boundaries are applied front-back and left-right, modelling a finite-aperture periodic IDT.

| Case | Stack | Nodes | Sweep (GHz) | f_r (GHz) |
|:---|:---:|---:|:---:|---:|
| `SP_3D_1ceng` | Single layer | 8,127 | 1.50 – 2.70 | 1.81 |
| `SP_3D_2ceng` | Two layers | 8,721 | 1.75 – 2.00 | 1.84 |
| `SP_3D_3ceng` | Three layers | 9,513 | 1.60 – 2.00 | 1.76 |
| `SP_3D_4ceng` | Four layers | 10,305 | 1.80 – 2.10 | 1.90 |

<div align="center">
<img src="docs/images/board_SP25D.png" width="100%"><br>
<sub><b>Fig. 7</b> · SP-2.5D overview: mesh, displacement field and potential field</sub>
<br><br>
<img src="docs/images/admittance_SP25D.png" width="100%"><br>
<sub><b>Fig. 8</b> · Y11 admittance curves of the SP-2.5D series</sub>
</div>

<a id="fp2d"></a>

### 🔹 FP-2D — 2-D Finite Device

Real finite-length device models (multi-finger IDT arrays), fixed at the bottom and free on the sides — corresponding directly to the actual chip layout.

| Case | Stack (substrate → top) | Nodes | Sweep (GHz) | f_r (GHz) |
|:---|:---:|---:|:---:|---:|
| `FP_2D_1ceng` | LiTaO₃ | 17,349 | 1.60 – 2.00 | 1.70 |
| `FP_2D_2ceng` | LiTaO₃ / Si | 17,829 | 1.60 – 2.00 | 1.73 |
| `FP_2D_3ceng` | LiTaO₃ / SiO₂ / Si | 18,809 | 1.60 – 2.00 | 1.66 |
| `FP_2D_4ceng` | LiTaO₃ / SiO₂ / Poly-Si / Si | 20,769 | 1.60 – 2.00 | 1.66 |

<div align="center">
<img src="docs/images/mesh_FP2D.png" width="100%"><br>
<sub><b>Fig. 9</b> · FP-2D finite-element meshes — coloured by material to show the piezoelectric layer, functional sublayers, electrodes and PML absorber</sub>
<br><br>
<img src="docs/images/admittance_FP2D.png" width="100%"><br>
<sub><b>Fig. 10</b> · Y11 admittance curves of the FP-2D series</sub>
</div>

<a id="fp25d"></a>

### 🔹 FP-2.5D — 2.5-D Finite Device

The largest models in the library — the biggest mesh exceeds 270,000 nodes and one million DOFs, demonstrating the solver's capacity for large-scale problems.

| Case | Stack | Nodes | Sweep (GHz) | f_r (GHz) |
|:---|:---:|---:|:---:|---:|
| `FP_3D_1ceng` | Single layer | 273,627 | 1.80 – 2.20 | 1.88 |
| `FP_3D_2ceng` | Two layers | 86,835 | 1.75 – 2.00 | 1.81 |
| `FP_3D_3ceng` | Three layers | 207,453 | 1.60 – 2.00 | 1.85 |
| `FP_3D_4ceng` | Four layers | 66,585 | 1.80 – 2.10 | 1.87 |

<div align="center">
<img src="docs/images/board_FP25D.png" width="100%"><br>
<sub><b>Fig. 11</b> · FP-2.5D overview: mesh, displacement field and potential field</sub>
<br><br>
<img src="docs/images/admittance_FP25D.png" width="100%"><br>
<sub><b>Fig. 12</b> · Y11 admittance curves of the FP-2.5D series — harmonic response of large-scale finite-device models</sub>
</div>

---

<a id="stack"></a>

## 🛠️ Tech Stack

| Tool | Role |
|---|---|
| **MATLAB** (with Parallel Computing Toolbox) | FE assembly and `parfor` parallel frequency-domain solve |
| **Gmsh** | Parametric geometry and meshing |
| **Python / matplotlib** | Gmsh scripting interface and post-processing visualisation |

---

<a id="demo"></a>

## 💻 Code Demos

**10 ready-to-run demos** are bundled with this repository, all sharing the **same top-level solver core ([`codes/`](codes/)) and mesh sources ([`mesh/`](mesh/))**, differing only in dimension, boundary conditions and stack composition.

### 🔹 SP-2D — periodic unit cell, 2D (since v0.1.0)

- [`SP_2D_TCSAW/`](SP_2D_TCSAW/) — Q9 elements · Bloch periodic BC · ≈ 12 500 nodes · `matlab -batch "SolveSAW"` (≈ 4 – 5 min, single process)

### 🔹 FP-2D — finite device, 2D (since v0.2.0)

- [`FP_2D_TCSAW/`](FP_2D_TCSAW/) — full 21-period multi-finger IDT · floating-potential end electrodes · ≈ 48 700 nodes · `matlab -batch "SolveSAW"` (≈ 30 – 60 min, single process)

### 🔹 SP-2.5D — periodic unit cell, 2.5D (since v0.3.0)

| Demo | Stack | Pitch | Sweep | Nodes |
|---|---|---|---|---|
| [`SP_3D_1ceng/`](SP_3D_1ceng/) | LiTaO₃ + Al | 1.085 µm | 1.50 – 2.70 GHz | ~ 8 100 |
| [`SP_3D_2ceng/`](SP_3D_2ceng/) | + Si layer | 1.085 µm | 1.75 – 2.00 GHz | ~ 8 700 |
| [`SP_3D_3ceng/`](SP_3D_3ceng/) | + SiO₂ + Poly-Si layers | 1.085 µm | 1.60 – 2.00 GHz | ~ 9 500 |
| [`SP_3D_4ceng/`](SP_3D_4ceng/) | + Si layer (4-layer stack) | 1.0 µm | 1.80 – 2.10 GHz | ~ 10 300 |

These 4 demos use 27-node hexahedral (Hex27) high-order elements. Uniform run command: `cd SP_3D_<N>ceng && matlab -batch "Solve3DSAW"` (single process, ~10 – 30 min depending on layer count and sweep size).

### 🔹 FP-2.5D — finite device, 2.5D (since v0.4.0)

| Demo | Stack | Pitch | Sweep | Nodes |
|---|---|---|---|---|
| [`FP_3D_1ceng/`](FP_3D_1ceng/) | LiNbO₃ + Al | 1.0 µm | 1.80 – 2.20 GHz | ~ 274 K |
| [`FP_3D_2ceng/`](FP_3D_2ceng/) | LiTaO₃ + Al + Si | 1.085 µm | 1.75 – 2.00 GHz | ~ 87 K |
| [`FP_3D_3ceng/`](FP_3D_3ceng/) | + SiO₂ + Poly-Si layers | 1.0 µm | 1.60 – 2.00 GHz | ~ 207 K |
| [`FP_3D_4ceng/`](FP_3D_4ceng/) | + Si layer (5-layer stack) | 1.0 µm | 1.80 – 2.10 GHz | ~ 67 K |

These 4 demos also use Hex27, with a full 21-period multi-finger IDT. Uniform run command: `cd FP_3D_<N>ceng && matlab -batch "Solve3DSAW"` (single process; larger than SP-2.5D, typically 1 – several hours depending on layer count and sweep size).

Use **SP** for rapid design-space sweeps; use **FP** when the result needs to match a fabricated chip. Each demo's `Solve*SAW.m` prepends `addpath('../codes')` and `addpath('../mesh')`, so the top-level shared folders are picked up automatically.

### Mesh regeneration (one-time)

The MATLAB mesh `.m` files are **not bundled** (they are large and easy to regenerate). Before the first run, generate them once from the Gmsh `.py` sources:

```bash
# SP-2D / FP-2D
python mesh/SAW-PeriodBC1_TC_1.py    # → mesh/SAW_PeriodBC1_TC.m   (for SP_2D_TCSAW)
python mesh/SAW_TC_PML3.py           # → mesh/SAW_TC_PML3.m        (for FP_2D_TCSAW)

# SP-2.5D (v0.3.0)
python mesh/SP_3D_1ceng.py           # → mesh/SP_3D_1ceng.m
python mesh/SP_3D_2ceng.py           # → mesh/SP_3D_2ceng.m
python mesh/SP_3D_3ceng.py           # → mesh/SP_3D_3ceng.m
python mesh/SP_3D_4ceng.py           # → mesh/SP_3D_4ceng.m

# FP-2.5D (4 new in v0.4.0)
python mesh/FP_3D_1ceng.py           # → mesh/FP_3D_1ceng.m
python mesh/FP_3D_2ceng.py           # → mesh/FP_3D_2ceng.m
python mesh/FP_3D_3ceng.py           # → mesh/FP_3D_3ceng.m
python mesh/FP_3D_4ceng.py           # → mesh/FP_3D_4ceng.m
```

Requires [Gmsh](https://gmsh.info) and Python with the `gmsh` module. If Gmsh / Python are not available, pre-generate elsewhere and copy the resulting `.m` files into `mesh/`.

All demos produce `Y11.mat` + mesh / displacement / potential / Y₁₁ admittance figures. Requires MATLAB R2023a+ only — no extra toolboxes needed. Released under the [MIT License](LICENSE); version history in [`CHANGELOG.md`](CHANGELOG.md).

---

<a id="contact"></a>

## 🤝 Contact & Collaboration

Discussions on SAW simulation, piezoelectric FEM and PML implementations are very welcome; academic collaborations, industry consulting and pull requests are equally welcome.

- 🐛 **Issues** · [GitHub Issues](https://github.com/Duane245/sawsim/issues) — bug reports and feature requests
