<div align="center">

**中文** · [English](https://github.com/Duane245/sawsim/blob/main/README.en.md)

# SawSim

**声表面波（SAW）谐振器周期单元的压电耦合有限元求解器**
Piezoelectric coupled FEM for SAW resonator unit cells · Q9 / Hex27 · PML · Bloch periodicity

[![CI](https://github.com/Duane245/sawsim/actions/workflows/ci.yml/badge.svg)](https://github.com/Duane245/sawsim/actions/workflows/ci.yml)
[![DOI v2.0.0](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.22728471-1682D4?logo=zenodo&logoColor=white)](https://doi.org/10.5281/zenodo.22728471)
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

项目名 **SawSim**；Python 包名与命令名 `sawsim`；在线服务 sawsim.com 即将开放。

</div>

---

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

无图形界面的 Linux 上 Gmsh 需要 `libglu1-mesa libopengl0`。详见 [快速开始](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.md)。

## 能力

| | |
|---|---|
| **模型** | 9 种周期单元模板：5 种 2D（Q9，含 TC-SAW）与 4 种 2.5D 周期薄片（Hex27），单层至四层叠层 |
| **物理** | 位移–电势全耦合；ME0 平面应变或 ME1 面外位移扩展；各向异性单晶按内禀 ZXZ 欧拉角旋转 |
| **边界** | 左右 Bloch 周期边界，底部复坐标拉伸 PML |
| **网格** | Gmsh Python API 参数化建模，二次等参单元 |
| **求解** | 复数稀疏系统实分块，MKL PARDISO 或 SciPy SuperLU，频点多进程并行 |
| **输出** | Y11 导纳（CSV / NPZ / JSON）、网格、位移场与电势场图、材料快照与源码哈希，任务可完整复现 |
| **材料** | 内置 LiNbO₃（文献）、Si、SiO₂、poly-Si、Si₃N₄、Al、Cu；自定义 JSON 导入 |

## 验证

每个模板与独立的参考有限元解逐点比对；主谐振与反谐振频率全部一致，主谐振区误差 0.1 – 2 %，2D 多层模板在 2.4 GHz 以上高阶模态区存在偏差。完整误差表、图和说明见 [验证](https://github.com/Duane245/sawsim/blob/main/docs/validation.md)。`pytest` 在 5 – 6 个频点上复现该比对。

<div align="center">
<img src="https://raw.githubusercontent.com/Duane245/sawsim/main/docs/figures/compare_2p5d_double.png" width="640"><br>
<sub>2.5D SP 双层（LiNbO₃ 0.6 µm / Si 6.51 µm），251 频点。虚线 sawsim，实线参考解，幅值相对 L2 误差 0.15 %。</sub>
</div>

## 文档

- [快速开始](https://github.com/Duane245/sawsim/blob/main/docs/getting-started.md) — 安装、第一个算例、输出文件、单位
- [模型库](https://github.com/Duane245/sawsim/blob/main/docs/models.md) — 九种模板、参数、位移模型、边界与已知限制
- [材料库与晶体取向](https://github.com/Duane245/sawsim/blob/main/docs/materials-and-orientation.md) — 内置材料、记录格式、自定义导入、ZXZ 欧拉角
- [验证](https://github.com/Duane245/sawsim/blob/main/docs/validation.md) — 与参考解的逐点比对及解读

## 项目结构

```
src/sawsim/        Python 包（api、cli、config、models、solver、saw2d、sp_meshes、sp_hex_meshes、material_library）
tests/             回归与 API 测试，tests/data 为参考曲线
docs/              文档与图
matlab/            v0.x 的 MATLAB + Gmsh 实现（历史版本，MIT）
tools/             维护脚本
```

## 许可

Python 包 `sawsim` 以 **AGPL-3.0-or-later** 发布（它通过 Python API 链接 GPL 许可的 Gmsh）。`matlab/` 下的历史 MATLAB 实现保持 MIT。其他授权方式请联系作者。

## 引用

引用具体版本请用版本 DOI（v2.0.0：[10.5281/zenodo.22728471](https://doi.org/10.5281/zenodo.22728471)）；引用项目整体请用概念 DOI [10.5281/zenodo.20362278](https://doi.org/10.5281/zenodo.20362278)，它始终指向最新版本。格式见 [CITATION.cff](https://github.com/Duane245/sawsim/blob/main/CITATION.cff)。

