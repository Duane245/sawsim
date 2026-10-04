<div align="center">

# FP 2D TCSAW Demo

**自包含的 2D 有限器件温度补偿型 SAW(TC-SAW)仿真**

**简体中文** · [English](README.en.md)

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## 简介

自包含的 MATLAB 算例,模拟**有限长度**的二维温度补偿型 SAW 谐振器:LiNbO₃ 衬底 + SiO₂ / Si₃N₄ 温补叠层 + Al 多指叉指电极。相比 [`SP_2D_TCSAW/`](../SP_2D_TCSAW/) 那个周期单元算例,本算例直接对**整个器件**(21 个 IDT 周期,约 48 700 节点)建模 —— 左右两端为悬浮电势电极,底部布置复坐标拉伸 PML,与真实芯片版图一一对应。

频域扫频输出 Y₁₁ 导纳曲线。

---

## 运行

```bash
cd FP_2D_TCSAW
matlab -batch "SolveSAW"
```

或在 MATLAB 交互会话中:

```matlab
cd FP_2D_TCSAW
SolveSAW
```

**输出**

| 文件 / 图窗 | 内容 |
|---|---|
| `Y11.mat` | `fre`(201 个频点)、`Q`、`Y` |
| 图 1 | 网格(按材料分区上色) |
| 图 2 | 位移场 |
| 图 3 | 电势场 |
| 图 4 | Y₁₁ 导纳曲线 |

201 频点扫频在典型工作站上耗时 **约 30 – 60 分钟**(单进程,无需 Parallel Computing Toolbox);48 700 节点的网格内存峰值约 6 – 8 GB。

---

## 几何与物理参数

| 项 | 值 |
|---|---|
| 压电衬底 | LiNbO₃ |
| 温补叠层 | SiO₂ + Si₃N₄ |
| 电极 | Al 多指叉指(IDT) |
| IDT 周期数 | 21 |
| 周期(pitch) | 1.9936 µm |
| 孔径(器件长度) | 41.866 µm |
| 单元 | Q9(9 节点四边形) |
| 左右边界 | 自由 + 端部悬浮电势电极(XFL / XFR) |
| 底部边界 | PML(复坐标拉伸) |
| PML 厚度 | 1.9936 µm |
| 扫频范围 | 1.60 – 2.00 GHz |
| 频点数 | 201 |
| 网格节点数 | 约 48 700 |

---

## SP-2D vs FP-2D — 该用哪个?

| 维度 | [`SP_2D_TCSAW/`](../SP_2D_TCSAW/)(SP) | `FP_2D_TCSAW/`(FP,本算例) |
|---|---|---|
| 几何 | 单个 IDT 周期 | 完整 21 周期器件 |
| 左右边界 | Bloch 周期 | 自由 + 悬浮电势电极 |
| 网格规模 | 约 12 500 节点 | 约 48 700 节点 |
| 扫频耗时 | 约 4 – 5 分钟 | 约 30 – 60 分钟 |
| 关注点 | 周期本征模态特征 | 真实器件响应,含端部反射 / 杂散模 |

**SP 适合** 设计空间快速扫描;**FP 适合** 与实测芯片对照。

---

## 文件结构

```
FP_2D_TCSAW/
├── SolveSAW.m                          主驱动脚本
├── initial_material_parameters.m       材料参数(LiNbO3 / Al / SiO2 / Si3N4)
├── initialPML.m                        PML 初始化(复坐标拉伸)
├── readGmsh.m                          网格读取
├── codes/                              求解器核心
│   ├── AssemblyKM2D.m                      K / M 装配入口
│   ├── boundary_idx_2DF.m                  FP 边界索引
│   ├── findSAWBoundary2DF.m                悬浮电势边节点识别
│   ├── forces.m / solution.m               载荷向量 / 线性求解
│   ├── formStiffnessMass2D*.m              压电耦合分块(uu / φφ / uφ)
│   ├── formStiffnessMass2DPML*.m           PML 区域装配(复坐标拉伸)
│   ├── gaussQuadrature.m                   Gauss 积分
│   ├── shapeFunctionsQ2D.m                 Q9 形函数
│   ├── Jacobian.m                          Jacobian 工具
│   ├── oulaTransfer.m                      晶体张量欧拉角旋转
│   ├── ComputingC2D.m                      刚度张量构造
│   └── plot_*.m  /  plotY11.m              可视化辅助
└── mesh/
    ├── SAW_TC_PML3.m                       MATLAB 网格(由下方 .py 生成)
    └── SAW_TC_PML3.py                      Gmsh 参数化几何脚本
```

---

## 依赖

- MATLAB R2023a 或更高版本
- 无需任何附加 Toolbox(单进程顺序扫频)
- 仓库直接附带 MATLAB 网格 `.m` 文件;若要从 `.py` 重新生成,需要 [Gmsh](https://gmsh.info) 和 Python

---

## 方法

- **未知场** `[u₁, u₂, φ]`(位移 + 电势)经压电本构关系耦合
- **装配** `K` 与 `M` 采用 `[u | φ]` 分块形式
- **端部电极** 左右两端模拟为**悬浮电势**等势体(对系统矩阵相应的行 / 列求和,以约束等电位而无需指定电压值)
- **PML** 通过复坐标拉伸 `α = 1 + d/(iω)` 实现,沿多项式衰减廓线 `d` 吸收外行波;在扫频上限 `ω = 2π · fre(end)` 处固定
- **扫频** 在每个频点求解 `(-ω²M + K) x = f`,然后由信号电极感应电荷 `Q` 计算 `Y₁₁ = |iωQ/V|`

---

## 引用

如本算例对你有帮助,欢迎引用本仓库:

[SawSim citation guide / 引用指南](../CITING.md)

---

## 协议

基于 [MIT License](../LICENSE) 发布
