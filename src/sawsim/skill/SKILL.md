---
name: sawsim
description: Simulate SAW (surface acoustic wave) resonator unit cells with the SawSim finite-element package - resonance fr, antiresonance fa, coupling k2eff, admittance curves, parameter scans, mesh-convergence checks, and reproducing a reference model from its inputs. Use when the user asks about SAW / TC-SAW / IHP-SAW resonator frequencies, coupling, pitch or metal-ratio design, layer stacks on LiTaO3/LiNbO3, or wants to run `sawsim`.
---

# SawSim for agents

SawSim solves the coupled piezoelectric FEM of **one periodic IDT cell** (infinite periodic
resonator, lossless) and returns the admittance Y(f). Finite-length devices (reflectors,
aperture, bus bars, HCT) are **not** in this package - say so if asked.

Every command below prints exactly one JSON object on stdout (progress on stderr); exit code 1
means `"ok": false` with an `error`/`errors` field. Runs are cached by config hash under
`$SAWSIM_RUNS_DIR` (default `./sawsim_runs`), so repeating a config is free.

## Workflow

1. `sawsim templates --json` - pick the template that matches the stack (table below).
2. `sawsim schema <model_id>` - defaults, allowed ranges, field meanings. Start from the
   defaults and change only what the task specifies.
3. `sawsim validate '<json>'` - fix every error; the reply lists `allowed` values.
4. `sawsim locate '<json>'` - coarse sweep, widens the band if fr/fa are outside it, then a
   zoomed 101-point sweep around fr..fa. **Use this for any fr/fa/k2 answer.** (~15 s for 2D)
5. `sawsim converge '<json>'` - repeats locate at mesh_um/2 and reports the fr/fa shift.
   Do this before claiming a result is accurate or when comparing designs that differ by
   less than ~1 MHz. The refined mesh is clamped to the template minimum (e.g. sp_tcsaw
   0.1 -> 0.08 um), so the default call always works. To resolve differences smaller than
   `uncertainty_mhz`, `run` a denser sweep (e.g. 401 points over fr-5 MHz..fa+5 MHz).
6. Report fr, fa (GHz), k2eff (%), the uncertainty, the mesh check, and any `warnings`.

Other commands: `sawsim run '<json>' --json` (one sweep exactly as configured),
`sawsim scan '<json>' --param pitch_um --values 1.0,1.05,1.1 [--locate]`,
`sawsim summarize <dir> [--curve]` (`--curve` adds the sampled Y arrays),
`sawsim compare <dir> <reference.csv|npz>` (fr/fa deviation vs a reference curve; CSV columns
f,|Y| or f,Re,Im), `sawsim materials`.

**Admittance curves / figures.** Every result directory holds `admittance.csv`
(frequency_hz, real_y, imag_y, abs_y), `curve.json` and `Y11.png`. To show the user curves,
make one overlay figure (fr dashed, fa dotted, legend = the config fields that differ):

```bash
sawsim plot <dir1> <dir2> [reference.csv] -o compare.png [--quantity abs|db|real|imag] [--labels a,b,c]
```

`locate` returns the **zoom** around fr..fa; the full-band curve is `coarse.output_dir`
(plot both to show the whole response and the resolved resonance).
Config can be a file path or inline JSON; `--set key=value` overrides one field.

## Output fields

`fr_ghz`, `fa_ghz` (V-fit between samples), `k2eff` = pi^2/4 (fa-fr)/fa (fraction, not %),
`uncertainty_mhz` (half the frequency step - conservative; the V-fit is usually much better),
`modes` (other in-band peaks), `warnings`, `next_steps`, `artifacts` (Y11.png, field plots,
admittance.csv), `dofs`, `output_dir`. `q_r`/`q_a` are null: the model is lossless.

Warnings to act on: `peak_at_band_edge` (move/widen band), `antiresonance_not_found`
(raise stop_ghz), `coarse_sampling` (use locate), `no_resonance_found` (weak coupling:
more points - locate does this), `stronger_response_at_band_edge` (a stronger mode may sit
just outside the band), `multiple_modes` (check you are reading the intended mode - e.g. a
Rayleigh spurious next to the SH main mode). The main mode is the strongest resonance
(largest |Y|/f peak with a deep fr->fa dip), so weakly coupled materials (AlN, k2 ~0.1-1 %)
are found too; `locate` keeps zooming until fr..fa is resolved.

## Templates

| model_id | stack (top -> bottom) | mode |
|---|---|---|
| sp_single_layer | electrodes / thick piezo substrate | ME1 |
| sp_double_layer | electrodes / thin piezo film (substrate_um) / Si | ME1 |
| sp_triple_layer | electrodes / piezo film / SiO2 / poly-Si | ME1 |
| sp_quad_layer | electrodes / piezo film / SiO2 / poly-Si / Si (IHP-SAW) | ME1 |
| sp_tcsaw | SiN / SiO2 overcoat / Cu electrodes / LiNbO3 (TC-SAW) | ME0 only |
| sp_2p5d_*_layer | same stacks as 3D Hex27 slab, needs aperture_um; minutes per run | ME1 only |
| **sp_stack** | any: 0-3 `coatings` / electrodes / piezo layer / 0-6 backing `layers` | ME0 or ME1 |

`layers` order: the layers **below** the piezo layer, top to bottom (sp_tcsaw only: its two
coatings, SiO2 then SiN). Fixed count per template; sp_stack takes 0-6. `coatings` (sp_stack
only): 0-3 layers above the electrodes, inner to outer. `substrate_um` is always the
thickness of the piezo layer. Only the substrate may be piezoelectric; layers and coatings
must be non-piezoelectric (isotropic or anisotropic elastic + dielectric).

**Which template?** Use a named template when the stack matches it (validated against an
independent reference). Use `sp_stack` for anything else - other layer counts, coatings on
any stack, custom materials, pitch 0.1-20 um, 0.02-20 GHz. sp_stack reproduces the five 2D
templates' fr/fa (see docs/ai-agents.md); its PML sits under the lowest layer and uses that
layer's material. With `linbo3_tc` as substrate it uses the TC-SAW xz convention (ME0 only).
Its mesh is structured: element size = mesh_um within 2 x pitch of the surface, coarser deeper;
start at mesh_um ~ pitch/4 and run `converge`.

Geometry conventions: the cell is two electrodes wide (2 x pitch, one + and one - finger);
electrode width = metal_ratio x pitch. In sp_tcsaw the SiO2 thickness is measured **from the
piezo surface** (it embeds the electrodes, so SiO2 above the electrode top = SiO2 - electrode_um);
if a user gives the overcoat thickness above the electrodes, add electrode_um and say so.
In the named 2D templates the bottom PML uses the main piezo material, also under Si backings;
in 2.5D and sp_stack it uses the lowest backing material (see `notes` in `sawsim schema`).
Independent sweeps may run in parallel; identical configs share one cached result safely.

## Pitfalls (read before mapping a user's description)

- **Mode**: `mode_extension` 1 keeps the out-of-plane displacement (needed for SH / leaky
  modes on rotated-Y LiTaO3); 0 is in-plane only (Rayleigh). sp_tcsaw accepts only 0.
- **Materials**: `sawsim materials` lists ids with `reference_frame`. `sp_baseline` +
  default Euler (0, -42, 0) is the package's 42°Y-X LiTaO3-type setup (rho = 7450).
  `linbo3_tc` is **already rotated** into the TC-SAW device frame: keep Euler (0, 0, 0) -
  do not rotate it again for "128°Y-X". `linbo3_bouchy_2022` is a literature crystal-frame
  LiNbO3 (needs explicit Euler angles). Electrode/overlay materials are isotropic.
- **Cut names -> Euler angles**: conventions differ between tools, and the legacy datasets'
  crystal frames are not independently verified. Prefer the template default angles when the
  user names the cut the template was built for, and report the result as "per the template's
  cut convention"; if you must convert, state the ZXZ angles you used as an assumption
  (intrinsic ZXZ, degrees, see `materials`).
- **Units**: lengths in um, frequencies in GHz. Admittance is per unit aperture (S/m) in 2D;
  for 2.5D multiply by the slab width to get S. fr/fa/k2 are unaffected.
- `electrode_um` = electrode thickness; electrode width = metal_ratio x pitch.
  Resonance scales roughly as 1/pitch - use that to seed pitch searches.
- Ranges are template-limited (e.g. pitch 0.8-1.5 um, metal_ratio 0.3-0.7); if a target
  needs values outside, report it rather than silently clamping.
- A unit-cell fr/fa is the infinite-periodic resonance; real devices shift slightly.

## Custom materials

If a material is not in `sawsim materials`, create it from literature constants:

```bash
sawsim materials --symmetries            # accepted crystal classes + an example spec
sawsim materials --create spec.json      # build full tensors, validate, import (add --dry-run to test)
sawsim materials --show user_aln         # full record
```

Spec: `id` (must start with `user_`), `name`, `symmetry` (isotropic: E_gpa, nu, eps_r;
cubic: C11, C12, C44, eps_r; hexagonal_6mm: C11 C12 C13 C33 C44 e15 e31 e33 eps11 eps33;
trigonal_3m: + C14, e22), `constants` (stiffness in GPa, e in C/m^2, relative permittivity),
`rho_kg_m3`, `roles` (`substrate` for piezoelectric; `layer`/`electrode` need e = 0),
`source` (**cite where every constant comes from**). Tensors are in crystal axes (Z = c axis);
orient with the ZXZ Euler angles in the config (substrate: euler_*_deg; layers: per-layer
euler_*_deg). Records are immutable: to change one, create a new id or `version`.
`--import record.json` takes a complete record (C_pa/e_c_m2/eps_f_m in SI, as `--show` prints).
Sign conventions differ between sources (e.g. e22, C14); state the source convention you used.

## Reproducing a reference model

Given a description (materials, thicknesses, cut, pitch, metal ratio, band) of a model
computed elsewhere: map it to a template (table above), put every given number in the
config, keep the rest at template defaults and **list which defaults you kept**; run
`locate` + `converge`; if a reference curve is available use `sawsim compare`. Judge
agreement by fr/fa deviation in MHz/ppm, not by |Y| amplitude (amplitudes of a lossless
model near the poles are not comparable).

## Design example: hit a target fr

```bash
sawsim locate '{"model_id":"sp_tcsaw"}'            # fr0 at pitch p0
# p1 = p0 * fr0 / f_target ; locate again; 1-2 more secant steps reach +/-0.5 MHz
sawsim locate '{"model_id":"sp_tcsaw","pitch_um":0.9875}'
```
