[中文](models.md) · **English**

# Models

Nine single-period (SP) unit-cell templates. Layer counts refer to the main piezoelectric layer plus the carrier layers beneath it, excluding electrodes and PML; lengths in µm.

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

## Input parameters

| Field | Meaning | Default |
|---|---|---|
| `pitch_um` | IDT pitch (the unit cell is 2 × pitch wide) | 1.085 (TC-SAW 0.9968) |
| `electrode_um` | Electrode thickness | 0.17 |
| `metal_ratio` | Metallisation ratio | 0.5 |
| `substrate_um` | Main piezoelectric layer thickness (TC-SAW: total piezo depth) | template |
| `layers` | `[{material_id, thickness_um, euler_phi/theta/psi_deg}]`; carrier layers top-down for 2D multilayers, coating layers inside-out for TC-SAW | template |
| `mesh_um` | Mesh size control | 0.5 (TC 0.1, Hex27 0.2 – 0.217) |
| `start_ghz`, `stop_ghz`, `points` | Band and number of points (3 – 401) | template, 41 points |
| `voltage` | Drive voltage | 1 |
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
- **2D templates assign the main piezoelectric material to the PML**, also below carrier layers of multilayer stacks, following the source cases; Hex27 PMLs continue the bottom-most layer material. The convention is recorded in `metadata.json`.

## Known limitations

- The 2.5D Hex27 kernel lacks the ∂u<sub>z</sub>/∂y term in the γ<sub>yz</sub> strain; it is kept for comparability with the original numbers and flagged in the metadata. Do not infer general 3D accuracy from it.
- Hex27 assembly is capped at 2000 volume elements / 30000 nodes; larger meshes are rejected with a hint to coarsen.
- 2D multilayer templates deviate from the reference above about 2.4 GHz in the higher-order mode region; see [Validation](validation.en.md).
