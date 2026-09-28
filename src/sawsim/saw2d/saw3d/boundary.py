"""Boundary-node extraction and periodic-DOF indexing.

Ports ``findSAWBoundary3DS.m``, ``SortLR_3d.m``, ``SortFB_3d.m`` and
``Boundary_idx_vect3DS.m`` for the single-period (SP) 3-D model.

All node ids are kept 0-based.  DOF layout: u DOFs are interleaved
(node ``n`` -> ``3n, 3n+1, 3n+2``); phi DOFs are block-appended (node ``n`` ->
``GDofu + n``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np


# ---------------------------------------------------------------- set helpers
def _u(a):
    """sorted unique, like MATLAB unique()."""
    return np.unique(np.asarray(a, dtype=np.int64).ravel())


def _intersect(a, b):
    return np.intersect1d(a, b, assume_unique=False)


def _setdiff(a, b):
    return np.setdiff1d(a, b, assume_unique=False)


# ---------------------------------------------------------- boundary finding
def find_saw_boundary_3ds(mesh):
    """Return the boundary node sets from the QUADS9 physical tags.

    Tags: 1=left, 2=right, 3=back, 4=front, 5=bottom, 7=signal(+), 8=ground(-).
    """
    q = mesh.quads9
    tag = mesh.quad_tag

    def nodes_of(t):
        return _u(q[tag == t, :9])

    gamma_l = nodes_of(1)
    gamma_r = nodes_of(2)
    gamma_back = nodes_of(3)
    gamma_front = nodes_of(4)
    gamma_2 = nodes_of(5)
    gamma_zheng = nodes_of(7)
    gamma_fu = nodes_of(8)
    return dict(L=gamma_l, R=gamma_r, front=gamma_front, back=gamma_back,
                bottom=gamma_2, zheng=gamma_zheng, fu=gamma_fu)


# ---------------------------------------------------------- symmetric sorting
def sort_lr_3d(left, right, node_coords):
    """Order left/right node sets so paired nodes share an index (by y then z)."""
    cor = np.round(node_coords * 1e9, 1)
    il = np.lexsort((cor[left, 2], cor[left, 1]))
    ir = np.lexsort((cor[right, 2], cor[right, 1]))
    return left[il], right[ir]


def sort_fb_3d(front, back, node_coords):
    """Order front/back node sets so paired nodes share an index (by x then z)."""
    cor = np.round(node_coords * 1e9, 1)
    iff = np.lexsort((cor[front, 2], cor[front, 0]))
    ib = np.lexsort((cor[back, 2], cor[back, 0]))
    return front[iff], back[ib]


# -------------------------------------------------------------- DOF container
@dataclass
class Boundary:
    machine: dict = field(default_factory=dict)
    electric: dict = field(default_factory=dict)


def _mach_block(nodes):
    """u-DOFs of a node set, component-major: [all ux, all uy, all uz]."""
    nodes = np.asarray(nodes, dtype=np.int64)
    return np.concatenate([3 * nodes, 3 * nodes + 1, 3 * nodes + 2])


def boundary_idx_vect_3ds(sets, node_coords, gdofu):
    """Build the periodic / prescribed DOF index sets (port of Boundary_idx_vect3DS.m)."""
    g2 = sets["bottom"]
    L, R = sets["L"], sets["R"]
    front, back = sets["front"], sets["back"]
    zheng, fu = sets["zheng"], sets["fu"]

    # --- remove electrode nodes from front/back
    front_zheng = _intersect(front, zheng)
    back_zheng = _intersect(back, zheng)
    front_fu = _intersect(front, fu)
    back_fu = _intersect(back, fu)
    front = _setdiff(front, np.concatenate([front_zheng, front_fu]))
    back = _setdiff(back, np.concatenate([back_zheng, back_fu]))

    # --- remove bottom nodes from front/back/L/R
    g_2F = _intersect(g2, front)
    g_2b = _intersect(g2, back)
    g_2L = _intersect(g2, L)
    g_2R = _intersect(g2, R)

    g_Lb_e = _intersect(L, back)
    g_Rb_e = _intersect(R, back)
    g_2Lb = _intersect(g2, g_Lb_e)
    g_2Rb = _intersect(g2, g_Rb_e)
    g_2L_e = _setdiff(g_2L, g_2Lb)
    g_2R_e = _setdiff(g_2R, g_2Rb)

    front = _setdiff(front, g_2F)
    back = _setdiff(back, g_2b)
    L = _setdiff(L, g_2L)
    R = _setdiff(R, g_2R)

    # --- remove periodic-boundary corner points
    g_Lb = _intersect(L, back)
    g_Rb = _intersect(R, back)
    L = _setdiff(L, g_Lb)
    R = _setdiff(R, g_Rb)

    # --- symmetric sorting so periodic pairs share an index
    L, R = sort_lr_3d(L, R, node_coords)
    front, back = sort_fb_3d(front, back, node_coords)
    g_2F, g_2b = sort_fb_3d(g_2F, g_2b, node_coords)
    g_2L_e, g_2R_e = sort_lr_3d(g_2L_e, g_2R_e, node_coords)
    front_zheng, back_zheng = sort_fb_3d(front_zheng, back_zheng, node_coords)
    front_fu, back_fu = sort_fb_3d(front_fu, back_fu, node_coords)

    bnd = Boundary()
    # --- solid mechanics
    bnd.machine["period_F"] = np.concatenate(
        [_mach_block(front), _mach_block(front_zheng), _mach_block(front_fu)])
    bnd.machine["period_B"] = np.concatenate(
        [_mach_block(back), _mach_block(back_zheng), _mach_block(back_fu)])
    bnd.machine["period_L"] = _mach_block(L)
    bnd.machine["period_R"] = _mach_block(R)
    bnd.machine["fix"] = _mach_block(g2)

    # --- electrostatics
    bnd.electric["period_F"] = np.concatenate([front + gdofu, g_2F + gdofu])
    bnd.electric["period_B"] = np.concatenate([back + gdofu, g_2b + gdofu])
    bnd.electric["period_L"] = np.concatenate([L + gdofu, g_2L_e + gdofu])
    bnd.electric["period_R"] = np.concatenate([R + gdofu, g_2R_e + gdofu])
    bnd.electric["zheng"] = zheng + gdofu
    bnd.electric["fu"] = fu + gdofu
    return bnd


# ============================================================================
# FP（有限器件）变体：单向 F↔B 周期 + 左右反射栅悬浮电势 XFL / XFR
#
# 与 SP 不同：
#   * 无 L↔R 周期（左右外侧已被多片 PML 吸收）
#   * 反射栅 XFL / XFR 上所有节点共享同一电势 —— 等价于把整组 phi DOF 合并到 [0]
#   * 物理标签：3=back, 4=front, 5=bottom, 6=XFL, 7=XFR, 8=zheng, 9=fu
# ============================================================================
def find_saw_boundary_3df(mesh):
    """Return boundary node sets for the FP (finite-device) 3-D model.

    Tags: 3=back, 4=front, 5=bottom, 6=XFL, 7=XFR, 8=signal, 9=ground.
    """
    q = mesh.quads9
    tag = mesh.quad_tag

    def nodes_of(t):
        return _u(q[tag == t, :9])

    return dict(XFL=nodes_of(6), XFR=nodes_of(7),
                front=nodes_of(4), back=nodes_of(3),
                bottom=nodes_of(5),
                zheng=nodes_of(8), fu=nodes_of(9))


def boundary_idx_vect_3df(sets, node_coords, gdofu):
    """Build FP 3-D boundary DOF container (port of ``Boundary_idx3DF.m``).

    Folds:
      * mechanics F↔B (front master, back slave) including frontXFL/backXFL
        and frontXFR/backXFR pairs (which share displacement with the front face)
      * electric  F↔B for the non-electrode, non-XFL/XFR potentials
      * electric  XFL[0]→ master / XFL[1:] → slave (equipotential reflector grid)
        and likewise for XFR — *not* part of F↔B (kept in ``bnd.electric["XFL"]``).
    """
    g2 = sets["bottom"]
    front, back = sets["front"], sets["back"]
    zheng, fu = sets["zheng"], sets["fu"]
    XFL, XFR = sets["XFL"], sets["XFR"]

    # --- front/back: peel off electrode + XFL/XFR subsets (still paired)
    frontZ = _intersect(front, zheng); backZ = _intersect(back, zheng)
    frontF = _intersect(front, fu);    backF = _intersect(back, fu)
    front = _setdiff(front, np.concatenate([frontZ, frontF]))
    back = _setdiff(back, np.concatenate([backZ, backF]))

    frontXFL = _intersect(front, XFL); backXFL = _intersect(back, XFL)
    frontXFR = _intersect(front, XFR); backXFR = _intersect(back, XFR)
    front = _setdiff(front, np.concatenate([frontXFL, frontXFR]))
    back = _setdiff(back, np.concatenate([backXFL, backXFR]))

    # --- front/back: drop bottom-edge nodes (those go to fix)
    g_2F = _intersect(g2, front); g_2b = _intersect(g2, back)
    front = _setdiff(front, g_2F); back = _setdiff(back, g_2b)

    # --- symmetric sorting so paired nodes share an index
    front, back = sort_fb_3d(front, back, node_coords)
    frontZ, backZ = sort_fb_3d(frontZ, backZ, node_coords)
    frontF, backF = sort_fb_3d(frontF, backF, node_coords)
    frontXFL, backXFL = sort_fb_3d(frontXFL, backXFL, node_coords)
    frontXFR, backXFR = sort_fb_3d(frontXFR, backXFR, node_coords)
    g_2F, g_2b = sort_fb_3d(g_2F, g_2b, node_coords)

    bnd = Boundary()
    # --- mechanics: F↔B (every pair set carries all 3 disp components)
    bnd.machine["period_F"] = np.concatenate([
        _mach_block(front), _mach_block(frontZ), _mach_block(frontF),
        _mach_block(frontXFL), _mach_block(frontXFR)])
    bnd.machine["period_B"] = np.concatenate([
        _mach_block(back), _mach_block(backZ), _mach_block(backF),
        _mach_block(backXFL), _mach_block(backXFR)])
    bnd.machine["fix"] = _mach_block(g2)

    # --- electrostatics
    bnd.electric["period_F"] = np.concatenate([front + gdofu, g_2F + gdofu])
    bnd.electric["period_B"] = np.concatenate([back + gdofu, g_2b + gdofu])
    bnd.electric["zheng"] = zheng + gdofu
    bnd.electric["fu"] = fu + gdofu
    # Whole XFL/XFR set (front/back/bottom-edge nodes included).  The solver
    # treats element [0] as the master and folds [1:] onto it (equipotential).
    bnd.electric["XFL"] = XFL + gdofu
    bnd.electric["XFR"] = XFR + gdofu
    return bnd
