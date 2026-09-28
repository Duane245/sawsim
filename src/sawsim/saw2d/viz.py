"""绘图：网格、位移场、电势场、Y11 导纳曲线。

图中文字采用英文（运行环境无中文字体）。对外展示的曲线图中
参考解一律标注为「FEM software」，不出现具体商业软件名。
"""

from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

from .piezo_fem import Model

_PALETTE = ["#4C72B0", "#C44E52", "#55A868", "#8172B2", "#CCB974", "#64B5CD"]


def _corner_polys(model: Model):
    """返回各单元 4 角点多边形（单位 µm）与标签。"""
    xy = model.pos_m * 1e6                                # m -> µm
    return xy[model.quads[:, :4]], model.elem_tag


def _figsize(model: Model):
    """按求解域长宽比给出合适的画布尺寸。"""
    xr = np.ptp(model.pos_m[:, 0])
    yr = np.ptp(model.pos_m[:, 1])
    asp = xr / yr if yr > 0 else 1.0
    if asp >= 1.0:                                        # 宽扁
        return (min(14, 3 + 8 * min(asp, 4)), 4.5)
    return (4.5, min(11, 3 + 8 / max(asp, 0.25)))         # 高窄


def plot_mesh(model: Model, path: str, title: str = "Mesh (by material)",
              tag_labels: dict | None = None):
    """绘制网格，按材料分区着色。

    Parameters
    ----------
    tag_labels : dict[int, str] | None
        ``{物理组标签: 图例名}``；同名标签合并为一种颜色 / 一个图例项。
        缺省时按标签自动命名。
    """
    polys, tags = _corner_polys(model)
    if tag_labels is None:
        tag_labels = {int(t): f"tag {int(t)}" for t in np.unique(tags)}

    groups = {}                                           # label -> [tags]
    for tag, lab in tag_labels.items():
        groups.setdefault(lab, []).append(tag)

    fig, ax = plt.subplots(figsize=_figsize(model))
    for ci, (lab, tlist) in enumerate(groups.items()):
        sel = np.isin(tags, tlist)
        if not sel.any():
            continue
        pc = PolyCollection(polys[sel], facecolors=_PALETTE[ci % len(_PALETTE)],
                            edgecolors="#172b3b", linewidths=0.45, label=lab,
                            alpha=0.85)
        ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xlabel("x / um")
    ax.set_ylabel("y / um")
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), fontsize=8,
              frameon=False, ncol=1)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_nodal_field(model: Model, values: np.ndarray, path: str,
                     title: str, cbar_label: str):
    """以单元面填色绘制节点标量场（取单元 4 角点均值）。"""
    polys, _ = _corner_polys(model)
    facevals = values[model.quads[:, :4]].mean(axis=1)
    fig, ax = plt.subplots(figsize=_figsize(model))
    pc = PolyCollection(polys, array=facevals, cmap="turbo",
                        edgecolors="face", linewidths=0)
    ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xlabel("x / um")
    ax.set_ylabel("y / um")
    ax.set_title(title)
    fig.colorbar(pc, ax=ax, label=cbar_label, shrink=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_y11(fre, Y, path: str, ref_path: str | None = None,
             title: str = "Admittance Y11", ref_freq_scale: float = 1.0):
    """绘制 Y11 导纳曲线；若给定参考文件则叠加对比。

    参考曲线标注为「FEM software」。``ref_freq_scale`` 用于把参考文件第一列
    缩放到 GHz（例如 MHz 文件传 1e-3）。
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    if ref_path is not None:
        try:
            ref = np.loadtxt(ref_path, comments="%")
            ax.plot(ref[:, 0] * ref_freq_scale, np.log(np.abs(ref[:, 1])),
                    "-", color="#C44E52", lw=2.4,
                    label="FEM software (reference)")
        except OSError:
            pass
    ax.plot(np.asarray(fre) * 1e-9, np.log(np.abs(Y)), "--",
            color="#1f4e9c", lw=1.8, label="This work (Python FEM)")
    ax.set_xlim(fre[0] * 1e-9, fre[-1] * 1e-9)
    ax.set_xlabel("f / GHz")
    ax.set_ylabel("Admittance  ln|Y|")
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
