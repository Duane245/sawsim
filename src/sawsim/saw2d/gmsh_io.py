"""Gmsh Python API → :class:`saw2d.mmesh.Msh` 直读路径(2D,跳过 ``.m``)。

与 3D 的 :mod:`saw2d.saw3d.gmsh_io` 同款思路:
1. mesh 脚本(``mesh/Meshing*.py`` 改造后)调用 ``build_mesh()`` 在内存里
   ``gmsh.initialize() / 建模 / generate(2) / setOrder(2)``;
2. 紧接着 :func:`harvest_2d_mesh` 从当前 Gmsh 会话抽数据,返回与
   :func:`saw2d.mmesh.read_m_mesh` 同结构的 :class:`Msh`;
3. 调用方再 ``gmsh.finalize()``。

Gmsh 元素类型:``8 = Line3`` (3 节点线), ``10 = Quad9``。
"""

from __future__ import annotations

import numpy as np
import gmsh

from .mmesh import Msh


_TYPE_LINE3 = 8
_TYPE_QUAD9 = 10


def _node_tag_to_index(node_tags: np.ndarray) -> np.ndarray:
    n_tags = node_tags.astype(np.int64)
    tmax = int(n_tags.max())
    tag2idx = np.full(tmax + 1, -1, dtype=np.int64)
    tag2idx[n_tags] = np.arange(n_tags.size, dtype=np.int64)
    return tag2idx


def _collect_typed_elements(dim: int, elem_type: int, nodes_per_elem: int):
    """Iterate physical groups of ``dim``, collect typed elements as
    ``(node_tag_flat_int64, physical_tag_int64)``。"""
    conn_blocks: list[np.ndarray] = []
    tag_blocks: list[np.ndarray] = []
    for d, ptag in gmsh.model.getPhysicalGroups(dim):
        if d != dim:
            continue
        for entity in gmsh.model.getEntitiesForPhysicalGroup(dim, ptag):
            types, _etags, n_tags = gmsh.model.mesh.getElements(dim, int(entity))
            for et, nt in zip(types, n_tags):
                if int(et) != elem_type:
                    continue
                nt = np.asarray(nt, dtype=np.int64)
                ne = nt.size // nodes_per_elem
                if ne == 0:
                    continue
                conn_blocks.append(nt)
                tag_blocks.append(np.full(ne, int(ptag), dtype=np.int64))
    if not conn_blocks:
        return (np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64))
    return (np.concatenate(conn_blocks), np.concatenate(tag_blocks))


def _clean_pos(pos: np.ndarray) -> np.ndarray:
    """``%.13g`` 文本往返压平 1-ULP 噪声,与 ``gmsh.write(.m)`` 精度对齐。
    详见 :mod:`saw2d.saw3d.gmsh_io` 同名函数的说明。"""
    flat = pos.ravel()
    cleaned = np.array([float(f"{x:.13g}") for x in flat], dtype=float)
    return cleaned.reshape(pos.shape)


def harvest_2d_mesh() -> Msh:
    """从当前 Gmsh 会话抽取 Quad9 + Line3 网格,返回与
    :func:`saw2d.mmesh.read_m_mesh` 同结构的 :class:`Msh`。

    必须在 ``gmsh.model.mesh.generate(2) + setOrder(2)`` 之后,
    ``gmsh.finalize()`` 之前调用。

    返回的 ``Msh`` 字段(与 ``.m`` 解析器一致):
      * ``nbNod`` (int) 节点总数
      * ``POS``   (N, 3) float, μm,**第 3 列(z)恒为 0**(2D 模型)
      * ``QUADS9`` (Nq, 10) float, **1-based** 节点索引 + 第 10 列物理标签
      * ``LINES3`` (Nl, 4) float, **1-based** 节点索引 + 第 4 列物理标签
    """
    # ---- 节点
    node_tags, coords_flat, _ = gmsh.model.mesh.getNodes()
    node_tags = np.asarray(node_tags, dtype=np.int64)
    coords = np.asarray(coords_flat, dtype=float).reshape(-1, 3)

    n_nodes = node_tags.size
    order = np.argsort(node_tags)
    pos = _clean_pos(coords[order])                        # 1-based ascending
    tag2idx = _node_tag_to_index(node_tags)
    tag2idx[node_tags[order]] = np.arange(n_nodes, dtype=np.int64)

    # ---- Quad9 体单元(2D 主体)
    q_flat, q_tag = _collect_typed_elements(2, _TYPE_QUAD9, 9)
    if q_flat.size:
        # 重映射到 0-based dense index,再 +1 还原成 .m 解析器的 1-based 约定
        q_dense = tag2idx[q_flat].reshape(-1, 9) + 1
        quads9 = np.concatenate([q_dense.astype(float),
                                 q_tag.reshape(-1, 1).astype(float)], axis=1)
    else:
        quads9 = np.empty((0, 10), dtype=float)

    # ---- Line3 线单元(边界条件用)
    l_flat, l_tag = _collect_typed_elements(1, _TYPE_LINE3, 3)
    if l_flat.size:
        l_dense = tag2idx[l_flat].reshape(-1, 3) + 1
        lines3 = np.concatenate([l_dense.astype(float),
                                 l_tag.reshape(-1, 1).astype(float)], axis=1)
    else:
        lines3 = np.empty((0, 4), dtype=float)

    msh = Msh()
    msh["nbNod"] = int(n_nodes)
    msh["POS"] = pos
    msh["QUADS9"] = quads9
    msh["LINES3"] = lines3
    return msh


def verify_against_m_2d(msh_api: Msh, m_path: str,
                        tol_pos: float = 1e-12) -> dict:
    """与 :func:`saw2d.mmesh.read_m_mesh` 解析路径对照。

    单元数组比较用"按 tag 节点集等价性",与 3D 同款 ——
    下游 ``model.nodes_with_tag`` / ``where(elem_tag == ...)`` 等
    依赖标签下的节点 / 单元集合,不依赖行序。
    """
    from .mmesh import read_m_mesh
    ref = read_m_mesh(m_path)
    report = {}

    report["nbNod"] = (msh_api.nbNod == ref.nbNod,
                       f"api={msh_api.nbNod}, m={ref.nbNod}")

    if msh_api.POS.shape == ref.POS.shape:
        diff = float(np.max(np.abs(msh_api.POS - ref.POS)))
        report["POS"] = (diff <= tol_pos, f"max|Δ|={diff:.3e} (tol={tol_pos:.0e})")
    else:
        report["POS"] = (False, f"shape api={msh_api.POS.shape} m={ref.POS.shape}")

    for name, idx_cols, tag_col in [("QUADS9", slice(0, 9), 9),
                                    ("LINES3", slice(0, 3), 3)]:
        a = getattr(msh_api, name); b = getattr(ref, name)
        if a.shape != b.shape:
            report[name] = (False, f"shape api={a.shape} m={b.shape}")
            continue
        api_tags = set(a[:, tag_col].astype(int).tolist())
        ref_tags = set(b[:, tag_col].astype(int).tolist())
        if api_tags != ref_tags:
            report[name] = (False, f"tag sets differ: api={sorted(api_tags)} "
                                   f"m={sorted(ref_tags)}")
            continue
        all_ok = True
        details = []
        for t in sorted(api_tags):
            a_sig = {tuple(sorted(row[idx_cols].astype(int)))
                     for row in a[a[:, tag_col] == t]}
            b_sig = {tuple(sorted(row[idx_cols].astype(int)))
                     for row in b[b[:, tag_col] == t]}
            ok = a_sig == b_sig
            all_ok = all_ok and ok
            details.append(f"tag={t}:{'='if ok else'≠'}{len(a_sig)}")
        report[name] = (all_ok, "set-of-tuples per tag — " + ", ".join(details))
    return report
