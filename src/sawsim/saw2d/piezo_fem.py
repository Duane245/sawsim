"""向量化压电耦合有限元组装（纯 NumPy / SciPy）。

对应 MATLAB ``AssemblyKM2D.m`` 及 ``formStiffnessMass2D*`` 系列的
**向量化形式**：所有单元一次性算出单元矩阵，再用一次 COO 散装为全局稀疏矩阵，
取代逐单元 / 逐基函数对的循环。

设计要点
--------
* 单元：9 节点双二次四边形（Q9），等参几何，3x3 高斯积分（与 MATLAB 一致）。
* 节点编号直接沿用 Gmsh 节点号（0 基），无需重映射。
* 自由度排布 ``[ux | uy | uz | phi]``，``GDof = 4 * numberNodes``（ME=1 / 2.5D）。
* PML：复数坐标拉伸，衰减系数按单元中心节点坐标取值，固定在扫频上限频率。
* 应变采用 9 分量（非对称位移梯度）形式，统一处理 PML 与非 PML 区域。
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import scipy.sparse as sp

from .materials import Material

# MATLAB formStiffnessMass2DPML.m 中的数值缩放系数（位移未知量列缩放，
# 改善 [u|phi] 耦合系统条件数；在电荷 Q 的计算中自动抵消）。
SCALE = 6.173191780858575e-11

# ME=1（2.5D）位移分量 -> [(9 分量应变行号, 求导方向)]
# 9 分量应变 g = [dux/dx, duy/dy, 0, 0, 0, dux/dy, duz/dy, duz/dx, duy/dx]
# 求导方向：0 = d/dx, 1 = d/dy
_STRAIN_SEL = {
    0: [(0, 0), (5, 1)],   # u_x
    1: [(1, 1), (8, 0)],   # u_y
    2: [(6, 1), (7, 0)],   # u_z
}

# ME=0（2D 平面分析）位移分量 -> [(3 分量 Voigt 应变行号, 求导方向)]
# 应变 ε = [εxx, εyy, εxy] = [∂x ux, ∂y uy, ∂y ux + ∂x uy]
_STRAIN_SEL_ME0 = {
    0: [(0, 0), (2, 1)],   # u_x -> εxx via ∂x，εxy via ∂y
    1: [(1, 1), (2, 0)],   # u_y -> εyy via ∂y，εxy via ∂x
}


# ---------------------------------------------------------------------------
# Q9 形函数与 3x3 高斯积分（对应 shapeFunctionsQ2D.m / gaussQuadrature.m）
# ---------------------------------------------------------------------------
def _gauss_3x3():
    g = np.array([-0.774596669241483, 0.0, 0.774596669241483])
    w = np.array([5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0])
    pts = np.array([(gx, gy) for gy in g for gx in g])     # (9,2)
    wts = np.array([wx * wy for wy in w for wx in w])      # (9,)
    return pts, wts


def _q9_shapes(xi, eta):
    """Q9 形函数及其自然坐标导数（节点序与 Gmsh QUADS9 一致）。

    Parameters
    ----------
    xi, eta : ndarray (nq,)

    Returns
    -------
    N : ndarray (nq, 9)
    dN : ndarray (nq, 9, 2)   —— 对 (xi, eta) 的导数
    """
    xi = np.asarray(xi, float)
    eta = np.asarray(eta, float)
    N = 0.25 * np.stack([
        xi * eta * (xi - 1) * (eta - 1),
        xi * eta * (xi + 1) * (eta - 1),
        xi * eta * (xi + 1) * (eta + 1),
        xi * eta * (xi - 1) * (eta + 1),
        -2 * eta * (xi * xi - 1) * (eta - 1),
        -2 * xi * (xi + 1) * (eta * eta - 1),
        -2 * eta * (xi * xi - 1) * (eta + 1),
        -2 * xi * (xi - 1) * (eta * eta - 1),
        4 * (xi * xi - 1) * (eta * eta - 1),
    ], axis=-1)
    dN_xi = 0.25 * np.stack([
        eta * (2 * xi - 1) * (eta - 1),
        eta * (2 * xi + 1) * (eta - 1),
        eta * (2 * xi + 1) * (eta + 1),
        eta * (2 * xi - 1) * (eta + 1),
        -4 * xi * eta * (eta - 1),
        -2 * (2 * xi + 1) * (eta + 1) * (eta - 1),
        -4 * xi * eta * (eta + 1),
        -2 * (2 * xi - 1) * (eta + 1) * (eta - 1),
        8 * xi * (eta * eta - 1),
    ], axis=-1)
    dN_eta = 0.25 * np.stack([
        xi * (xi - 1) * (2 * eta - 1),
        xi * (xi + 1) * (2 * eta - 1),
        xi * (xi + 1) * (2 * eta + 1),
        xi * (xi - 1) * (2 * eta + 1),
        -2 * (xi + 1) * (xi - 1) * (2 * eta - 1),
        -4 * xi * eta * (xi + 1),
        -2 * (xi + 1) * (xi - 1) * (2 * eta + 1),
        -4 * xi * eta * (xi - 1),
        8 * eta * (xi * xi - 1),
    ], axis=-1)
    return N, np.stack([dN_xi, dN_eta], axis=-1)


# ---------------------------------------------------------------------------
# PML 张量构造
# ---------------------------------------------------------------------------
def _C9(C: np.ndarray) -> np.ndarray:
    """6x6 刚度矩阵扩展为 9x9（对应 ``[C, C(:,4:6); C(4:6,:), C(4:6,4:6)]``）。"""
    C9 = np.zeros((9, 9), dtype=np.result_type(C, float))
    C9[:6, :6] = C
    C9[:6, 6:9] = C[:6, 3:6]
    C9[6:9, :6] = C[3:6, :6]
    C9[6:9, 6:9] = C[3:6, 3:6]
    return C9


def _e9(e: np.ndarray) -> np.ndarray:
    """3x6 压电矩阵扩展为 3x9（对应 ``[e, e(:,4:6)]``）。"""
    e9 = np.zeros((3, 9), dtype=np.result_type(e, float))
    e9[:, :6] = e
    e9[:, 6:9] = e[:, 3:6]
    return e9


def _T9(a1, a2, a3):
    """PML 坐标拉伸张量 T11（9x9，逐单元），对应 ``formStiffnessMass2DPMLuu``。"""
    code = {
        "A": a2 * a3 / a1, "b": a3, "c": a2,
        "D": a1 * a3 / a2, "e": a1, "F": a1 * a2 / a3,
    }
    row = {0: "AbcccbbAA", 1: "bDeeeDDbb", 2: "ceFFFeecc"}
    row[3] = row[4] = row[2]
    row[5] = row[6] = row[1]
    row[7] = row[8] = row[0]
    ne = np.asarray(a1).shape[0]
    T = np.empty((9, 9, ne), dtype=complex)
    for r in range(9):
        for cidx, ch in enumerate(row[r]):
            T[r, cidx] = code[ch]
    return T


def _Teps(a1, a2, a3):
    """PML 介电张量拉伸（3x3，逐单元），对应 ``formStiffnessMass2DPMLfi``。"""
    A = a2 * a3 / a1
    D = a1 * a3 / a2
    F = a1 * a2 / a3
    ne = np.asarray(a1).shape[0]
    T = np.empty((3, 3, ne), dtype=complex)
    T[0, 0], T[0, 1], T[0, 2] = A, a3, a2
    T[1, 0], T[1, 1], T[1, 2] = a3, D, a1
    T[2, 0], T[2, 1], T[2, 2] = a2, a1, F
    return T


# ---------------------------------------------------------------------------
# 有限元模型
# ---------------------------------------------------------------------------
@dataclass
class Model:
    """承载网格几何与连接关系的有限元模型（节点号直接沿用 Gmsh 编号）。"""

    pos_m: np.ndarray        # (nnod,2) 节点坐标，单位 m
    quads: np.ndarray        # (ne,9) 单元-节点连接（0 基）
    elem_tag: np.ndarray     # (ne,) 单元物理组标签
    N: int                   # 节点总数

    @property
    def ne(self) -> int:
        return self.quads.shape[0]

    def nodes_with_tag(self, line_tag: int, lines: np.ndarray) -> np.ndarray:
        """返回带指定线物理组标签的边界节点（Gmsh 节点号，0 基，已排序去重）。"""
        sel = lines[lines[:, 3] == line_tag][:, :3].astype(int) - 1
        return np.unique(sel)


def build_model(msh) -> Model:
    """由解析得到的 ``msh`` 构建有限元模型（坐标微米 -> 米）。"""
    pos_m = msh.POS[:, :2] * 1e-6
    quads = msh.QUADS9[:, :9].astype(int) - 1
    elem_tag = msh.QUADS9[:, 9].astype(int)
    return Model(pos_m=pos_m, quads=quads, elem_tag=elem_tag,
                 N=pos_m.shape[0])


# ---------------------------------------------------------------------------
# PML 配置
# ---------------------------------------------------------------------------
@dataclass
class PMLRegion:
    """单个 PML 子区域的几何与衰减参数（对应 MATLAB ``initialPML.m``）。

    ``kind`` 决定坐标拉伸方向：``'x'`` 侧边、``'y'`` 底部、``'xy'`` 角部。
    衰减量 ``d = dmax * (1 - (c-cp)^2/(ca-cp)^2)^n``，
    ``cp`` 为外边界（衰减最强），``ca`` 为内边界（衰减为 0）。
    """

    tag: int                 # QUADS9 物理组标签
    kind: str                # 'x' | 'y' | 'xy'
    dmax: float = 1e11
    n: int = 3
    xa: float = 0.0          # x 向内边界（m）
    xp: float = 0.0          # x 向外边界（m）
    ya: float = 0.0          # y 向内边界（m）
    yp: float = 0.0          # y 向外边界（m）


def material_index(model: Model, tag_map: dict) -> np.ndarray:
    """由 ``{物理组标签: 材料序号}`` 构造逐单元材料索引，形状 (ne,)。"""
    idx = np.full(model.ne, -1, dtype=int)
    for tag, mi in tag_map.items():
        idx[model.elem_tag == tag] = mi
    if (idx < 0).any():
        bad = sorted(set(model.elem_tag[idx < 0].tolist()))
        raise ValueError(f"以下单元标签未在材料映射中: {bad}")
    return idx


def element_alpha(model: Model, pml_regions, omega: float):
    """逐单元 PML 拉伸系数 ``(a1, a2, a3)``，形状均为 (ne,) 复数。"""
    ne = model.ne
    a1 = np.ones(ne, dtype=complex)
    a2 = np.ones(ne, dtype=complex)
    a3 = np.ones(ne, dtype=complex)

    centre = model.quads[:, 8]                            # 局部第 9 号 = 中心节点
    xc = model.pos_m[centre, 0]
    yc = model.pos_m[centre, 1]
    for reg in pml_regions:
        sel = model.elem_tag == reg.tag
        if "x" in reg.kind:
            ratio = np.clip((xc - reg.xp) ** 2 / (reg.xa - reg.xp) ** 2, 0.0, 1.0)
            d_x = reg.dmax * (1.0 - ratio) ** reg.n
            a1[sel] = 1.0 + d_x[sel] / (1j * omega)
        if "y" in reg.kind:
            ratio = np.clip((yc - reg.yp) ** 2 / (reg.ya - reg.yp) ** 2, 0.0, 1.0)
            d_y = reg.dmax * (1.0 - ratio) ** reg.n
            a2[sel] = 1.0 + d_y[sel] / (1j * omega)
    return a1, a2, a3


# ---------------------------------------------------------------------------
# 全局组装（向量化）
# ---------------------------------------------------------------------------
def _element_geometry(model: Model):
    """逐单元、逐积分点的梯度 Gram 矩阵与质量 Gram 矩阵。

    Returns
    -------
    G : dict[(d1,d2)] -> ndarray (ne,9,9)
        ``G[d1,d2][e,i,j] = ∫ ∂N_i/∂x_d1 · ∂N_j/∂x_d2``
    GM : ndarray (ne,9,9)
        ``GM[e,i,j] = ∫ N_i · N_j``
    """
    pts, wts = _gauss_3x3()
    Nq, dNref = _q9_shapes(pts[:, 0], pts[:, 1])           # (nq,9), (nq,9,2)

    xy = model.pos_m[model.quads]                          # (ne,9,2)
    # 雅可比 J[e,q,i,j] = Σ_a xy[e,a,i] dNref[q,a,j]
    J = np.einsum("eai,qaj->eqij", xy, dNref)              # (ne,nq,2,2)
    detJ = J[..., 0, 0] * J[..., 1, 1] - J[..., 0, 1] * J[..., 1, 0]
    invJ = np.empty_like(J)
    invJ[..., 0, 0], invJ[..., 1, 1] = J[..., 1, 1], J[..., 0, 0]
    invJ[..., 0, 1], invJ[..., 1, 0] = -J[..., 0, 1], -J[..., 1, 0]
    invJ /= detJ[..., None, None]

    # 全局梯度 dNxy[e,q,a,k] = Σ_j dNref[q,a,j] invJ[e,q,j,k]
    dNxy = np.einsum("qaj,eqjk->eqak", dNref, invJ)        # (ne,nq,9,2)
    dV = wts[None, :] * detJ                              # (ne,nq) 积分权重

    G = {}
    for d1 in (0, 1):
        for d2 in (0, 1):
            G[(d1, d2)] = np.einsum("eq,eqa,eqb->eab", dV,
                                    dNxy[..., d1], dNxy[..., d2])
    GM = np.einsum("eq,qa,qb->eab", dV, Nq, Nq)           # (ne,9,9)
    return G, GM


def assemble(model: Model, materials, elem_mat_idx, pml_regions, omega_top: float):
    """组装全局刚度 ``K`` 与质量 ``M``（4N x 4N，复数稀疏）。

    与 MATLAB ``AssemblyKM2D.m`` 一致：PML 坐标拉伸固定在扫频上限
    ``omega_top``，``K`` / ``M`` 只组装一次。

    Returns
    -------
    (K, M) : scipy.sparse.csr_matrix
        全局刚度与质量矩阵，自由度排布 ``[ux|uy|uz|phi]``。
    """
    N, ne = model.N, model.ne
    quads = model.quads

    # 1) 单元几何（梯度 Gram 矩阵）
    G, GM = _element_geometry(model)

    # 2) 逐单元有效本构张量
    a1, a2, a3 = element_alpha(model, pml_regions, omega_top)
    T9 = _T9(a1, a2, a3)                                  # (9,9,ne)
    Te = T9[:3]                                           # (3,9,ne)
    Teps = _Teps(a1, a2, a3)                              # (3,3,ne)

    mat_idx = np.asarray(elem_mat_idx, dtype=int)
    C9_lib = np.stack([_C9(m.C) for m in materials])      # (nmat,9,9)
    e9_lib = np.stack([_e9(m.e) for m in materials])      # (nmat,3,9)
    eps_lib = np.stack([m.eps for m in materials])        # (nmat,3,3)
    rho_lib = np.array([m.rho for m in materials])        # (nmat,)

    C_eff = T9 * np.moveaxis(C9_lib[mat_idx], 0, -1)      # (9,9,ne)
    E_eff = Te * np.moveaxis(e9_lib[mat_idx], 0, -1)      # (3,9,ne)
    P_eff = Teps * np.moveaxis(eps_lib[mat_idx], 0, -1)   # (3,3,ne)
    rho_eff = rho_lib[mat_idx] * a1 * a2 * a3             # (ne,)

    # 3) 各耦合子块的单元矩阵（ne,9,9），再散装为全局 COO
    rows, cols, data = [], [], []
    rid = np.broadcast_to(quads[:, :, None], (ne, 9, 9))  # 行节点
    cid = np.broadcast_to(quads[:, None, :], (ne, 9, 9))  # 列节点

    def scatter(blk, roff, coff, fac):
        rows.append((rid + roff).ravel())
        cols.append((cid + coff).ravel())
        data.append((blk * fac).ravel())

    # K_uu：位移-位移（列缩放 SCALE）
    for a in range(3):
        for b in range(3):
            blk = np.zeros((ne, 9, 9), dtype=complex)
            for rv, dv in _STRAIN_SEL[a]:
                for ru, du in _STRAIN_SEL[b]:
                    blk += C_eff[rv, ru][:, None, None] * G[(dv, du)]
            scatter(blk, a * N, b * N, SCALE)

    # K_ufi（不缩放）与 K_fiu = SCALE * K_ufi^T
    for a in range(3):
        blk = np.zeros((ne, 9, 9), dtype=complex)         # [i=位移, j=phi]
        for rv, dv in _STRAIN_SEL[a]:
            for k in (0, 1):
                blk += E_eff[k, rv][:, None, None] * G[(dv, k)]
        scatter(blk, a * N, 3 * N, 1.0)
        scatter(blk.transpose(0, 2, 1), 3 * N, a * N, SCALE)

    # K_fifi：电势-电势（全局取负号）
    blk = np.zeros((ne, 9, 9), dtype=complex)
    for j in (0, 1):
        for k in (0, 1):
            blk += P_eff[j, k][:, None, None] * G[(j, k)]
    scatter(blk, 3 * N, 3 * N, -1.0)

    K = sp.coo_matrix((np.concatenate(data),
                       (np.concatenate(rows), np.concatenate(cols))),
                      shape=(4 * N, 4 * N), dtype=complex).tocsr()

    # 质量矩阵：仅位移块，三分量相同，列缩放 SCALE
    mblk = (rho_eff[:, None, None] * GM) * SCALE          # (ne,9,9)
    mrows, mcols, mdata = [], [], []
    for a in range(3):
        mrows.append((rid + a * N).ravel())
        mcols.append((cid + a * N).ravel())
        mdata.append(mblk.ravel())
    M = sp.coo_matrix((np.concatenate(mdata),
                       (np.concatenate(mrows), np.concatenate(mcols))),
                      shape=(4 * N, 4 * N), dtype=complex).tocsr()

    return K, M


# ---------------------------------------------------------------------------
# ME=0（2D 平面分析）向量化组装：[ux | uy | phi]，GDof = 3N
# ---------------------------------------------------------------------------
def assemble_ME0(model: Model, materials, elem_mat_idx, pml_regions,
                 omega_top: float):
    """Plane-strain xy assembly [ux | uy | phi], 3N unknowns.

    Input tensors are already rotated then projected to Voigt [xx,yy,xy] and
    electric [x,y]. Lift them to zero-filled full tensors, share the verified
    derivative-specific ME1 PML assembly, and retain its principal xy/phi block.
    This is uz=0, Ez=0, not a plane-stress Schur complement.

    A single 3x3 PML Voigt multiplier is incorrect for engineering shear:
    ux,y and uy,x stretch differently. A direct reduced gradient assembly is
    algebraically equivalent, but COO accumulation order changed matrix entries
    at 1e-17 relative and amplified solution errors on this ill-conditioned model.
    Sharing the full assembly preserves its exact accumulation order. Temporary
    assembly therefore uses 4N, while returned matrices and the solve use 3N.
    """
    lifted = []
    strain = [0, 1, 5]
    electric = [0, 1]
    for material in materials:
        if material.C.shape != (3,3) or material.e.shape != (2,3) or material.eps.shape != (2,2):
            raise ValueError('ME0 requires projected xy tensors: C3x3, e2x3, eps2x2')
        C = np.zeros((6,6), dtype=material.C.dtype)
        e = np.zeros((3,6), dtype=material.e.dtype)
        eps = np.zeros((3,3), dtype=material.eps.dtype)
        C[np.ix_(strain,strain)] = material.C
        e[np.ix_(electric,strain)] = material.e
        eps[np.ix_(electric,electric)] = material.eps
        lifted.append(Material(material.rho,C,e,eps))
    K, M = assemble(model,lifted,elem_mat_idx,pml_regions,omega_top)
    n = model.N
    keep = np.r_[0:2*n,3*n:4*n]
    return K[keep][:,keep].tocsr(), M[keep][:,keep].tocsr()
