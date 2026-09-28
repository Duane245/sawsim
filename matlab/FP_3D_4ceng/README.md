<div align="center">

# FP_3D_4ceng Demo

**自包含的 2.5D 有限器件 SAW 谐振器仿真 —— LT + Al + SiO₂ + Poly-Si + Si**

**简体中文** · [English](README.en.md)

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## 简介

自包含的 MATLAB 算例,模拟 2.5D **有限器件**(FP)SAW 谐振器:21 周期多指 IDT + 反射栅 + 27 节点六面体(Hex27)高阶单元;左右两侧采用悬浮电势端部边界,前后施加 Bloch 周期边界以等效模拟无限大孔径。叠层结构:**LiTaO₃ + Al + SiO₂ + Poly-Si + Si**;左 / 右 / 下方布置复坐标拉伸 PML 吸收外行波。

频域扫频输出 Y₁₁ 导纳曲线。

本 demo 与同系列其它 demo(`FP_3D_1ceng/` ~ `FP_3D_4ceng/`)共享同一套求解器核心,仅在叠层结构、pitch、扫频范围上差异。

---

## 运行

仓库采用共享的顶层 [`codes/`](../codes/) 与 [`mesh/`](../mesh/),驱动脚本会自动把它们加入 MATLAB 路径。

```bash
cd FP_3D_4ceng
matlab -batch "Solve3DSAW"
```

或在 MATLAB 交互会话中:

```matlab
cd FP_3D_4ceng
Solve3DSAW
```

**输出**

| 文件 / 图窗 | 内容 |
|---|---|
| `Y11.mat` | `fre`(301 个频点)、`Q`、`Y` |
| 图 1 | 网格(按材料分区) |
| 图 2 | 位移场 |
| 图 3 | 电势场 |
| 图 4 | Y₁₁ 导纳曲线 |

301 频点扫频在典型工作站上耗时 **约 1 小时**(单进程,无需 Parallel Computing Toolbox);Hex27 节点数 ≈ 67 K,内存峰值受网格规模影响。

---

## 几何与物理参数

| 项 | 值 |
|---|---|
| 叠层结构(衬底 → 上) | LiTaO₃ + Al + SiO₂ + Poly-Si + Si |
| 电极 | Al(21 周期多指 IDT) |
| 周期(pitch) | 1.0 µm |
| 单元 | Hex27(27 节点六面体高阶单元) |
| 边界 | 悬浮电势(左右端)+ Bloch 周期(前后) |
| 外围吸收 | PML(复坐标拉伸,左 / 右 / 下) |
| 扫频范围 | 1.80 – 2.10 GHz |
| 频点数 | 301 |
| 网格节点数 | ≈ 67 K |

---

## 网格生成

MATLAB 网格 `.m` 文件因体积较大且容易重生成,**未随仓库分发**。请通过 Gmsh `.py` 源脚本一次性生成:

```bash
# 需要 Gmsh (https://gmsh.info) 及带 gmsh 模块的 Python
python mesh/FP_3D_4ceng.py
# 该脚本输出 mesh/FP_3D_4ceng.m, 驱动脚本 Solve3DSAW.m 通过
#   FP_3D_4ceng;   % 调用该 .m 加载网格
```

如果运行机器上没有 Gmsh / Python,也可以在其它地方预先生成好 `FP_3D_4ceng.m` 再拷贝到 `mesh/` 目录。

---

## 文件结构

```
FP_3D_4ceng/
├── Solve3DSAW.m                      主驱动脚本(开头自动 addpath ../codes、../mesh)
├── initial_material_parameters.m     材料参数
├── initialPML.m                      PML 初始化(复坐标拉伸)
└── readmesh.m                        网格读取
```

(共享的顶层 [`codes/`](../codes/) 与 [`mesh/`](../mesh/),请见仓库根 README)

---

## 依赖

- MATLAB R2023a 或更高版本
- 无需任何附加 Toolbox(单进程顺序扫频)
- Gmsh + Python(一次性,仅用于重新生成 `.m` 网格,见上)

---

## 协议

基于 [MIT License](../LICENSE) 发布
