[中文](models.md) · **English**

# Models

Ten single-period (SP) unit-cell templates; `sp_stack` is a generic 2D stack with any number of layers. Layer counts refer to the main piezoelectric layer plus the carrier layers beneath it, excluding electrodes and PML; lengths in µm.

| Template id | Element / dimension | Default stack (top to bottom) | Displacement model | Default band, GHz |
|---|---|---|---|---|
| `sp_single_layer` | Q9 · 2D | piezo 8 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_double_layer` | Q9 · 2D | piezo 0.6 / Si 8.33 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_triple_layer` | Q9 · 2D | piezo 0.6 / SiO₂ 0.5 / poly-Si 6.9 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_quad_layer` | Q9 · 2D | piezo 0.6 / SiO₂ 0.5 / poly-Si 1 / Si 7.83 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_tcsaw` | Q9 · 2D | LiNbO₃ 15.95; SiO₂ 0.72 and SiN 0.04 temperature-compensation layers on top | ME0 | 1.6 – 2.0 |
| `sp_2p5d_single_layer` | Hex27 · periodic slice | piezo 6.51 | ME1 | 1.5 – 2.7 |
| `sp_2p5d_double_layer` | Hex27 · periodic slice | piezo 0.6 / Si 6.51 | ME1 | 1.75 – 2.0 |
| `sp_2p5d_triple_layer` | Hex27 · periodic slice | piezo 0.6 / SiO₂ 0.5 / poly-Si 6.51 | ME1 | 1.6 – 2.0 |
| `sp_2p5d_quad_layer` | Hex27 · periodic slice | piezo 0.6 / SiO₂ 0.5 / poly-Si 1 / Si 6 | ME1 | 1.8 – 2.1 |
| `sp_stack` | Q9 · 2D (structured) | 0–3 coatings over the electrodes; piezo layer; 0–6 backing layers (default = single layer) | ME0 / ME1 | 1.5 – 2.7 (allowed 0.02 – 20) |

## Input parameters

| Field | Meaning | Default |
|---|---|---|
| `pitch_um` | IDT pitch (the unit cell is 2 × pitch wide) | 1.085 (TC-SAW 0.9968) |
| `electrode_um` | Electrode thickness | 0.17 |
| `metal_ratio` | Metallisation ratio | 0.5 |
| `substrate_um` | Main piezoelectric layer thickness (TC-SAW: total piezo depth) | template |
| `layers` | `[{material_id, thickness_um, euler_phi/theta/psi_deg}]`; carrier layers top-down for 2D multilayers, coating layers inside-out for TC-SAW | template |
| `coatings` | `sp_stack` only: layers over the electrodes, inside-out; the first is measured from the piezo surface, embeds the electrodes and must be thicker than them | `[]` |
| `mesh_um` | Mesh size control | 0.5 (TC 0.1, Hex27 0.2 – 0.217) |
| `start_ghz`, `stop_ghz`, `points` | Band and number of points (3 – 401) | template, 41 points |
| `voltage` | drive voltage | 1 |
| `beta_dk`, `eta_eps` | loss (2D templates, piezoelectric layer and its PML only, as in the reference FEM models): Rayleigh stiffness damping K_uu(1 + i·beta_dk·ω), dielectric loss ε(1 − i·eta_eps) | 0 (lossless) |
| `mode_extension` | 0 = ME0, 1 = ME1 | 1 (TC-SAW: 0 only) |
| `substrate_material`, `electrode_material` | Material ids | `sp_baseline`, `al` (TC: `linbo3_tc`, `cu`) |
| `euler_phi_deg`, `euler_theta_deg`, `euler_psi_deg` | ZXZ Euler angles of the main piezo layer | see materials doc |
| `aperture_um` | Hex27 only: y-width of the periodic slice | 0.217 (quad layer 0.25) |

Out-of-range values are rejected when the `Model` is constructed.

## Displacement models

- **ME0** plane strain: unknowns (u<sub>x</sub>, u<sub>y</sub>, φ), u<sub>z</sub> = 0, E<sub>z</sub> = 0. The full tensors are rotated first, then the Voigt [xx, yy, xy] and electric [x, y] components are retained.
- **ME1** out-of-plane extension: unknowns (u<sub>x</sub>, u<sub>y</sub>, u<sub>z</sub>, φ), ∂/∂z = 0, zero out-of-plane wavenumber.
- **TC-SAW**: source tensors live in the xz plane; the 2D computation takes the [x, z] projection mapped onto mesh [x, y]; the mapping is recorded in the metadata.

## Boundaries and PML

- Bloch periodic boundaries (zero phase) left and right, equivalent to an infinite periodic array; Hex27 slices are also periodic front-to-back.
- Complex-coordinate-stretched PML at the bottom; PML thickness 2 × pitch for 2D templates (TC-SAW 4 × pitch).
- `sp_stack`: PML 2 × pitch thick, made of the lowest backing layer's material (the piezo material when there is no backing).
- **2D templates assign the main piezoelectric material to the PML**, also below carrier layers of multilayer stacks, following the source cases; Hex27 PMLs continue the bottom-most layer material. The convention is recorded in `metadata.json`.

## Mesh resolution

- Laterally (along propagation) every template has at least 8 second-order elements (Q9; Hex27 likewise) per wavelength λ = 2 × pitch, also at the coarsest allowed `mesh_um`; `tests/test_stack_materials.py` checks each template.
- `sp_stack` meshes are structured: 8 lateral strips at the electrode edges, ⌈width/mesh_um⌉ elements each; vertically, element height = `mesh_um` within 2 × pitch of the surface and max(mesh_um, min(4·mesh_um, pitch/2)) deeper; at least 8 PML rows.
- Same stacks as the five 2D templates (`converge` fine-mesh result vs the independent reference):

| same stack as | reference fr / fa (GHz) | template Δfr / Δfa (MHz) | sp_stack Δfr / Δfa (MHz) | sp_stack − template (MHz) | DoF template / sp_stack |
|---|---|---|---|---|---|
| sp_single_layer | 1.80791 / 1.87557 | −0.13 / +0.03 | −0.17 / −0.07 | −0.04 / −0.09 | 25028 / 7668 |
| sp_double_layer | 1.82362 / 1.90406 | −0.55 / −0.42 | −0.50 / −0.37 | +0.05 / +0.05 | 22596 / 8460 |
| sp_triple_layer | 1.75860 / 1.84384 | −0.44 / −0.30 | −0.44 / −0.36 | −0.01 / −0.06 | 25700 / 7932 |
| sp_quad_layer | 1.75859 / 1.84382 | −0.45 / −0.33 | −0.44 / −0.37 | +0.01 / −0.03 | 24708 / 8988 |
| sp_tcsaw | 1.75891 / 1.81852 | −0.10 / −0.19 | −0.04 / −0.16 | +0.06 / +0.03 | 59805 / 73425 |

## Known limitations

- The 2.5D Hex27 kernel lacks the ∂u<sub>z</sub>/∂y term in the γ<sub>yz</sub> strain; it is kept for comparability with the original numbers and flagged in the metadata. Do not infer general 3D accuracy from it.
- Hex27 assembly is capped at 2000 volume elements / 30000 nodes; larger meshes are rejected with a hint to coarsen.
- 2D multilayer templates deviate from the reference above about 2.4 GHz in the higher-order mode region; see [Validation](validation.en.md).
