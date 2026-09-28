"""边界条件、约束凝聚与频率扫描求解。

对应 MATLAB 的 ``boundary_idx_2D[SF].m`` / ``boundaryPeriodic2D.m`` /
悬浮电势凝聚 / ``forces.m`` / ``solution.m`` 以及扫频循环。

两类算例统一处理
----------------
* **SP（单周期单元）**：周期（Bloch）边界 —— 右边界自由度按 y 对应并入左边界。
* **FP（有限器件）**：悬浮电势边界 —— XFL / XFR 各自所有节点共享一个电势。

两者都写成「主-从自由度合并」：构造合并变换 ``T``，``A_merged = Tᵀ A T``。

求解后端
--------
每个频点求解复数稀疏系统 ``A = -omega^2 M + K``。``A`` 用实数分块
``[[Ar,-Ai],[Ai,Ar]]`` 转为实数系统，交由 MKL PARDISO（pypardiso）直解：
所有频点稀疏模式相同，PARDISO 自动复用符号分解。
扫频可并行（``n_jobs`` > 1，类似 MATLAB ``parfor``）。
"""

from __future__ import annotations

import os
import multiprocessing as mp
import numpy as np
import scipy.sparse as sp

from .piezo_fem import Model

try:
    from pypardiso import PyPardisoSolver
    _HAVE_PARDISO = True
except Exception:                                          # pragma: no cover
    _HAVE_PARDISO = False
    import scipy.sparse.linalg as spla


# ---------------------------------------------------------------------------
# 边界自由度构建：返回 (fix, zheng, fu, merge_groups)
# ---------------------------------------------------------------------------
def bc_periodic(model: Model, lines: np.ndarray,
                tag_bottom=21, tag_left=19, tag_right=20,
                tag_zheng=17, tag_fu=18, ndisp: int = 3):
    """SP 算例：周期（Bloch）边界。

    ``ndisp`` —— 位移分量数：ME=1 取 3，ME=0 取 2
    （自由度排布 ``[ux | uy | (uz) | phi]``，phi 偏移 ``ndisp*N``）。
    """
    N = model.N
    bottom = model.nodes_with_tag(tag_bottom, lines)
    left = model.nodes_with_tag(tag_left, lines)
    right = model.nodes_with_tag(tag_right, lines)
    zheng = model.nodes_with_tag(tag_zheng, lines)
    fu = model.nodes_with_tag(tag_fu, lines)

    c2L = np.intersect1d(bottom, left)
    c2R = np.intersect1d(bottom, right)
    L = np.setdiff1d(left, c2L)
    R = np.setdiff1d(right, c2R)
    L = L[np.argsort(model.pos_m[L, 1])]
    R = R[np.argsort(model.pos_m[R, 1])]
    if L.size != R.size:
        raise RuntimeError("左右周期边界节点数不一致")

    disp_L = [L + a * N for a in range(ndisp)]
    disp_R = [R + a * N for a in range(ndisp)]
    L1 = np.concatenate(disp_L + [L + ndisp * N, c2L + ndisp * N])
    R1 = np.concatenate(disp_R + [R + ndisp * N, c2R + ndisp * N])
    merge_groups = [np.array([lm, rs]) for lm, rs in zip(L1, R1)]

    fix = np.concatenate([bottom + a * N for a in range(ndisp)])
    return fix, zheng + ndisp * N, fu + ndisp * N, merge_groups


def bc_floating(model: Model, lines: np.ndarray,
                tag_bottom=7, tag_XFL=3, tag_XFR=4,
                tag_zheng=5, tag_fu=6, ndisp: int = 3):
    """FP 算例：有限器件 + 悬浮电势边界。

    ``ndisp`` —— 位移分量数（ME=1 为 3，ME=0 为 2）。
    """
    N = model.N
    bottom = model.nodes_with_tag(tag_bottom, lines)
    XFL = model.nodes_with_tag(tag_XFL, lines)
    XFR = model.nodes_with_tag(tag_XFR, lines)
    zheng = model.nodes_with_tag(tag_zheng, lines)
    fu = model.nodes_with_tag(tag_fu, lines)

    fix = np.concatenate([bottom + a * N for a in range(ndisp)])
    merge_groups = [XFL + ndisp * N, XFR + ndisp * N]      # 等电势整组合并
    return fix, zheng + ndisp * N, fu + ndisp * N, merge_groups


# ---------------------------------------------------------------------------
# 合并变换
# ---------------------------------------------------------------------------
def _merge_transform(gdof: int, merge_groups):
    """由主-从合并组构造变换矩阵 ``T``：``A_merged = Tᵀ A T``。

    用并查集（union-find）处理跨组共享节点的情况（例如 3D 周期边界中的
    角点既在 L-R 对里又在 F-B 对里 —— 整个等价类最终并入单一主自由度）。
    """
    nodes = set()
    pairs = []                                             # list of (slave, master)
    for g in merge_groups:
        g = np.asarray(g, dtype=int)
        if g.size == 0:
            continue
        nodes.update(int(x) for x in g)
        m = int(g[0])
        for s in g[1:]:
            pairs.append((int(s), m))

    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # 合并时把从节点的根指向主节点的根（保留先列出的主节点为最终代表）
    for s, m in pairs:
        rs, rm = find(s), find(m)
        if rs != rm:
            parent[rs] = rm

    slaves, masters = [], []
    is_slave = np.zeros(gdof, dtype=bool)
    for n in nodes:
        r = find(n)
        if r != n:
            slaves.append(n)
            masters.append(r)
            is_slave[n] = True
    slaves = np.array(slaves, dtype=int)
    masters = np.array(masters, dtype=int)

    keep = np.where(~is_slave)[0]
    rows = np.concatenate([keep, slaves])
    cols = np.concatenate([keep, masters])
    T = sp.coo_matrix((np.ones(rows.size), (rows, cols)),
                      shape=(gdof, gdof)).tocsr()
    return T, slaves, masters


# ---------------------------------------------------------------------------
# 3D 边界条件
# ---------------------------------------------------------------------------
def _sort_by_yz(nodes: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """按 (y, z) 字典序对节点排序（用于 L↔R 3D 配对）。
    对应 MATLAB ``SortLR_3d``：原代码主键为 y、次键为 z（用复数虚部表达）。
    """
    nodes = np.asarray(nodes, dtype=int)
    if nodes.size == 0:
        return nodes
    y = np.round(pos[nodes, 1] * 1e10).astype(np.int64)
    z = np.round(pos[nodes, 2] * 1e10).astype(np.int64)
    return nodes[np.lexsort((z, y))]                       # 主键 y，次键 z


def _sort_by_xz(nodes: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """按 (x, z) 字典序对节点排序（用于 F↔B 3D 配对）。"""
    nodes = np.asarray(nodes, dtype=int)
    if nodes.size == 0:
        return nodes
    x = np.round(pos[nodes, 0] * 1e10).astype(np.int64)
    z = np.round(pos[nodes, 2] * 1e10).astype(np.int64)
    return nodes[np.lexsort((z, x))]


def bc_periodic_3D(model, faces: np.ndarray,
                   tag_left=1, tag_right=2, tag_back=3, tag_front=4,
                   tag_bottom=5, tag_zheng=7, tag_fu=8):
    """SP_3D 算例：x（左右）+ y（前后）两向周期 + 底部 z 固定。

    对应 MATLAB ``boundary_idx3D.m`` + ``boundaryPeriodic1_3D.m``，仔细消去
    边界交集以避免重复合并（角点等价类由 ``_merge_transform`` 的并查集解决）。
    """
    N = model.N
    nwt = model.nodes_with_face_tag
    L = nwt(tag_left, faces)
    R = nwt(tag_right, faces)
    Front = nwt(tag_front, faces)
    Back = nwt(tag_back, faces)
    Bottom = nwt(tag_bottom, faces)
    zheng = nwt(tag_zheng, faces)
    fu = nwt(tag_fu, faces)
    pos = model.pos_m

    # 前后面：去掉电极
    frontZ = np.intersect1d(Front, zheng); backZ = np.intersect1d(Back, zheng)
    frontF = np.intersect1d(Front, fu);    backF = np.intersect1d(Back, fu)
    Front_ = np.setdiff1d(Front, np.concatenate([frontZ, frontF]))
    Back_ = np.setdiff1d(Back, np.concatenate([backZ, backF]))

    # 底边交集
    gam2F = np.intersect1d(Bottom, Front_)
    gam2B = np.intersect1d(Bottom, Back_)
    gam2L = np.intersect1d(Bottom, L)
    gam2R = np.intersect1d(Bottom, R)

    # 角点：底-左-后、底-右-后
    LBe = np.intersect1d(L, Back_)
    RBe = np.intersect1d(R, Back_)
    gam2Lb = np.intersect1d(Bottom, LBe)
    gam2Rb = np.intersect1d(Bottom, RBe)
    gam2L_e = np.setdiff1d(gam2L, gam2Lb)
    gam2R_e = np.setdiff1d(gam2R, gam2Rb)

    # 前后面：去掉底边
    Front_ = np.setdiff1d(Front_, gam2F)
    Back_ = np.setdiff1d(Back_, gam2B)
    # 左右面：去掉底边
    L_ = np.setdiff1d(L, gam2L)
    R_ = np.setdiff1d(R, gam2R)
    # 左右面：去掉与后面相交的边（其余角点保留在 L_/R_ 中）
    L_ = np.setdiff1d(L_, np.intersect1d(L_, Back_))
    R_ = np.setdiff1d(R_, np.intersect1d(R_, Back_))

    # 对称排序，保证 L[k]↔R[k]、F[k]↔B[k] 一一对应
    L_ = _sort_by_yz(L_, pos);     R_ = _sort_by_yz(R_, pos)
    Front_ = _sort_by_xz(Front_, pos); Back_ = _sort_by_xz(Back_, pos)
    gam2F = _sort_by_xz(gam2F, pos);   gam2B = _sort_by_xz(gam2B, pos)
    gam2L_e = _sort_by_yz(gam2L_e, pos); gam2R_e = _sort_by_yz(gam2R_e, pos)
    frontZ = _sort_by_xz(frontZ, pos); backZ = _sort_by_xz(backZ, pos)
    frontF_ = _sort_by_xz(frontF, pos); backF_ = _sort_by_xz(backF, pos)

    merge_groups = []

    # 力学 F↔B（含落在前/后面的电极节点）
    def pair_disp(A, B_, n=3):
        for a, b in zip(A, B_):
            for c in range(n):
                merge_groups.append(np.array([a + c * N, b + c * N]))
    pair_disp(Front_, Back_)
    pair_disp(frontZ, backZ)
    pair_disp(frontF_, backF_)
    # 力学 L↔R
    pair_disp(L_, R_)

    # 静电 F↔B（前后面 + 底-前/底-后边）
    def pair_phi(A, B_):
        for a, b in zip(A, B_):
            merge_groups.append(np.array([a + 3 * N, b + 3 * N]))
    pair_phi(Front_, Back_)
    pair_phi(gam2F, gam2B)
    # 静电 L↔R（L+ 底-左边 ↔ R+ 底-右边）
    pair_phi(L_, R_)
    pair_phi(gam2L_e, gam2R_e)

    fix = np.concatenate([Bottom, Bottom + N, Bottom + 2 * N])
    return fix, zheng + 3 * N, fu + 3 * N, merge_groups


def _realblock(A: sp.spmatrix) -> sp.csr_matrix:
    """复数稀疏矩阵 -> 等价实数分块 ``[[Ar,-Ai],[Ai,Ar]]``。"""
    Ar = A.real
    Ai = A.imag
    out = sp.bmat([[Ar, -Ai], [Ai, Ar]], format="csr")
    out.sort_indices()
    return out


# 并行扫频：worker 通过 fork 继承父进程的求解器（写时复制）
_SWEEP_SOLVER = None


def _sweep_worker(arg):
    omega, V = arg
    _, Q, Y = _SWEEP_SOLVER.solve(omega, V)
    return Q, Y


class FrequencySolver:
    """压电耦合算例的频率扫描求解器（周期 / 悬浮电势统一处理）。

    一次组装、多次扫频。所有频点共用同一稀疏模式，
    实数分块矩阵 ``Km2`` / ``Mm2`` 预先构造，每个频点只做
    ``A2 = Km2 - omega^2 Mm2`` 的数值更新与一次 PARDISO 直解。
    """

    def __init__(self, K: sp.spmatrix, M: sp.spmatrix,
                 fix: np.ndarray, zheng: np.ndarray, fu: np.ndarray,
                 merge_groups):
        self.K = K.tocsr()
        gdof = K.shape[0]
        self.gdof = gdof
        self.zheng = np.asarray(zheng, dtype=int)
        self.fu = np.asarray(fu, dtype=int)

        T, self.slaves, self.masters = _merge_transform(gdof, merge_groups)
        Km = (T.T @ self.K @ T).tocsr()
        Mm = (T.T @ M.tocsr() @ T).tocsr()

        prescribed = np.unique(np.concatenate(
            [fix, self.slaves, self.zheng, self.fu]))
        self.active = np.setdiff1d(np.arange(gdof), prescribed)
        self.n_active = self.active.size

        s = np.zeros(gdof)
        s[self.zheng] = 1.0                                # 信号电极指示向量
        self.Km_s = np.asarray(Km @ s).ravel()
        self.Mm_s = np.asarray(Mm @ s).ravel()
        self.kts = np.asarray(self.K.T @ s).ravel()        # Q = kts . disp

        # 凝聚后的有源子矩阵；A = Km_aa - omega^2 Mm_aa 的稀疏模式与频率无关
        self.Km_aa = Km[self.active][:, self.active].tocsr()
        self.Mm_aa = Mm[self.active][:, self.active].tocsr()

        self._pardiso = None
        self._pardiso_pid = None

    # -- 后端：每进程独立的 PARDISO 求解器（fork 安全）--
    def _backend(self):
        if not _HAVE_PARDISO:
            return None
        pid = os.getpid()
        if self._pardiso is None or self._pardiso_pid != pid:
            self._pardiso = PyPardisoSolver()
            self._pardiso_pid = pid
        return self._pardiso

    def solve(self, omega: float, V: float = 1.0):
        """求解单个角频率 ``omega``，返回 ``(disp, Q, Y)``。"""
        w2 = omega ** 2
        rhs = -(self.Km_s - w2 * self.Mm_s)[self.active] * V
        n = self.n_active

        # A = -omega^2 M + K（有源块）；实数分块后稀疏模式与频率无关
        A2 = _realblock((self.Km_aa - w2 * self.Mm_aa).tocsr())
        b2 = np.concatenate([rhs.real, rhs.imag])

        ps = self._backend()
        if ps is not None:
            z2 = ps.solve(A2, b2)
        else:                                              # 退化：scipy 直解
            z2 = spla.spsolve(A2.tocsc(), b2)
        x = z2[:n] + 1j * z2[n:]

        disp = np.zeros(self.gdof, dtype=complex)
        disp[self.active] = x
        disp[self.slaves] = disp[self.masters]             # 从自由度并入主自由度
        disp[self.zheng] = V
        disp[self.fu] = 0.0

        Q = self.kts @ disp
        Y = abs(1j * omega * Q / V)
        return disp, Q, Y

    def sweep(self, fre, V: float = 1.0, n_jobs: int = 1, progress: bool = True):
        """对频率数组 ``fre``（Hz）扫频，返回 ``(Q, Y)``。

        ``n_jobs > 1`` 时按频点并行（multiprocessing，类似 MATLAB ``parfor``）。
        """
        fre = np.asarray(fre, dtype=float)
        omegas = 2 * np.pi * fre

        if n_jobs == 1:
            Q = np.zeros(fre.size, dtype=complex)
            Y = np.zeros(fre.size, dtype=float)
            for k, om in enumerate(omegas):
                _, Q[k], Y[k] = self.solve(om, V)
                if progress and (k % 25 == 0 or k == fre.size - 1):
                    print(f"  扫频 {k + 1:4d}/{fre.size}  "
                          f"f = {fre[k] * 1e-9:.4f} GHz  |Y| = {Y[k]:.4g}")
            return Q, Y

        global _SWEEP_SOLVER
        _SWEEP_SOLVER = self                               # fork 子进程继承
        if progress:
            print(f"  并行扫频：{fre.size} 个频点，{n_jobs} 进程 ...")
        with mp.get_context("fork").Pool(n_jobs) as pool:
            res = pool.map(_sweep_worker, [(om, V) for om in omegas],
                           chunksize=4)
        Q = np.array([r[0] for r in res], dtype=complex)
        Y = np.array([r[1] for r in res], dtype=float)
        return Q, Y
