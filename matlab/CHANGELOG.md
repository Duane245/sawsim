# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与
[Semantic Versioning](https://semver.org/lang/zh-CN/) 规范。

## [Unreleased]

### Changed
- Renamed SAW-FEM-MATLAB to SawSim on 2026-09-05; updated project URLs and citation guidance.
- Preserved existing release tags, version numbers, and Zenodo DOIs; archived releases retain their original citation titles.

## [0.4.0] - 2026-06-10

### Added
- 第四批开源算例(共 4 个,FP-2.5D 系列有限器件):
  - `FP_3D_1ceng/` —— LiNbO₃ + Al, pitch 1.0 µm, 1.8–2.2 GHz, ~274 K 节点
  - `FP_3D_2ceng/` —— LiTaO₃ + Al + Si, pitch 1.085 µm, 1.75–2.0 GHz, ~87 K 节点
  - `FP_3D_3ceng/` —— + SiO₂ + Poly-Si 层, pitch 1.0 µm, 1.6–2.0 GHz, ~207 K 节点
  - `FP_3D_4ceng/` —— + Si 层(5 层叠层), pitch 1.0 µm, 1.8–2.1 GHz, ~67 K 节点
  - Hex27 高阶六面体单元、21 周期多指 IDT、悬浮电势端部边界 + Bloch 周期(前后)、复坐标拉伸 PML(左 / 右 / 下)
  - 单进程序列扫频,跑通命令 `matlab -batch "Solve3DSAW"`
- 4 个 Gmsh 网格生成脚本,按 demo 名命名:`mesh/FP_3D_<N>ceng.py`
- `codes/` 新增 3 个 FP 边界 helper:`Boundary_idx3DF.m`、`boundaryPeriodic1_3DF.m`、`findSAWBoundary3DF.m`

## [0.3.0] - 2026-06-04

### Added
- 第三批开源算例(共 4 个,SP-2.5D 系列周期单元):
  - `SP_3D_1ceng/` —— LiTaO₃ + Al, pitch 1.085 µm, 1.5–2.7 GHz, ~8 100 节点
  - `SP_3D_2ceng/` —— + Si 层, pitch 1.085 µm, 1.75–2.0 GHz, ~8 700 节点
  - `SP_3D_3ceng/` —— + SiO₂ + Poly-Si 层, pitch 1.085 µm, 1.6–2.0 GHz, ~9 500 节点
  - `SP_3D_4ceng/` —— + Si 层(4 层叠层), pitch 1.0 µm, 1.8–2.1 GHz, ~10 300 节点
  - Hex27 高阶六面体单元、Bloch 周期边界、复坐标拉伸 PML
  - 单进程序列扫频,跑通命令 `matlab -batch "Solve3DSAW"`
- 4 个 Gmsh 网格生成脚本,按 demo 名命名:`mesh/SP_3D_<N>ceng.py`
- `codes/` 新增 22 个 3D helper(Hex27 装配、形函数、PML、边界排序、3D 绘图)

## [0.2.0] - 2026-05-25

### Added
- 第二个开源算例 `FP_2D_TCSAW/` —— 温度补偿型 SAW(TC-SAW)二维**有限器件**模型
  - 21 周期多指 IDT,约 48 700 节点
  - LiNbO₃ 衬底 + SiO₂ / Si₃N₄ 温补层 + Al 叉指电极
  - Q9 单元、悬浮电势端部边界、复坐标拉伸 PML
  - 单进程序列扫频,跑通命令 `matlab -batch "SolveSAW"`

## [0.1.0] - 2026-05-24

### Added
- 首个开源算例 `2DTCSAW/` —— 温度补偿型 SAW (TC-SAW) 二维周期单元 demo
  - LiNbO₃ 衬底 + SiO₂ / Si₃N₄ 温补层 + Al 叉指电极
  - Q9 单元、Bloch 周期边界、复坐标拉伸 PML
  - 单进程序列扫频,跑通命令 `matlab -batch "SolveSAW"`
- MIT 许可证(`LICENSE`,© 2026 Shaoqing Duan)
- 项目主 README(英文)+ `README.zh-CN.md`(中文)
- 中英双语 demo README(`2DTCSAW/README.md`)

### Notes
- 仓库性质由"纯展示文档"扩展为"展示 + 可运行代码 demo"

[Unreleased]: https://github.com/Duane245/sawsim/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/Duane245/sawsim/releases/tag/v0.4.0
[0.3.0]: https://github.com/Duane245/sawsim/releases/tag/v0.3.0
[0.2.0]: https://github.com/Duane245/sawsim/releases/tag/v0.2.0
[0.1.0]: https://github.com/Duane245/sawsim/releases/tag/v0.1.0
