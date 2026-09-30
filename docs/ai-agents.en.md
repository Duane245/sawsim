[中文](https://github.com/Duane245/sawsim/blob/main/docs/ai-agents.md) · **English**

# Driving SawSim with AI agents

Since 2.1, SawSim has a command-line interface for AI coding agents (Claude Code, codex, …).
Every command prints exactly one JSON object on stdout with the resonance fr, antiresonance fa,
k²eff, warnings and suggested next steps. An agent can set up a model, run it, tune parameters
and check mesh convergence without reading Python source or parsing curve files.

## Install

```bash
pip install sawsim
sawsim guide                      # print the agent guide (workflow, fields, pitfalls)
sawsim guide --install-claude     # install it as a Claude Code skill (~/.claude/skills/sawsim/SKILL.md)
```

- **Claude Code**: after installing the skill, just ask, e.g. "use sawsim to get fr and k² of a 600 nm 42°Y-X LT film bonded on Si".
- **codex and other agents**: say "sawsim is installed, run `sawsim guide` first"; inside this repository they also read `AGENTS.md`.
- Without the skill it still works: the first line of `sawsim --help` tells agents to run `sawsim guide`.

## Commands

| command | purpose |
|---|---|
| `sawsim templates --json` | templates: dimension, layer count, supported ME modes, default band |
| `sawsim schema <model_id>` | defaults, allowed ranges and meaning of every field |
| `sawsim materials` | material library (with reference frames) and the ZXZ Euler convention |
| `sawsim validate <cfg>` | check without running; on failure also returns the template's allowed values |
| `sawsim run <cfg> --json` | one sweep exactly as configured, with metrics |
| `sawsim locate <cfg>` | coarse sweep → widen the band if fr/fa are outside → 101-point zoom around fr–fa; **use this for fr/fa/k²** |
| `sawsim converge <cfg>` | rerun with half the mesh size, report the fr/fa shift (MHz, ppm) |
| `sawsim scan <cfg> --param P --values a,b,c [--locate]` | parameter scan, table of fr/fa/k² |
| `sawsim compare <result dir> <reference.csv/npz>` | fr/fa deviation from a reference \|Y\| curve |
| `sawsim summarize <result dir>` | re-extract metrics from an existing result |

`<cfg>` is a JSON file path or inline JSON starting with `{`; `--set key=value` overrides one field.
Exit code 0 = success, 1 = `"ok": false` with `error`/`errors` in the JSON. Progress goes to stderr only.

Runs are cached by config hash in `$SAWSIM_RUNS_DIR` (default `./sawsim_runs`); an identical config returns immediately.

## Output fields

| field | meaning |
|---|---|
| `fr_ghz`, `fa_ghz` | \|Y\| maximum and the following minimum, refined between samples by a V-fit |
| `k2eff` | π²/4 · (fa − fr)/fa (a fraction, not %), same as the web UI |
| `uncertainty_mhz` | half the frequency step, conservative; the V-fit is usually much better |
| `modes` | other in-band peaks (e.g. a Rayleigh spurious next to the SH main mode) |
| `warnings` | `peak_at_band_edge`, `antiresonance_not_found`, `coarse_sampling`, `multiple_modes` |
| `next_steps` | suggestions derived from the warnings |
| `artifacts` | paths of Y11.png, mesh plot, displacement/potential field plots, admittance.csv |
| `q_r`, `q_a` | always null: the solver model is lossless, resonances are poles |

## Accuracy

fr/fa extracted with `sawsim.metrics` from the validation data (`tests/data/`), deviation from the independent reference FEM:

| template | reference fr / fa (GHz) | Δfr / Δfa (MHz) |
|---|---|---|
| sp_single_layer | 1.80791 / 1.87557 | −0.06 / 0.00 |
| sp_double_layer | 1.82363 / 1.90406 | 0.00 / 0.00 |
| sp_triple_layer | 1.75860 / 1.84383 | −0.45 / −0.43 |
| sp_quad_layer | 1.75859 / 1.84382 | 0.00 / 0.00 |
| sp_tcsaw | 1.75891 / 1.81852 | −0.09 / −0.16 |
| sp_2p5d_single_layer | 1.80791 / 1.87554 | −0.08 / −0.03 |
| sp_2p5d_double_layer | 1.84441 / 1.92538 | 0.00 / −0.01 |
| sp_2p5d_triple_layer | 1.75820 / 1.84342 | 0.00 / −0.01 |
| sp_2p5d_quad_layer | 1.89841 / 1.98725 | +0.04 / +0.06 |

The reference curves have a 1–2 MHz frequency step; `tests/test_agent.py` uses 1 MHz as the regression bound.

## Agent acceptance (2026-09-30, sawsim 2.1.0)

The six prompts of [`examples/agent_tasks.md`](https://github.com/Duane245/sawsim/blob/main/examples/agent_tasks.md) were given verbatim to two
agents, saying only "sawsim is installed" - no field names, no reference results. Both started from `sawsim --help` and found `sawsim guide` themselves.

| task | content | graded against | codex (gpt-6-astra) | Claude Code (Opus) |
|---|---|---|---|---|
| A1 | reproduce a TC-SAW reference model from an engineering description | reference fr/fa 1.75891 / 1.81852 GHz | 1.75882 / 1.81833 ✓ | 1.7588 / 1.8183 ✓ |
| A2 | reproduce LT film / Si | 1.82363 / 1.90406 | 1.82307 / 1.90365 ✓ | 1.8231 / 1.9037 ✓ |
| A3 | reproduce IHP-SAW four-layer | 1.75859 / 1.84382 | 1.75813 / 1.84347 ✓ | 1.7581 / 1.8435 ✓ |
| B1 | default single-layer fr/fa/k² | 1.80777 / 1.87557, 8.92 % | 1.80779 / 1.87559, 8.92 % ✓ | 1.8078 / 1.8756, 8.92 % ✓ |
| B2 | tune pitch to fr = 1.7975 GHz ± 2 MHz | hidden answer 0.9731 um | 0.97307 um, +0.04 MHz ✓ | 0.97304 um, +0.09 MHz ✓ |
| B3 | k² difference, metal ratio 0.4 vs 0.6, and mesh-convergence verdict | +0.29 pp, mesh error <= 0.03 | +0.30, significant ✓ | +0.30, significant ✓ |

- Both agents solved 6/6 (pass: fr/fa within 2 MHz), ran mesh-refinement checks unprompted, and handled the traps: the pre-rotated TC-SAW dataset (Euler 0), ME0 for TC-SAW, and the two poly-Si records (template default chosen).
- codex: 9.4 min, ~70 sawsim calls. Claude (remote over ssh): 16 min, 25 calls. Both reached the B2 target in 3 secant steps.
- In A2/A3, refining the mesh from 0.5 to 0.25 um moves fr by ~0.5 MHz; the deviations above include that.
- Issues the agents raised were fixed or documented: a cache race between concurrent identical runs (fixed, with a test); the TC-SAW SiO2 thickness is measured from the piezo surface; the 2D templates' bottom PML uses the piezo material; `converge` clamps the mesh to the template minimum.

