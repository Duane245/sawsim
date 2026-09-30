**中文** · [English](https://github.com/Duane245/sawsim/blob/main/docs/ai-agents.en.md)

# 用 AI 代理驱动 SawSim

SawSim 2.1 起为 AI 编程代理（Claude Code、codex 等）提供了一套命令行接口：每条命令只在 stdout 输出一个 JSON 对象，
直接给出谐振频率 fr、反谐振频率 fa、k²eff、警告和下一步建议。代理不需要读 Python 源码或解析曲线文件，
就能完成建模、计算、调参和收敛检查。

## 安装

```bash
pip install sawsim
sawsim guide                      # 打印给 AI 的使用说明（流程、字段、易错点）
sawsim guide --install-claude     # 安装为 Claude Code skill（~/.claude/skills/sawsim/SKILL.md）
```

- **Claude Code**：安装 skill 后，直接用自然语言提问，例如“用 sawsim 算一下 42°Y-X LT 薄膜 600 nm 键合在硅上的 fr 和 k²”。
- **codex 等其他代理**：告诉它“已安装 sawsim，先运行 `sawsim guide`”即可；在本仓库内工作时会读取 `AGENTS.md`。
- 不装 skill 也能用：`sawsim --help` 第一行就提示代理先运行 `sawsim guide`。

## 命令

| 命令 | 作用 |
|---|---|
| `sawsim templates --json` | 模板列表：维度、层数、支持的 ME 模式、默认频带 |
| `sawsim schema <model_id>` | 某模板的默认值、取值范围、每个字段的含义 |
| `sawsim materials` | 材料库（含参考坐标系说明）与 ZXZ 欧拉角约定；`--show ID` 完整记录，`--create` 由晶系常数生成并导入新材料，`--import` 导入完整记录 |
| `sawsim validate <cfg>` | 只校验不计算；失败时同时返回该模板允许的取值 |
| `sawsim run <cfg> --json` | 按配置算一次扫频并返回指标 |
| `sawsim locate <cfg>` | 粗扫 → 频带不含 fr/fa 时自动扩展 → 在 fr–fa 附近 101 点细扫；**求 fr/fa/k² 用它** |
| `sawsim converge <cfg>` | 网格尺寸减半重算，报告 fr/fa 的移动量（MHz、ppm） |
| `sawsim scan <cfg> --param P --values a,b,c [--locate]` | 参数扫描，返回 fr/fa/k² 表 |
| `sawsim compare <结果目录> <参考.csv/npz>` | 与参考 \|Y\| 曲线比较 fr/fa 偏差 |
| `sawsim summarize <结果目录>` | 对已有结果重新提取指标 |

`<cfg>` 可以是 JSON 文件路径，也可以是以 `{` 开头的内联 JSON；`--set key=value` 覆盖单个字段。
退出码 0 表示成功，1 表示 JSON 里 `"ok": false` 并附 `error`/`errors`。进度信息只写 stderr。

结果按配置哈希缓存在 `$SAWSIM_RUNS_DIR`（默认 `./sawsim_runs`），重复提交相同配置直接返回，不重算。

## 通用叠层与自定义材料

- **`sp_stack`**：压电层下 0–6 层背衬（`layers`），电极上 0–3 层覆盖（`coatings`），节距 0.1–20 µm、频率 0.02–20 GHz。
  与五个二维模板配出相同叠层时，fr/fa 与原模板相差 ≤ 0.1 MHz，与独立参考解相差 ≤ 0.5 MHz（见 [模型库](models.md#网格分辨率)）。
- **自定义材料**：`sawsim materials --create` 接受晶系独立常数（isotropic / cubic / hexagonal_6mm / trigonal_3m），生成完整张量、校验后导入；
  代理必须在 `source` 中写明常数出处。只有衬底可以是压电材料。
- **弱耦合**：谐振识别基于 |Y|/f（去掉静电容的线性背景），`locate` 会在 fr–fa 未分辨时自动加密，AlN 这类 k² ≈ 0.1 % 的材料也能定位。

## 输出字段

| 字段 | 含义 |
|---|---|
| `fr_ghz`, `fa_ghz` | \|Y\| 最大点与其后的最小点，采样点之间用 V 形拟合细化 |
| `k2eff` | π²/4 · (fa − fr)/fa（小数，不是百分数），与网页端一致 |
| `uncertainty_mhz` | 半个频率步长，偏保守；V 形拟合通常远好于此 |
| `modes` | 频带内其他谐振峰（例如主 SH 模旁的 Rayleigh 杂散） |
| `warnings` | `peak_at_band_edge`、`antiresonance_not_found`、`coarse_sampling`、`multiple_modes` |
| `next_steps` | 基于警告的下一步建议 |
| `artifacts` | Y11.png、网格图、位移/电势场图、admittance.csv 的路径 |
| `q_r`, `q_a` | 恒为 null：求解模型无损，谐振是极点 |

## 精度参考

用 `sawsim.metrics` 从验证数据（`tests/data/`）中提取 fr/fa，9 个模板与独立参考有限元解的偏差：

| 模板 | 参考 fr / fa (GHz) | Δfr / Δfa (MHz) |
|---|---|---|
| sp_single_layer | 1.80791 / 1.87557 | −0.06 / 0.00 |
| sp_double_layer | 1.82363 / 1.90406 | 0.00 / 0.00 |
| sp_triple_layer | 1.75860 / 1.84383 | −0.45 / −0.43 |
| sp_quad_layer | 1.75859 / 1.84382 | 0.00 / 0.00 |
| sp_tcsaw | 1.75891 / 1.81852 | −0.09 / −0.16 |
| sp_2p5d_single_layer | 1.80791 / 1.87554 | −0.08 / −0.03 |
| sp_2p5d_double_layer | 1.84441 / 1.92538 | 0.00 / −0.01 |
| sp_2p5d_triple_layer | 1.75820 / 1.84342 | 0.00 / −0.01 |
| sp_2p5d_quad_layer | 1.89841 / 1.98725 | +0.04 / +0.06 |

参考曲线的频率步长为 1–2 MHz。`tests/test_agent.py` 把 1 MHz 作为回归门限。

## 代理验收（2026-09-30，sawsim 2.1.0）

把 [`examples/agent_tasks.md`](https://github.com/Duane245/sawsim/blob/main/examples/agent_tasks.md) 的 6 道题原样交给两个代理，
提示里只说明“已安装 sawsim”，不给字段名、不给参考结果。两个代理都从 `sawsim --help` 出发，自己找到 `sawsim guide`。

| 题 | 内容 | 判分依据 | codex (gpt-6-astra) | Claude Code (Opus) |
|---|---|---|---|---|
| A1 | 按工程描述复现 TC-SAW 参考模型 | 参考 fr/fa 1.75891 / 1.81852 GHz | 1.75882 / 1.81833 ✓ | 1.7588 / 1.8183 ✓ |
| A2 | 复现 LT 薄膜 / Si | 1.82363 / 1.90406 | 1.82307 / 1.90365 ✓ | 1.8231 / 1.9037 ✓ |
| A3 | 复现 IHP-SAW 四层 | 1.75859 / 1.84382 | 1.75813 / 1.84347 ✓ | 1.7581 / 1.8435 ✓ |
| B1 | 默认单层模板 fr/fa/k² | 1.80777 / 1.87557，8.92 % | 1.80779 / 1.87559，8.92 % ✓ | 1.8078 / 1.8756，8.92 % ✓ |
| B2 | 调节周期使 fr = 1.7975 GHz ± 2 MHz | 隐藏答案 0.9731 µm | 0.97307 µm，+0.04 MHz ✓ | 0.97304 µm，+0.09 MHz ✓ |
| B3 | 金属化比 0.4 vs 0.6 的 k² 差及网格收敛判断 | +0.29 个百分点，网格误差 ≤ 0.03 | +0.30，判定显著 ✓ | +0.30，判定显著 ✓ |

- 两个代理 6 题全对（通过标准：fr/fa 偏差 ≤ 2 MHz），都主动做了网格加密检查，并正确处理了易错点：TC-SAW 数据已预旋转、欧拉角保持 0；TC-SAW 只能用 ME0；多晶硅有两条材料记录，选了模板默认的那条。
- codex 用时 9.4 分钟、调用 sawsim 约 70 次；Claude 经 ssh 远程调用，用时 16 分钟、调用 25 次。两者都用割线法 3 步命中 B2 的目标频率。
- A2/A3 的网格从 0.5 µm 加密到 0.25 µm 后，fr 移动约 0.5 MHz。报告的偏差已包含这部分。
- 代理指出的问题已修正或写进说明：同一配置并发运行时缓存冲突（已修复，并加了测试）；TC-SAW 的 SiO₂ 厚度从压电表面量起；2D 模板的底部 PML 用的是压电材料；`converge` 会把网格限制在模板下限。

