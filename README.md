<div align="center">

**中文** · [English](https://github.com/Duane245/sawsim/blob/main/README.en.md)

# SawSim

**声表面波（SAW）谐振器周期单元的压电耦合有限元求解器**
Piezoelectric coupled FEM for SAW resonator unit cells · Q9 / Hex27 · PML · Bloch periodicity

[![CI](https://github.com/Duane245/sawsim/actions/workflows/ci.yml/badge.svg)](https://github.com/Duane245/sawsim/actions/workflows/ci.yml)
[![DOI v2.0.0](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.22728471-1682D4?logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.22728471)
[![PyPI](https://img.shields.io/pypi/v/sawsim?logo=pypi&logoColor=white)](https://pypi.org/project/sawsim/)
[![Last commit](https://img.shields.io/github/last-commit/Duane245/sawsim)](https://github.com/Duane245/sawsim/commits/main)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

项目名 **SawSim**；Python 包名与命令名 `sawsim`。

</div>

---

## 最新动态

- **2.1.0（开发中，2026-10）**：面向 AI 代理的 JSON 命令行、使用说明与本地 MCP 服务（Claude Code、codex、Claude 桌面版、Cursor）；
  通用叠层 `sp_stack` 与按晶系常数自定义材料；压电层材料损耗（Rayleigh 刚度阻尼 + 介电损耗）与 Q 值。
- **2.0.2（2026-09）**：发布到 PyPI，`pip install sawsim`。

完整记录见 [CHANGELOG](https://github.com/Duane245/sawsim/blob/main/CHANGELOG.md)。

## 安装与使用

```bash
pip install sawsim
pip install "sawsim[fast]"     # 可选：MKL PARDISO 直接求解器
```

```python
from sawsim import Model, sweep

r = sweep(Model("sp_double_layer", pitch_um=1.085, points=101), "out/dbl")
r.frequency_ghz, r.admittance, r.peak_frequency_ghz
```

```bash
sawsim templates
sawsim run config.json -o out/dbl
```

**AI 代理**（Claude Code、codex 等）：每条命令都可输出 JSON，直接给出 fr、fa、k²eff 与警告。在**运行 AI 代理的那台机器**上、装有 sawsim 的同一 Python 环境里执行一次安装命令，然后新开一个会话，直接用自然语言提问即可（例如“用 sawsim 算一下 TC-SAW 的 fr 和 k²”）。

```bash
sawsim guide --install-claude                 # Claude Code：安装为 skill（~/.claude/skills/sawsim）
sawsim guide --install-codex                  # codex：写入全局指令 ~/.codex/AGENTS.md
sawsim guide                                  # 其他代理：打印完整说明
sawsim mcp --print-config claude-desktop     # MCP（Claude 桌面版、Cursor 等）：打印配置片段
sawsim locate '{"model_id": "sp_tcsaw"}'      # 自动定位谐振/反谐振并细扫
sawsim converge '{"model_id": "sp_tcsaw"}'    # 网格加密检查
```

无图形界面的 Linux 上 Gmsh 需要 `libglu1-mesa libopengl0`。详见 [快速开始](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.md)。

## 能力

| | |
|---|---|
| **模型** | 10 种周期单元模板：5 种 2D（Q9，含 TC-SAW）、4 种 2.5D 周期薄片（Hex27），以及通用叠层 `sp_stack`（0–6 背衬层 + 0–3 覆盖层） |
| **物理** | 位移–电势全耦合；ME0 平面应变或 ME1 面外位移扩展；各向异性单晶按内禀 ZXZ 欧拉角旋转 |
| **边界** | 左右 Bloch 周期边界，底部复坐标拉伸 PML |
| **网格** | Gmsh Python API 参数化建模，二次等参单元 |
| **求解** | 复数稀疏系统实分块，MKL PARDISO 或 SciPy SuperLU，频点多进程并行 |
| **输出** | Y11 导纳（CSV / NPZ / JSON）、网格、位移场与电势场图、材料快照与源码哈希，任务可完整复现 |
| **材料** | 内置 LiNbO₃（文献）、LiTaO₃ 型基准数据集、Si、SiO₂、poly-Si、Si₃N₄、Al、Cu；自定义 JSON 导入，或由晶系独立常数生成（各向同性 / 立方 / 6mm / 3m） |
| **损耗与 Q** | 压电层 Rayleigh 刚度阻尼 + 介电损耗（与参考有限元模型一致），自动解析谐振 / 反谐振品质因数 Q_r / Q_a |
| **AI 接口** | JSON 命令行（定位 fr/fa、网格收敛检查、参数扫描、出图）、Claude Code / codex 使用说明、本地 MCP 服务 |

## 验证

每个模板都与独立的参考有限元解比较：九个模板的谐振频率 fr 与反谐振频率 fa 与参考解相差均在 0.5 MHz 以内（多数小于 0.1 MHz）。无损模型的峰谷幅值对频率采样极其敏感，不作为精度指标。完整误差表、图和说明见 [验证](https://github.com/Duane245/sawsim/blob/main/docs/validation.md)。`pytest` 在 5 – 6 个频点上复现该比对。

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Duane245/sawsim/main/docs/figures/readme_validation_dark.png">
  <img alt="SawSim 与参考有限元解的比较" src="https://raw.githubusercontent.com/Duane245/sawsim/main/docs/figures/readme_validation_light.png" width="100%">
</picture>
<sub>左：TC-SAW 周期单元的导纳，SawSim（实线）与参考有限元解（圆点，每 4 个采样点显示 1 个）。右：九个模板的谐振与反谐振频率偏差。</sub>
</div>

## 文档

- [快速开始](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.md) — 安装、第一个算例、输出文件、单位
- [模型库](https://github.com/Duane245/sawsim/blob/main/docs/models.md) — 十种模板（含通用叠层）、参数、位移模型、边界、网格分辨率与已知限制
- [材料库与晶体取向](https://github.com/Duane245/sawsim/blob/main/docs/materials-and-orientation.md) — 内置材料、记录格式、自定义导入、ZXZ 欧拉角
- [验证](https://github.com/Duane245/sawsim/blob/main/docs/validation.md) — 谐振与反谐振频率与参考解的比对
- [用 AI 代理驱动 SawSim](https://github.com/Duane245/sawsim/blob/main/docs/ai-agents.md) — JSON 命令、输出字段、fr/fa 精度、代理验收结果

## 项目结构

```
src/sawsim/        Python 包（api、cli、agent、metrics、config、models、solver、saw2d、sp_meshes、sp_hex_meshes、material_library、skill）
examples/          AI 代理验收任务
tests/             回归与 API 测试，tests/data 为参考曲线
docs/              文档与图
matlab/            v0.x 的 MATLAB + Gmsh 实现（历史版本，MIT）
```

## 许可

Python 包 `sawsim`：**AGPL-3.0-or-later**；`matlab/` 目录：MIT。详见 [LICENSE.md](https://github.com/Duane245/sawsim/blob/main/LICENSE.md)。如需商业授权，请通过 GitHub 联系作者。

## 引用

作者：Shaoqing Duan。

引用具体版本请用版本 DOI（v2.0.0：[10.5281/zenodo.22728471](https://doi.org/10.5281/zenodo.22728471)）；引用项目整体请用概念 DOI [10.5281/zenodo.20362278](https://doi.org/10.5281/zenodo.20362278)，它始终指向最新版本。格式见 [CITATION.cff](https://github.com/Duane245/sawsim/blob/main/CITATION.cff)。

```bibtex
@software{duan_sawsim,
  author    = {Duan, Shaoqing},
  title     = {{SawSim: An open-source piezoelectric finite-element solver for SAW resonators}},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.20362278},
  url       = {https://github.com/Duane245/sawsim}
}
```

