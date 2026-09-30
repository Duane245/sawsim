**中文** · [English](materials-and-orientation.en.md)

# 材料库与晶体取向

## 内置材料

| id | 名称 | 角色 | 状态 | 说明 |
|---|---|---|---|---|
| `linbo3_bouchy_2022` | LiNbO₃ · Bouchy 2022（25 °C） | 压电基板 | literature | Bouchy et al., *Materials* 2022, 15, 4716（DOI 10.3390/ma15134716）。完整 Cᴱ / e / εˢ / ρ，室温、实部无损近似，测量频段 20 Hz – 20 MHz |
| `linbo3_tc` | LiNbO₃ · TC-SAW 数据集 | 压电基板 | legacy | 完整张量，ρ = 4628 kg/m³。数据已在参考器件坐标系中（预旋转） |
| `sp_baseline` | 压电基板 · 基准数据集 I | 压电基板 | legacy | 完整张量，ρ = 7450 kg/m³（与 LiTaO₃ 相符）。晶体身份未经独立核实 |
| `al`, `al_hex35` | Al 铝（ν = 0.33 / 0.35） | 电极 | legacy | E = 70 GPa，ρ = 2700 kg/m³ |
| `cu` | Cu 铜 | 电极 | legacy | E = 120 GPa，ν = 0.34，ρ = 8960 kg/m³ |
| `si_isotropic` | Si 硅 · 各向同性近似 | 功能层 | legacy | E = 170 GPa，ν = 0.28，ρ = 2329 kg/m³，εr = 11.7 |
| `si_cubic_hex` | Si 硅 · 立方各向异性 | 功能层 | legacy | C11 = 166、C12 = 64、C44 = 80 GPa，εr = 11.68 |
| `si_aniso_hex` | Si 硅 · 各向异性全张量 | 功能层 | legacy | 完整 6×6 刚度，εr = 11.8 |
| `polysi`, `polysi_160` | Poly-Si 多晶硅（E = 169 / 160 GPa） | 功能层 | legacy | ν = 0.22，ρ = 2320 kg/m³，εr = 4.5 |
| `sio2` | SiO₂ 二氧化硅 | 功能层 | legacy | E = 70 GPa，ν = 0.17，ρ = 2200 kg/m³，εr = 4.2 |
| `sin` | Si₃N₄ 氮化硅 | 功能层 | legacy | E = 160 GPa，ν = 0.23，ρ = 3100 kg/m³，εr = 9.7 |

`legacy` 表示常用工程参数，原始文献与测量条件未逐条核实；`literature` 表示全部常数取自同一篇文献并注明表号。**`sp_baseline` 的密度对应 LiTaO₃ 而非 LiNbO₃**，在确认身份前请把它当作一个基准数据集而不是某种具体晶体。

内置记录只读。列出与查看：

```bash
python -m sawsim.material_library list
python -m sawsim.material_library show linbo3_bouchy_2022 --version 1.0.0
```

## 记录格式

每条记录是一个 JSON 文件，字段：

| 字段 | 含义 |
|---|---|
| `id`, `version`, `name`, `description` | 标识与说明；`version` 为语义化版本 |
| `roles` | `substrate` / `electrode` / `layer` 的子集 |
| `status` | `literature` / `legacy` / `user` |
| `source`, `reference_frame`, `temperature_k`, `symmetry` | 来源、张量所在坐标系、温度、对称性 |
| `constitutive` | 固定 `stress_charge`（应力–电荷形式） |
| `voigt_order` | 固定 `xx,yy,zz,yz,xz,xy`，工程剪切应变 |
| `rho_kg_m3` | 密度 |
| `C_pa` | 恒电场刚度 Cᴱ，6×6，Pa |
| `e_c_m2` | 压电应力矩阵 e，3×6，C/m² |
| `eps_f_m` | 恒应变绝对介电率 εˢ，3×3，F/m |
| `units` | 固定 `{"rho":"kg/m^3","C":"Pa","e":"C/m^2","eps":"F/m"}` |

不接受柔顺 s、应变常数 d、εᵀ、相对介电率或复数矩阵，不做本构形式转换。导入时校验矩阵尺寸、有限数值、正密度、C 与 ε 的对称性和正定性；电极和无源功能层要求 e = 0。

## 自定义材料

复制一条内置记录的 JSON，改 `id`（必须以 `user_` 开头）、`version`、常数、`source` 与 `reference_frame`，然后：

```bash
python -m sawsim.material_library import my_material.json
```

也可以只给晶系的独立常数，由 `sawsim materials --create` 生成完整张量并导入（支持 isotropic、cubic、hexagonal_6mm、trigonal_3m；`sawsim materials --symmetries` 列出所需常数，`--dry-run` 只校验不保存）：

```bash
sawsim materials --create '{"id": "user_aln", "name": "AlN", "symmetry": "hexagonal_6mm",
  "constants": {"C11": 345, "C12": 125, "C13": 120, "C33": 395, "C44": 118,
                "e15": -0.48, "e31": -0.58, "e33": 1.55, "eps11": 9.21, "eps33": 10.12},
  "rho_kg_m3": 3260, "roles": ["substrate"], "source": "<文献出处>"}'
```

刚度单位 GPa，e 单位 C/m²，介电为相对值；张量在晶轴坐标系（Z 为对称轴），取向用配置里的 ZXZ 欧拉角。trigonal_3m 采用 +C14、+e22 约定，与 `linbo3_bouchy_2022` 一致（`tests/test_stack_materials.py` 逐项核对）。只有衬底可以是压电材料。

记录保存到 `~/.sawsim/materials/`（环境变量 `SAWSIM_MATERIALS_DIR` 可改）。同 id 同版本不能覆盖，修改请升版本。在 `Model` 中通过 `substrate_material="user_xxx"` 或 `layers=[{"material_id": "user_xxx", ...}]` 引用。

每个任务把所用材料的完整记录写入 `input.json` 的 `material_snapshots`，并在 `material_snapshot.json` 记录 SHA-256 哈希。重算历史任务时用快照，不依赖库中文件是否仍存在。

## 欧拉角约定

采用内禀 ZXZ 欧拉角 (α, β, γ)，API 字段依次为 `euler_phi_deg`、`euler_theta_deg`、`euler_psi_deg`，单位度。旋转矩阵

```
A = Rz(α) · Rx(β) · Rz(γ)
Rz(t) = [[cos t, −sin t, 0], [sin t, cos t, 0], [0, 0, 1]]
Rx(t) = [[1, 0, 0], [0, cos t, −sin t], [0, sin t, cos t]]
```

把材料记录所在参考系的分量映射到器件全局坐标。张量变换为

```
C′ = M C Mᵀ      e′ = A e Mᵀ      ε′ = A ε Aᵀ
```

其中 M 为 A 对应的 Voigt 应力变换矩阵（顺序 xx, yy, zz, yz, xz, xy）。该约定与主流商业有限元软件的"旋转坐标系"定义一致。

默认角度：2D Q9 模板 (0, −42, 0)，Hex27 模板 (0, 48, 0)，TC-SAW (0, 0, 0)。`layers[]` 中每层可单独给出三个角度，缺省为 0。各向同性材料不受角度影响。

**角度是相对所选材料记录的参考系而言的**，不自动对应任何命名的晶圆切型（如 128° YX）。`linbo3_tc` 已经在器件坐标系中预旋转，其欧拉角是附加旋转。与其他软件对比时须先对齐原始张量、参考轴和极化方向。

### 历史约定

0.6.0 之前使用 `A = Rz(−ψ) Rx(−θ) Rz(−φ)`。旧配置的 (φ, θ, ψ) 对应新约定的 (−ψ, −θ, −φ)。导入旧配置时在 JSON 中显式写 `"euler_convention": "legacy_zxz"`，程序会自动换算并保存为当前约定。新配置写 `"euler_convention": "zxz"` 即可（保存的文件中该字段以历史标识符记录，属兼容保留）。
