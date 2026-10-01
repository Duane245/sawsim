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
sawsim guide --install-codex      # add it to codex's global instructions (~/.codex/AGENTS.md)
```

- **Claude Code**: after installing the skill, just ask, e.g. "use sawsim to get fr and k² of a 600 nm 42°Y-X LT film bonded on Si".
- **codex**: `sawsim guide --install-codex` adds a short section to the global instructions `~/.codex/AGENTS.md` (or `$CODEX_HOME/AGENTS.md`), which codex reads at every start; re-running replaces only that section. Inside this repository codex also reads the repo's `AGENTS.md`.
- **other agents**: say "sawsim is installed, run `sawsim guide` first".
- Without the skill it still works: the first line of `sawsim --help` tells agents to run `sawsim guide`.

## Commands

| command | purpose |
|---|---|
| `sawsim templates --json` | templates: dimension, layer count, supported ME modes, default band |
| `sawsim schema <model_id>` | defaults, allowed ranges and meaning of every field |
| `sawsim materials` | material library (with reference frames) and the ZXZ Euler convention; `--show ID` full record, `--create` builds + imports a material from crystal constants, `--import` a complete record |
| `sawsim validate <cfg>` | check without running; on failure also returns the template's allowed values |
| `sawsim run <cfg> --json` | one sweep exactly as configured, with metrics |
| `sawsim locate <cfg>` | coarse sweep → widen the band if fr/fa are outside → 101-point zoom around fr–fa; **use this for fr/fa/k²** |
| `sawsim converge <cfg>` | rerun with half the mesh size, report the fr/fa shift (MHz, ppm) |
| `sawsim scan <cfg> --param P --values a,b,c [--locate]` | parameter scan, table of fr/fa/k² |
| `sawsim compare <result dir> <reference.csv/npz>` | fr/fa deviation from a reference \|Y\| curve |
| `sawsim summarize <result dir> [--curve]` | re-extract metrics from an existing result; `--curve` adds the sampled admittance arrays |
| `sawsim plot <dirs or reference files>... -o fig.png` | overlay admittance curves in one figure with fr (dashed) and fa (dotted) marked; the legend shows the config fields that differ; reference CSV / npz can be added |

`<cfg>` is a JSON file path or inline JSON starting with `{`; `--set key=value` overrides one field.
Exit code 0 = success, 1 = `"ok": false` with `error`/`errors` in the JSON. Progress goes to stderr only.

Runs are cached by config hash in `$SAWSIM_RUNS_DIR` (default `./sawsim_runs`); an identical config returns immediately.

## MCP server (local)

`sawsim mcp` is a local MCP server shipped with the package: the AI client starts it as a subprocess on this
machine (stdio); nothing is uploaded and everything is computed locally; unit-cell models only (no HCT). It suits
clients without a terminal (Claude Desktop, Cursor) and also works with Claude Code / codex.

| client | configuration |
|---|---|
| Claude Code | `claude mcp add sawsim -- sawsim mcp` |
| Claude Desktop | add the snippet printed by `sawsim mcp --print-config claude-desktop` to `claude_desktop_config.json` |
| codex | add the snippet printed by `sawsim mcp --print-config codex` to `~/.codex/config.toml` |
| others (Cursor, …) | command `sawsim`, args `mcp` (stdio) |

`--print-config` writes the absolute path of the sawsim executable so the client always finds it (needed on Windows).
For long computations raise the client's tool timeout to a few minutes (codex: `tool_timeout_sec`).

Tools: `get_guide`, `list_templates`, `describe_template`, `list_materials`, `show_material`, `create_material`,
`validate_config`, `run_sweep`, `locate_resonance`, `check_convergence`, `scan_parameter`, `summarize_result`,
`plot_curves` (returns the image), `compare_with_reference` — one-to-one with the JSON commands above. Results are
cached in `$SAWSIM_RUNS_DIR` (default `~/.sawsim/runs`); figures go to `~/.sawsim/plots/` by default.

## Loss and Q

Lossless by default. Loss follows the reference FEM models and acts **on the piezoelectric layer (and its PML) only**;
electrodes and other layers stay lossless (2D templates; 2.5D not yet):
- `beta_dk` (s): Rayleigh stiffness damping, K_uu → K_uu(1 + i·beta_dk·ω), β_dK of the reference models (mass damping 0); the equivalent
  loss factor grows linearly with frequency;
- `eta_eps`: dielectric loss, ε → ε(1 − i·eta_eps), η_εS of the reference models.

Values in the reference models: TC-SAW β_dK = 1e-13, η_εS = 1.5e-3; IHP-SAW β_dK = 3e-14, η_εS = 1.5e-3.
With loss, `locate` adds narrow sweeps around fr and fa until the linewidth is resolved by ~40 samples and reports `q_r`
(3 dB width of |Y|²) and `q_a` (|Z|²), with the half-power interpolation bias removed by Richardson extrapolation; fr/fa are
refined to the peaks; lossless runs report Q as null. `converge` also reports the relative Q change. The admittance uses
the passive sign (Re Y ≥ 0).

Example: `sp_tcsaw` defaults with beta_dk = 1e-13, eta_eps = 1.5e-3 give Q_r = 1639.2, Q_a = 1651.8; a 401-point
brute-force sweep gives Q_r = 1639.1. This Q contains material loss and substrate radiation only — no electrode resistance,
finite aperture, bus bars or package.

## Generic stacks and custom materials

- **`sp_stack`**: 0–6 backing `layers` under the piezo layer, 0–3 `coatings` over the electrodes, pitch 0.1–20 µm, 0.02–20 GHz.
  Configured as the five 2D templates, its fr/fa agree with them within 0.1 MHz and with the independent reference within 0.5 MHz (see [Models](models.en.md#mesh-resolution)).
- **Custom materials**: `sawsim materials --create` takes the independent constants of a crystal class (isotropic / cubic / hexagonal_6mm / trigonal_3m), builds, validates and imports the full tensors;
  agents must cite the constants in `source`. Only the substrate may be piezoelectric.
- **Weak coupling**: resonances are detected on |Y|/f (the static-capacitance slope removed) and `locate` densifies until fr–fa is resolved, so materials such as AlN (k² ≈ 0.1 %) are found too.

## Output fields

| field | meaning |
|---|---|
| `fr_ghz`, `fa_ghz` | \|Y\| maximum and the following minimum, refined between samples by a V-fit |
| `k2eff` | π²/4 · (fa − fr)/fa (a fraction, not %) |
| `uncertainty_mhz` | half the frequency step, conservative; the V-fit is usually much better |
| `modes` | other in-band peaks (e.g. a Rayleigh spurious next to the SH main mode) |
| `warnings` | `peak_at_band_edge`, `antiresonance_not_found`, `coarse_sampling`, `multiple_modes` |
| `next_steps` | suggestions derived from the warnings |
| `artifacts` | paths of Y11.png, mesh plot, displacement/potential field plots, admittance.csv (frequency, Re, Im, \|Y\|) |
| `coarse` (`locate` only) | the full-band coarse sweep (directory and band); the top-level result is the zoom around fr–fa |
| `q_r`, `q_a` | 3 dB quality factors at fr / fa; given by `locate` when loss is set, null for lossless runs |

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
- **MCP acceptance (2026-10-01)**: codex solved A1, B2, B3 through the `sawsim mcp` tools only (no sawsim command in its shell):
  26 tool calls, 16 min; it called `get_guide` first, hit the B2 target in 3 secant steps (0.97304 um, +0.09 MHz) and answered B3
  (+0.30 pp) with a `plot_curves` figure. The original A1 wording ("SiO2 721.44 nm over the electrodes") was ambiguous: the main answer
  used "above the electrode top" (fr 1.75227 GHz) and also reported the "from the piezo surface" reading, 1.75879 GHz (0.12 MHz from
  the reference); the task text is now explicit. Finite Q values from dense sweeps of the lossless model are no longer reported.

