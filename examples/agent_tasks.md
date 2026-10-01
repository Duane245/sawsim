# AI agent tasks / AI 代理验收任务

Prompts to give an AI coding agent (Claude Code, codex, …) that has `sawsim` installed.
Give each prompt verbatim; do not mention sawsim field names. Grading is by fr/fa deviation
from an independent reference or a hidden answer (see `docs/ai-agents.md`).

把下列题目原样交给装好 `sawsim` 的 AI 代理，不提示内部字段名。

## A. Reproduce a reference model / 复现参考模型

**A1 TC-SAW**
> 用 sawsim 计算一个温度补偿型 SAW 谐振器的周期单元：LiNbO₃ 衬底（TC-SAW 常用的 128°Y-X 切，厚 15.9488 µm），
> Cu 电极厚 166.33 nm，电极周期 0.9968 µm，金属化比 0.46；表面覆盖 SiO₂（自压电表面起算总厚 721.44 nm，包埋电极），其上再覆盖 SiN 40 nm。
> 给出谐振频率 fr、反谐振频率 fa 和 k²eff，并说明你做了哪些假设。

**A2 LiTaO₃ thin film on Si / 键合薄膜**
> 用 sawsim 计算：42°Y-X LiTaO₃ 压电薄膜 600 nm 键合在 8.33 µm 硅（各向同性近似）上，Al 电极厚 170 nm，
> 周期 1.085 µm，金属化比 0.5。给出 fr、fa、k²eff，并说明假设。

**A3 IHP-SAW four-layer / 四层 IHP-SAW**
> 用 sawsim 计算 IHP-SAW 周期单元：42°Y-X LiTaO₃ 600 nm / SiO₂ 500 nm / 多晶硅 1 µm / Si 7.83 µm，
> Al 电极厚 170 nm，周期 1.085 µm，金属化比 0.5。给出 fr、fa、k²eff，并说明假设。

## B. Design / 设计

**B1**
> 用 sawsim 的单层模板、全部默认参数，谐振频率 fr、反谐振频率 fa 和 k²eff 分别是多少？

**B2**
> 用 sawsim 的 TC-SAW 模板，除电极周期外其余参数保持默认，调整周期使谐振频率 fr = 1.7975 GHz（误差 ±2 MHz）。
> 给出周期和最终的 fr。

**B3**
> 用 sawsim 的单层模板，比较金属化比 0.4 和 0.6 两个设计的 k²eff，差多少？这个差异是否明显大于数值（网格）误差？
