**中文** · [English](getting-started.en.md)

# 快速开始

## 安装

```bash
pip install sawsim      # 开发版：pip install git+https://github.com/Duane245/sawsim
pip install "sawsim[fast]"                                # 可选：pypardiso（MKL PARDISO 直接求解器）
```

要求 Python ≥ 3.8。依赖 numpy、scipy、matplotlib、gmsh、pydantic 会自动安装。

**无图形界面的 Linux**（服务器、CI、Docker）上 Gmsh 需要两个系统库：

```bash
sudo apt install libglu1-mesa libopengl0        # Debian / Ubuntu
```

没有 root 权限时，把包含 `libGLU.so.1`、`libOpenGL.so.0` 的目录写进环境变量 `SAWSIM_VENDOR_LIB_DIR`。

## 第一个算例

```python
from sawsim import Model, sweep

m = Model("sp_double_layer", pitch_um=1.085, electrode_um=0.17, points=101)
r = sweep(m, "out/double_layer")

r.frequency_ghz          # (101,) 频率
r.admittance             # (101,) 复数导纳 Y11
r.magnitude              # |Y11|
r.peak_frequency_ghz     # 采样点上的 |Y| 最大值对应频率
```

命令行等价写法：

```bash
sawsim templates                              # 列出 9 种模板
sawsim run config.json -o out/double_layer    # config.json 见下
```

```json
{"model_id": "sp_double_layer", "pitch_um": 1.085, "electrode_um": 0.17, "points": 101}
```

未给出的参数取模板默认值。`Model.templates()` 或 `sawsim templates` 列出模板 id；每个模板的默认几何、频段和层结构见 [模型库](models.md)。

## 输出目录

| 文件 | 内容 |
|---|---|
| `input.json` | 完整有效输入，含材料快照，可直接重算 |
| `curve.json`, `admittance.csv`, `admittance.npz` | 频率、Y11 实部/虚部/幅值 |
| `metadata.json` | 节点数、自由度、峰频、耗时、求解器后端、版本与源码哈希 |
| `mesh.npz`, `mesh.png` | 网格与网格图 |
| `fields.npz`, `disp_field.png`, `phi_field.png` | 峰频处的位移场与电势场 |
| `material_snapshot.json`, `material_data.npz` | 所用材料记录、哈希、旋转矩阵与旋转后张量 |
| `manifest.json` | 工件清单 |

只想检查几何时用 `sweep(m, "out/x", mesh_only=True)` 或 `sawsim run --mesh-only`。

## 单位约定

- 长度输入单位 µm，频率 GHz；内部与输出文件一律 SI。
- **2D 模板**（Q9）：导纳按单位面外孔径给出，单位 S/m。
- **2.5D 模板**（Hex27 周期薄片）：`curve.json` 的主曲线同样按孔径归一化为 S/m；`admittance.npz` 中的 `raw_admittance_s` 为薄片总导纳（S），`aperture_m` 为薄片宽度。与其他软件比较总导纳时用 `raw_admittance_s`，或用 `magnitude × aperture_m`。

## 进度回调与并行

```python
def on_progress(event):            # {'stage','completed','total','elapsed_seconds',...}
    print(event["stage"], event["completed"], "/", event["total"])

sweep(m, "out/x", on_progress=on_progress)
```

频点数大于 41 时扫频按频点多进程并行（默认最多 8 个进程，`SAW_SWEEP_WORKERS` 可调）；每个进程 BLAS 单线程。装了 pypardiso 时使用 MKL PARDISO，否则回退 SciPy SuperLU，两者结果相对差约 1e-4。

## 自定义材料

内置材料只读。自定义记录默认保存到 `~/.sawsim/materials/`（`SAWSIM_MATERIALS_DIR` 可改），格式与导入方法见 [材料库与晶体取向](materials-and-orientation.md)。
