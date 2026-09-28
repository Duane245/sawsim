"""解析 Gmsh 导出的 MATLAB 网格脚本（``mesh/*.m``）。

对应 MATLAB 端的网格 ``.m`` 文件：它们是给 MATLAB 运行的脚本，
逐行构建 ``msh`` 结构体。这里不执行 MATLAB，直接用正则把
``msh.<字段> = [ ... ];`` 形式的数值矩阵抽取出来。

字段约定（与 MATLAB 一致）：
    POS      节点坐标，单位 **微米**（列：x y z）
    QUADS9   9 节点四边形单元，列 1-9 为节点号(1 基)，列 10 为物理组标签
    LINES3   3 节点线单元，列 1-3 为节点号(1 基)，列 4 为物理组标签
    nbNod    节点总数
"""

from __future__ import annotations

import re
import numpy as np


class Msh(dict):
    """``msh`` 结构体的轻量封装，支持属性式访问（``msh.POS``）。"""

    def __getattr__(self, name):  # noqa: D105
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - 防御性
            raise AttributeError(name) from exc


def read_m_mesh(path: str) -> Msh:
    """读取 Gmsh ``.m`` 网格脚本，返回 :class:`Msh`。

    Parameters
    ----------
    path : str
        ``.m`` 网格文件路径。

    Returns
    -------
    Msh
        含 ``POS`` / ``QUADS9`` / ``LINES3`` 等键的字典。
    """
    text = open(path, encoding="utf-8", errors="replace").read()
    msh = Msh()

    m = re.search(r"nbNod\s*=\s*(\d+)", text)
    if m:
        msh["nbNod"] = int(m.group(1))

    # 抓取所有 “msh.NAME = [ ... ];” 数值矩阵块
    for blk in re.finditer(r"msh\.(\w+)\s*=\s*\[(.*?)\]\s*;", text, re.S):
        name, body = blk.group(1), blk.group(2)
        rows = []
        for line in body.strip().splitlines():
            line = line.strip().rstrip(";").strip()
            if not line:
                continue
            rows.append([float(x) for x in line.replace(",", " ").split()])
        if rows:
            msh[name] = np.asarray(rows, dtype=float)

    if "POS" not in msh:
        raise ValueError(f"{path}: 未找到 msh.POS")
    return msh
