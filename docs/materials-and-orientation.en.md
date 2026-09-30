[中文](materials-and-orientation.md) · **English**

# Materials and crystal orientation

## Built-in materials

| id | Name | Role | Status | Notes |
|---|---|---|---|---|
| `linbo3_bouchy_2022` | LiNbO₃ · Bouchy 2022 (25 °C) | substrate | literature | Bouchy et al., *Materials* 2022, 15, 4716 (DOI 10.3390/ma15134716). Full Cᴱ / e / εˢ / ρ, room temperature, real-part lossless approximation, measured 20 Hz – 20 MHz |
| `linbo3_tc` | LiNbO₃ · TC-SAW dataset | substrate | legacy | Full tensors, ρ = 4628 kg/m³. Already expressed in the reference device frame (pre-rotated) |
| `sp_baseline` | Piezo substrate · baseline dataset I | substrate | legacy | Full tensors, ρ = 7450 kg/m³ (consistent with LiTaO₃). Crystal identity not independently verified |
| `al`, `al_hex35` | Al (ν = 0.33 / 0.35) | electrode | legacy | E = 70 GPa, ρ = 2700 kg/m³ |
| `cu` | Cu | electrode | legacy | E = 120 GPa, ν = 0.34, ρ = 8960 kg/m³ |
| `si_isotropic` | Si · isotropic approximation | layer | legacy | E = 170 GPa, ν = 0.28, ρ = 2329 kg/m³, εr = 11.7 |
| `si_cubic_hex` | Si · cubic anisotropic | layer | legacy | C11 = 166, C12 = 64, C44 = 80 GPa, εr = 11.68 |
| `si_aniso_hex` | Si · anisotropic full tensor | layer | legacy | Full 6×6 stiffness, εr = 11.8 |
| `polysi`, `polysi_160` | Poly-Si (E = 169 / 160 GPa) | layer | legacy | ν = 0.22, ρ = 2320 kg/m³, εr = 4.5 |
| `sio2` | SiO₂ | layer | legacy | E = 70 GPa, ν = 0.17, ρ = 2200 kg/m³, εr = 4.2 |
| `sin` | Si₃N₄ | layer | legacy | E = 160 GPa, ν = 0.23, ρ = 3100 kg/m³, εr = 9.7 |

`legacy` marks commonly used engineering constants whose original literature and measurement conditions have not been verified item by item; `literature` marks records whose constants all come from one cited paper with table references. **The density of `sp_baseline` corresponds to LiTaO₃, not LiNbO₃**; treat it as a baseline dataset rather than a specific crystal until its identity is confirmed.

Built-in records are read-only. To list and inspect them:

```bash
python -m sawsim.material_library list
python -m sawsim.material_library show linbo3_bouchy_2022 --version 1.0.0
```

## Record format

Each record is one JSON file with the fields

| Field | Meaning |
|---|---|
| `id`, `version`, `name`, `description` | Identity and description; `version` is semantic |
| `roles` | Subset of `substrate` / `electrode` / `layer` |
| `status` | `literature` / `legacy` / `user` |
| `source`, `reference_frame`, `temperature_k`, `symmetry` | Provenance, frame of the tensors, temperature, symmetry |
| `constitutive` | Fixed: `stress_charge` |
| `voigt_order` | Fixed: `xx,yy,zz,yz,xz,xy`, engineering shear strain |
| `rho_kg_m3` | Density |
| `C_pa` | Stiffness at constant electric field Cᴱ, 6×6, Pa |
| `e_c_m2` | Piezoelectric stress matrix e, 3×6, C/m² |
| `eps_f_m` | Absolute permittivity at constant strain εˢ, 3×3, F/m |
| `units` | Fixed: `{"rho":"kg/m^3","C":"Pa","e":"C/m^2","eps":"F/m"}` |

Compliance s, strain constants d, εᵀ, relative permittivity and complex matrices are not accepted; no constitutive conversion is performed. Import validates matrix shapes, finiteness, positive density, symmetry and positive definiteness of C and ε; electrodes and passive layers must have e = 0.

## Custom materials

Copy the JSON of a built-in record, change `id` (must start with `user_`), `version`, the constants, `source` and `reference_frame`, then

```bash
python -m sawsim.material_library import my_material.json
```

Alternatively give only the independent constants of the crystal class and let `sawsim materials --create` build and import the full tensors (isotropic, cubic, hexagonal_6mm, trigonal_3m; `sawsim materials --symmetries` lists the required constants, `--dry-run` validates without saving):

```bash
sawsim materials --create '{"id": "user_aln", "name": "AlN", "symmetry": "hexagonal_6mm",
  "constants": {"C11": 345, "C12": 125, "C13": 120, "C33": 395, "C44": 118,
                "e15": -0.48, "e31": -0.58, "e33": 1.55, "eps11": 9.21, "eps33": 10.12},
  "rho_kg_m3": 3260, "roles": ["substrate"], "source": "<literature source>"}'
```

Stiffness in GPa, e in C/m², relative permittivities; tensors are in crystal axes (Z = symmetry axis) and are oriented with the ZXZ Euler angles of the config. trigonal_3m uses the +C14, +e22 convention of `linbo3_bouchy_2022` (checked term by term in `tests/test_stack_materials.py`). Only the substrate may be piezoelectric.

Records are stored in `~/.sawsim/materials/` (override with `SAWSIM_MATERIALS_DIR`). The same id and version cannot be overwritten; bump the version instead. Reference them with `substrate_material="user_xxx"` or `layers=[{"material_id": "user_xxx", ...}]` in `Model`.

Every run writes the complete records it used into `material_snapshots` in `input.json` and their SHA-256 hashes into `material_snapshot.json`. Re-running a saved job uses the snapshot and does not depend on the library file still existing.

## Euler angle convention

Intrinsic ZXZ Euler angles (α, β, γ); the API fields are `euler_phi_deg`, `euler_theta_deg`, `euler_psi_deg` in that order, in degrees. The rotation matrix is

```
A = Rz(α) · Rx(β) · Rz(γ)
Rz(t) = [[cos t, −sin t, 0], [sin t, cos t, 0], [0, 0, 1]]
Rx(t) = [[1, 0, 0], [0, cos t, −sin t], [0, sin t, cos t]]
```

and maps components from the frame of the material record to the global device frame. Tensors transform as

```
C′ = M C Mᵀ      e′ = A e Mᵀ      ε′ = A ε Aᵀ
```

with M the Voigt stress transformation matrix of A (order xx, yy, zz, yz, xz, xy). This matches the "rotated coordinate system" definition of mainstream commercial FEM codes.

Defaults: 2D Q9 templates (0, −42, 0), Hex27 templates (0, 48, 0), TC-SAW (0, 0, 0). Each entry in `layers[]` may carry its own three angles, defaulting to 0. Isotropic materials are unaffected by the angles.

**Angles are relative to the frame of the selected material record** and do not map automatically onto named wafer cuts such as 128° YX. `linbo3_tc` is already pre-rotated into the device frame, so its angles are an additional rotation. When comparing with other software, align the source tensors, reference axes and polarisation direction first.

### Legacy convention

Before 0.6.0 the code used `A = Rz(−ψ) Rx(−θ) Rz(−φ)`; a legacy (φ, θ, ψ) corresponds to (−ψ, −θ, −φ) in the current convention. To import an old configuration set `"euler_convention": "legacy_zxz"` explicitly in the JSON; it is converted and saved in the current convention. New configurations can simply use `"euler_convention": "zxz"` (saved files record the field under a historical identifier, kept for compatibility).
