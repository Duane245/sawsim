"""Gmsh Python API → :class:`Mesh` 直读路径(跳过 ``.m`` 中间文件)。

调用约定
--------
1. 由 ``mesh/SAW_3D_*.py`` 的 ``build_mesh()`` 把 Gmsh 会话初始化、建模、
   ``gmsh.model.mesh.generate(3) + setOrder(2)``;
2. 紧接着调用本模块 :func:`harvest_3d_mesh` 抽取 :class:`Mesh` 数据;
3. 调用方再 ``gmsh.finalize()``。

返回的 :class:`Mesh` 与 :func:`saw2d.saw3d.mesh_io.read_gmsh_m` 同结构:
- ``nb_nod`` (int) 节点数
- ``pos`` (N, 3) float, μm 单位 —— **不**乘 ``1e-6``,与 ``.m`` 解析路径一致
- ``quads9`` (Nq, 9) int64, **0-based** 节点索引
- ``quad_tag`` (Nq,) int64, 物理组标签
- ``hexas27`` (Nh, 27) int64, 0-based
- ``hex_tag`` (Nh,) int64

Gmsh 元素类型编号:`10 = Quad9`, `12 = Hex27`。
"""

from __future__ import annotations

import numpy as np
import gmsh

from .mesh_io import Mesh


_TYPE_QUAD9 = 10
_TYPE_HEX27 = 12


def _node_tag_to_index(node_tags: np.ndarray) -> np.ndarray:
    """构造 1-based tag → 0-based dense index 的查表数组。"""
    n_tags = node_tags.astype(np.int64)
    tmax = int(n_tags.max())
    tag2idx = np.full(tmax + 1, -1, dtype=np.int64)
    tag2idx[n_tags] = np.arange(n_tags.size, dtype=np.int64)
    return tag2idx


def _collect_typed_elements(dim: int, elem_type: int, nodes_per_elem: int):
    """按物理组遍历当前 ``gmsh.model``,收集指定类型单元的 (连接, 物理标签)。

    返回 ``(connectivity_flat_int64, tags_int64)``:
      * ``connectivity_flat`` shape ``(Ne * nodes_per_elem,)``,**1-based** node tags
      * ``tags`` shape ``(Ne,)``,physical group integer
    """
    conn_blocks: list[np.ndarray] = []
    tag_blocks: list[np.ndarray] = []

    for d, ptag in gmsh.model.getPhysicalGroups(dim):
        if d != dim:
            continue                                       # 防御性,gPG(dim) 一般已过滤
        for entity in gmsh.model.getEntitiesForPhysicalGroup(dim, ptag):
            types, _etags, n_tags = gmsh.model.mesh.getElements(dim, int(entity))
            for et, nt in zip(types, n_tags):
                if int(et) != elem_type:
                    continue                               # 例如线元 / 边角等
                nt = np.asarray(nt, dtype=np.int64)
                ne = nt.size // nodes_per_elem
                if ne == 0:
                    continue
                conn_blocks.append(nt)
                tag_blocks.append(np.full(ne, int(ptag), dtype=np.int64))

    if not conn_blocks:
        return (np.empty(0, dtype=np.int64),
                np.empty(0, dtype=np.int64))
    return (np.concatenate(conn_blocks), np.concatenate(tag_blocks))


def _clean_pos(pos: np.ndarray) -> np.ndarray:
    """通过 ``%.13g`` 文本往返清掉 1-ULP 噪声,逼近 ``gmsh.write(.m)`` 的精度。

    背景:Gmsh API ``getNodes()`` 返回的坐标含累计算术 1-ULP 误差,
    而 ``gmsh.write(.m)`` → text → 解析的链路会自然把这些 ULP 归零到
    "最短十进制" 形式。``sort_fb_3d`` / ``sort_lr_3d`` 用 ``np.round(*1e9, 1)``
    在 0.x5 nm 边界附近对 1-ULP 漂移敏感,会让两路 F↔B 配对错位。
    13 位有效数字 = 1e-13 相对精度 ≈ 几 fm,远低于任何 FEM 节点间距。
    """
    flat = pos.ravel()
    cleaned = np.array([float(f"{x:.13g}") for x in flat], dtype=float)
    return cleaned.reshape(pos.shape)


def harvest_3d_mesh() -> Mesh:
    """从当前 Gmsh 会话提取 Hex27 + Quad9 网格,返回 :class:`Mesh`。

    必须在 ``gmsh.model.mesh.generate(3) + setOrder(2)`` 之后、
    ``gmsh.finalize()`` 之前调用。
    """
    # ---- 节点
    node_tags, coords_flat, _ = gmsh.model.mesh.getNodes()
    node_tags = np.asarray(node_tags, dtype=np.int64)
    coords = np.asarray(coords_flat, dtype=float).reshape(-1, 3)

    n_nodes = node_tags.size
    # 0-based 紧致顺序:第 i 行对应 node_tags[i] 的坐标
    # 同时建 tag→idx 查表
    tag2idx = _node_tag_to_index(node_tags)
    # 把 pos 按 0-based dense index 排序:pos[idx] = coords[i] where idx = tag2idx[node_tags[i]]
    # 这里 node_tags 顺序就是 coords 顺序,所以重排到 0..N-1 即可:
    order = np.argsort(node_tags)                          # 1-based ascending
    # dense 顺序 = 排序后 node_tags 在 [1..N] 时直接对应
    pos = _clean_pos(coords[order])
    # tag2idx 重建为按"排序后位置"映射
    tag2idx[node_tags[order]] = np.arange(n_nodes, dtype=np.int64)

    # ---- Hex27 体单元
    hex_flat, hex_tag = _collect_typed_elements(3, _TYPE_HEX27, 27)
    if hex_flat.size:
        hexas27 = tag2idx[hex_flat].reshape(-1, 27)        # 0-based
    else:
        hexas27 = np.empty((0, 27), dtype=np.int64)

    # ---- Quad9 面单元
    q_flat, quad_tag = _collect_typed_elements(2, _TYPE_QUAD9, 9)
    if q_flat.size:
        quads9 = tag2idx[q_flat].reshape(-1, 9)            # 0-based
    else:
        quads9 = np.empty((0, 9), dtype=np.int64)

    return Mesh(nb_nod=int(n_nodes), pos=pos,
                quads9=quads9, quad_tag=quad_tag,
                hexas27=hexas27, hex_tag=hex_tag)


def verify_against_m(mesh_api: Mesh, m_path: str,
                     tol_pos: float = 1e-12) -> dict:
    """与 ``.m`` 解析路径对照,逐字段比对 :class:`Mesh`。

    ``hexas27`` / ``hex_tag`` 做严格 ``np.array_equal``(两侧体单元顺序一致);
    ``quads9`` / ``quad_tag`` 做**按物理标签的节点集合等价性**比较 —— 因为
    下游 :func:`find_saw_boundary_3ds`/``3df`` 只用 ``np.unique(q[tag==t, :9])``
    取每个标签的节点集,行顺序与单行内节点顺序不影响结果。
    """
    from .mesh_io import read_gmsh_m
    ref = read_gmsh_m(m_path)
    report = {}

    report["nb_nod"] = (mesh_api.nb_nod == ref.nb_nod,
                       f"api={mesh_api.nb_nod}, m={ref.nb_nod}")

    if mesh_api.pos.shape == ref.pos.shape:
        diff = float(np.max(np.abs(mesh_api.pos - ref.pos)))
        report["pos"] = (diff <= tol_pos, f"max|Δ|={diff:.3e} (tol={tol_pos:.0e})")
    else:
        report["pos"] = (False, f"shape api={mesh_api.pos.shape} m={ref.pos.shape}")

    # 体单元:先试严格 ``np.array_equal``;若行序不同则按 tag 比较单元(以 sorted
    # 27 节点 tuple 为指纹)的多集合 —— 行序不影响 K/M 装配。
    if (mesh_api.hexas27.shape == ref.hexas27.shape and
            mesh_api.hex_tag.shape == ref.hex_tag.shape and
            np.array_equal(mesh_api.hexas27, ref.hexas27) and
            np.array_equal(mesh_api.hex_tag, ref.hex_tag)):
        report["hexas27"] = (True, "row-identical")
        report["hex_tag"] = (True, "row-identical")
    elif mesh_api.hexas27.shape != ref.hexas27.shape:
        report["hexas27"] = (False, f"shape api={mesh_api.hexas27.shape} "
                                    f"m={ref.hexas27.shape}")
        report["hex_tag"] = report["hexas27"]
    else:
        api_tags = set(mesh_api.hex_tag.tolist())
        ref_tags = set(ref.hex_tag.tolist())
        all_ok = api_tags == ref_tags
        details = []
        for t in sorted(api_tags & ref_tags):
            a_sig = {tuple(sorted(r)) for r in mesh_api.hexas27[mesh_api.hex_tag == t]}
            b_sig = {tuple(sorted(r)) for r in ref.hexas27[ref.hex_tag == t]}
            ok = a_sig == b_sig
            all_ok = all_ok and ok
            details.append(f"tag={t}:{'='if ok else'≠'}{len(a_sig)}")
        msg = "set-of-tuples per tag — " + ", ".join(details)
        report["hexas27"] = (all_ok, msg)
        report["hex_tag"] = (all_ok, "tag set matches" if api_tags == ref_tags
                             else f"tag set diff: api={sorted(api_tags)} "
                                  f"m={sorted(ref_tags)}")

    # 面单元:按 tag 比对节点集
    api_tags = set(mesh_api.quad_tag.tolist())
    ref_tags = set(ref.quad_tag.tolist())
    if api_tags != ref_tags:
        report["quads9"] = (False, f"tag sets differ: api={sorted(api_tags)} "
                                   f"m={sorted(ref_tags)}")
        report["quad_tag"] = report["quads9"]
        return report
    all_ok = True
    details = []
    for t in sorted(api_tags):
        a = np.unique(mesh_api.quads9[mesh_api.quad_tag == t].ravel())
        b = np.unique(ref.quads9[ref.quad_tag == t].ravel())
        ok = a.size == b.size and bool(np.array_equal(a, b))
        all_ok = all_ok and ok
        details.append(f"tag={t}:{a.size}{'='if ok else'≠'}{b.size}")
    msg = "set-equal per tag — " + ", ".join(details)
    report["quads9"] = (all_ok, msg)
    report["quad_tag"] = (all_ok, "tag set matches")
    return report
