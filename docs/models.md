**中文** · [English](models.en.md)

# 模型库

十种周期单元（SP, single period）模板，其中 `sp_stack` 为任意层数的通用二维叠层。层数指主压电层及其下方承载层，不含电极与 PML；长度单位 µm。

| 模板 id | 单元 / 维度 | 默认叠层（自表面向下） | 位移模型 | 默认频段 GHz |
|---|---|---|---|---|
| `sp_single_layer` | Q9 · 2D | 压电层 8 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_double_layer` | Q9 · 2D | 压电层 0.6 / Si 8.33 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_triple_layer` | Q9 · 2D | 压电层 0.6 / SiO₂ 0.5 / poly-Si 6.9 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_quad_layer` | Q9 · 2D | 压电层 0.6 / SiO₂ 0.5 / poly-Si 1 / Si 7.83 | ME0 / ME1 | 1.5 – 2.7 |
| `sp_tcsaw` | Q9 · 2D | LiNbO₃ 15.95；表面 SiO₂ 0.72 与 SiN 0.04 温度补偿层 | ME0 | 1.6 – 2.0 |
| `sp_2p5d_single_layer` | Hex27 · 周期薄片 | 压电层 6.51 | ME1 | 1.5 – 2.7 |
| `sp_2p5d_double_layer` | Hex27 · 周期薄片 | 压电层 0.6 / Si 6.51 | ME1 | 1.75 – 2.0 |
| `sp_2p5d_triple_layer` | Hex27 · 周期薄片 | 压电层 0.6 / SiO₂ 0.5 / poly-Si 6.51 | ME1 | 1.6 – 2.0 |
| `sp_2p5d_quad_layer` | Hex27 · 周期薄片 | 压电层 0.6 / SiO₂ 0.5 / poly-Si 1 / Si 6 | ME1 | 1.8 – 2.1 |
| `sp_stack` | Q9 · 2D（结构化） | 电极上 0–3 覆盖层；压电层；其下 0–6 背衬层（默认同单层） | ME0 / ME1 | 1.5 – 2.7（允许 0.02 – 20） |

## 输入参数

| 字段 | 含义 | 默认 |
|---|---|---|
| `pitch_um` | 叉指周期（周期单元宽度为 2 × pitch） | 1.085（TC-SAW 0.9968） |
| `electrode_um` | 电极厚度 | 0.17 |
| `metal_ratio` | 金属化比 | 0.5 |
| `substrate_um` | 主压电层厚度（TC-SAW 为压电体总深度） | 模板决定 |
| `layers` | `[{material_id, thickness_um, euler_phi/theta/psi_deg}]`，2D 多层为承载层自上而下，TC-SAW 为包覆层自内而外 | 模板决定 |
| `coatings` | 仅 `sp_stack`：电极上方的覆盖层，自内而外；第一层从压电表面起算并包埋电极，须厚于电极 | `[]` |
| `mesh_um` | 网格控制尺寸 | 0.5（TC 0.1，Hex27 0.2 – 0.217） |
| `start_ghz`, `stop_ghz`, `points` | 频段与频点数（3 – 401） | 模板决定，41 点 |
| `voltage` | 激励电压 | 1 |
| `beta_dk`, `eta_eps` | 损耗（二维模板，仅压电层，与参考有限元模型一致；PML 为压电材料时随之带损耗）：Rayleigh 刚度阻尼 K_uu(1 + i·beta_dk·ω)，介电损耗 ε(1 − i·eta_eps) | 0（无损） |
| `mode_extension` | 0 = ME0，1 = ME1 | 1（TC-SAW 仅 0） |
| `substrate_material`, `electrode_material` | 材料 id | `sp_baseline`, `al`（TC：`linbo3_tc`, `cu`） |
| `euler_phi_deg`, `euler_theta_deg`, `euler_psi_deg` | 主压电层 ZXZ 欧拉角 | 见材料文档 |
| `aperture_um` | 仅 Hex27：周期薄片的 y 向宽度 | 0.217（四层 0.25） |

超出范围的值会在构造 `Model` 时被拒绝并给出中文提示。

## 位移模型

- **ME0** 平面应变：未知量 (u<sub>x</sub>, u<sub>y</sub>, φ)，u<sub>z</sub> = 0，E<sub>z</sub> = 0。先旋转完整张量，再取 Voigt [xx, yy, xy] 与电场 [x, y] 分量。
- **ME1** 面外位移扩展：未知量 (u<sub>x</sub>, u<sub>y</sub>, u<sub>z</sub>, φ)，∂/∂z = 0，面外波数为零。
- **TC-SAW** 源张量位于 xz 平面，二维计算取 [x, z] 投影后映射到网格 [x, y]，元数据中记录该映射。

## 边界与 PML

- 左右为 Bloch 周期边界（零相位），等效无限周期阵列；Hex27 前后也施加周期约束。
- 底部为复坐标拉伸 PML；2D 模板 PML 厚度为 2 × pitch（TC-SAW 4 × pitch）。
- `sp_stack` 的 PML 厚 2 × pitch，材料取最下层背衬（无背衬时取压电材料）。
- 所有模板（2D 与 Hex27）的 PML 均延续最底层材料：多层结构取最下层背衬，单层与 TC-SAW 取压电衬底，与参考模型一致；记录于 `metadata.json`。

## 网格分辨率

- 横向（沿传播方向）每个波长 λ = 2 × pitch 至少 8 个二阶单元（Q9；Hex27 同样满足），在每个模板允许的最粗 `mesh_um` 下也成立，`tests/test_stack_materials.py` 逐模板检查。
- `sp_stack` 为结构化网格：横向按电极边缘分 8 段，每段 ⌈宽度/mesh_um⌉ 个单元；纵向在表面以下 2 × pitch 内单元高度 = `mesh_um`，更深处放宽到 max(mesh_um, min(4·mesh_um, pitch/2))，PML 至少 8 层。
- 与五个二维模板相同叠层的比对（`converge` 细网格结果 vs 独立参考解）：

| 对照模板 | 参考 fr / fa (GHz) | 原模板 Δfr / Δfa (MHz) | sp_stack Δfr / Δfa (MHz) | sp_stack − 原模板 (MHz) | DoF 原模板 / sp_stack |
|---|---|---|---|---|---|
| sp_single_layer | 1.80791 / 1.87557 | −0.13 / +0.03 | −0.17 / −0.07 | −0.04 / −0.09 | 25028 / 7668 |
| sp_double_layer | 1.82362 / 1.90406 | −0.55 / −0.42 | −0.50 / −0.37 | +0.05 / +0.05 | 22596 / 8460 |
| sp_triple_layer | 1.75860 / 1.84384 | −0.44 / −0.31 | −0.44 / −0.36 | 0.00 / −0.05 | 25700 / 7932 |
| sp_quad_layer | 1.75859 / 1.84382 | −0.46 / −0.34 | −0.44 / −0.37 | +0.02 / −0.03 | 24708 / 8988 |
| sp_tcsaw | 1.75891 / 1.81852 | −0.10 / −0.19 | −0.04 / −0.16 | +0.06 / +0.03 | 59805 / 73425 |

## 已知限制

- 2.5D Hex27 内核的 γ<sub>yz</sub> 应变项缺少 ∂u<sub>z</sub>/∂y，为保持与原始数值可对照而保留，已在元数据标注；不应据此推断通用三维精度。
- Hex27 组装前限制最多 2000 个体单元、30000 节点，超过时报错并提示放粗网格。
- `sp_triple_layer` 的 fr/fa 比参考解低约 0.45 MHz，2.4 GHz 以上高阶模态的峰值也有偏差，原因尚在核查；`sp_2p5d_single_layer` 在 1.93 – 2.2 GHz 有小幅波动。见 [验证](validation.md)。
