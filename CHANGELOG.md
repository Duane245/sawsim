# Changelog / 更新记录

Key user-facing changes per release. / 各版本的关键更新。

## 2.1.0 (unreleased / 开发中)

**AI agents / AI 代理**
- JSON command line for AI coding agents: `schema`, `materials`, `validate`, `locate` (bracket and resolve fr/fa),
  `converge` (mesh check), `scan`, `plot` (overlay curves, fr/fa marked), `compare`, `summarize [--curve]`;
  results cached by config hash.<br>
  面向 AI 代理的 JSON 命令行：模板与材料查询、配置校验、`locate`（自动定位并细扫 fr/fa）、`converge`（网格收敛检查）、
  参数扫描、`plot`（多曲线叠加并标出 fr/fa）、与参考曲线比较、`summarize [--curve]`；相同配置的结果自动缓存。
- `sawsim guide` with `--install-claude` (Claude Code skill) and `--install-codex` (codex global AGENTS.md).<br>
  `sawsim guide` 使用说明，`--install-claude` 安装为 Claude Code skill，`--install-codex` 写入 codex 全局指令。
- Local MCP server `sawsim mcp` (stdio, 14 tools) for Claude Desktop, Cursor, Claude Code and codex;
  `--print-config` prints the client snippet.<br>
  本地 MCP 服务 `sawsim mcp`（14 个工具），支持 Claude 桌面版、Cursor、Claude Code、codex；`--print-config` 打印客户端配置。

**Models and physics / 模型与物理**
- Generic 2D stack `sp_stack`: 0–6 backing layers and 0–3 coatings, structured Q9 mesh; reproduces the five 2D
  templates' fr/fa within 0.1 MHz.<br>
  通用二维叠层 `sp_stack`：0–6 层背衬 + 0–3 层覆盖，结构化 Q9 网格；与五个二维模板的 fr/fa 相差 ≤ 0.1 MHz。
- Custom materials from crystal-class constants (isotropic, cubic, 6mm, 3m): `sawsim materials --create`.<br>
  由晶系独立常数（各向同性、立方、6mm、3m）生成自定义材料：`sawsim materials --create`。
- Material loss as in the reference FEM models, on the piezoelectric layer and its PML: Rayleigh stiffness damping
  `beta_dk` and dielectric loss `eta_eps`; `locate` resolves Q_r / Q_a.<br>
  与参考有限元模型一致的材料损耗，作用于压电层及其 PML：Rayleigh 刚度阻尼 `beta_dk` 与介电损耗 `eta_eps`；`locate` 给出 Q_r / Q_a。
- At least 8 second-order elements per wavelength laterally in every template.<br>
  所有模板横向每个波长至少 8 个二阶单元。

**Changed / 行为变化**
- Admittance now uses the passive sign (Re Y ≥ 0); magnitudes are unchanged.<br>
  导纳正负号改为通用约定（电导 Re Y ≥ 0），幅值 |Y| 不变。
- Resonance detection works on |Y|/f, so weakly coupled materials (e.g. AlN) are found.<br>
  谐振识别改用 |Y|/f，弱耦合材料（如 AlN）也能定位。

## 2.0.2

- PyPI release (`pip install sawsim`).<br>
  发布到 PyPI（`pip install sawsim`）。
