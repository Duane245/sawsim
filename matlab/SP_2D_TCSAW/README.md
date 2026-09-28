<div align="center">

# SP 2D TCSAW Demo

**自包含的 2D 单周期(Bloch)温度补偿型 SAW(TC-SAW)仿真**

**简体中文** · [English](README.en.md)

![MATLAB](https://img.shields.io/badge/MATLAB-R2023a%2B-EE6B27?logo=mathworks&logoColor=white)
![Method](https://img.shields.io/badge/Method-Piezoelectric%20FEM%20%2B%20PML-555555)
![License](https://img.shields.io/badge/License-MIT-blue)

</div>

---

## 简介

自包含的 MATLAB 算例,模拟**单周期**(SP)二维温度补偿型 SAW 谐振器:单个 IDT 周期,左右施加 Bloch 周期边界,等效模拟无限长周期叉指阵列。衬底为 LiNbO₃,上叠 SiO₂ / Si₃N₄ 温补层与 Al 叉指电极;底部布置复坐标拉伸 PML 吸收外行波。

**有限器件**(FP)版本(端部为悬浮电势电极)请见 [`../FP_2D_TCSAW/`](../FP_2D_TCSAW/)。

---

## 运行

仓库采用共享的顶层 [`codes/`](../codes/) 与 [`mesh/`](../mesh/),驱动脚本会自动把它们加入 MATLAB 路径。

```bash
cd SP_2D_TCSAW
matlab -batch "SolveSAW"
```

或在 MATLAB 交互会话中:

```matlab
cd SP_2D_TCSAW
SolveSAW
```

**输出**

| 文件 / 图窗 | 内容 |
|---|---|
| `Y11.mat` | `fre`(201 频点)、`Q`、`Y` |
| 图 1 | 网格(按材料分区) |
| 图 2 | 位移场 |
| 图 3 | 电势场 |
| 图 4 | Y₁₁ 导纳曲线 |

201 频点扫频在典型工作站上耗时 **约 4 – 5 分钟**(单进程,无需 Parallel Computing Toolbox)。

---

## 几何与物理参数

| 项 | 值 |
|---|---|
| 压电衬底 | LiNbO₃ |
| 温补叠层 | SiO₂ + Si₃N₄ |
| 电极 | Al(单个 IDT 周期) |
| 周期(pitch) | 1.9936 µm |
| 单元 | Q9(9 节点四边形) |
| 左右边界 | Bloch 周期 |
| 底部边界 | PML(复坐标拉伸) |
| 扫频范围 | 1.60 – 2.00 GHz |
| 频点数 | 201 |
| 网格节点数 | 约 12 500 |

---

## 网格生成

MATLAB 网格 `.m` 文件因体积较大且容易重生成,**未随仓库分发**。请通过 Gmsh 的 `.py` 源脚本一次性生成:

```bash
# 需要 Gmsh (https://gmsh.info) 及带 gmsh 模块的 Python
python mesh/SAW-PeriodBC1_TC_1.py
# 该脚本输出 mesh/SAW_PeriodBC1_TC.m, 驱动脚本里 SolveSAW.m 通过
#   SAW_PeriodBC1_TC;   % 调用该 .m 加载网格
```

如果运行机器上没有 Gmsh / Python,也可以在其它地方预先生成好 `SAW_PeriodBC1_TC.m` 再拷贝到 `mesh/` 目录。

---

## 文件结构

```
SP_2D_TCSAW/
├── SolveSAW.m                          主驱动脚本
├── initial_material_parameters.m       材料参数(LiNbO3 / Al / SiO2 / Si3N4)
├── initialPML.m                        PML 初始化(复坐标拉伸)
├── readGmsh.m                          网格读取
└── findSAWBoundary.m                   边界节点识别

(共享的顶层 codes/ 和 mesh/,请见仓库根 README)
```

---

## 依赖

- MATLAB R2023a 或更高版本
- 无需任何附加 Toolbox(单进程顺序扫频)
- Gmsh + Python(一次性,仅用于重新生成 `.m` 网格,见上)

---

## 协议

基于 [MIT License](../LICENSE) 发布
