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
`sawsim summarize <dir>`, `sawsim compare <dir> <reference.csv|npz>` (fr/fa deviation vs a
reference |Y| curve; CSV columns f_hz,|Y|), `sawsim materials`.
Config can be a file path or inline JSON; `--set key=value` overrides one field.

## Output fields

`fr_ghz`, `fa_ghz` (V-fit between samples), `k2eff` = pi^2/4 (fa-fr)/fa (fraction, not %),
`uncertainty_mhz` (half the frequency step - conservative; the V-fit is usually much better),
`modes` (other in-band peaks), `warnings`, `next_steps`, `artifacts` (Y11.png, field plots,
admittance.csv), `dofs`, `output_dir`. `q_r`/`q_a` are null: the model is lossless.

Warnings to act on: `peak_at_band_edge` (move/widen band), `antiresonance_not_found`
(raise stop_ghz), `coarse_sampling` (use locate), `multiple_modes` (check you are
reading the intended mode - e.g. a Rayleigh spurious next to the SH main mode).

## Templates

| model_id | stack (top -> bottom) | mode |
|---|---|---|
| sp_single_layer | electrodes / thick piezo substrate | ME1 |
| sp_double_layer | electrodes / thin piezo film (substrate_um) / Si | ME1 |
| sp_triple_layer | electrodes / piezo film / SiO2 / poly-Si | ME1 |
| sp_quad_layer | electrodes / piezo film / SiO2 / poly-Si / Si (IHP-SAW) | ME1 |
| sp_tcsaw | SiN / SiO2 overcoat / Cu electrodes / LiNbO3 (TC-SAW) | ME0 only |
| sp_2p5d_*_layer | same stacks as 3D Hex27 slab, needs aperture_um; minutes per run | ME1 only |

`layers` order: for backed templates, the layers **below** the piezo film, top to bottom; for
sp_tcsaw, the coatings from the electrode side outwards (SiO2 first, then SiN). The layer
count is fixed by the template. `substrate_um` is always the thickness of the piezo layer.

Geometry conventions: the cell is two electrodes wide (2 x pitch, one + and one - finger);
electrode width = metal_ratio x pitch. In sp_tcsaw the SiO2 thickness is measured **from the
piezo surface** (it embeds the electrodes, so SiO2 above the electrode top = SiO2 - electrode_um);
if a user gives the overcoat thickness above the electrodes, add electrode_um and say so.
In the 2D templates the bottom PML uses the main piezo material, also under Si backings; in
2.5D it uses the lowest backing material (see `notes` in `sawsim schema`).
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
