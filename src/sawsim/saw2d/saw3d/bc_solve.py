"""Periodic (Bloch) boundary conditions, load vector and linear solve.

Ports ``boundaryPeriodic1_3D.m``, ``forces.m`` and ``solution.m``.

``boundaryPeriodic1_3D`` folds the slave periodic DOFs onto their masters with a
sequence of in-place row/column additions.  Restricted to the DOFs that survive
into the reduced solve this is *exactly* the Galerkin projection ``T' A T`` with
a 0/1 connectivity matrix ``T`` (slave = master).

The MATLAB routine folds in **two stages** -- first front<->back, then
left<->right -- and the second stage operates on the result of the first.  This
ordering matters: the front-right edge nodes belong to ``period_F`` (a stage-1
master) *and* ``period_R`` (a stage-2 slave), so they form a fold chain
B -> F -> L that only resolves when the two operators are applied in sequence.
We therefore build two operators ``T_fb`` and ``T_lr`` and apply them in order.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve


def _fold_operator(slaves, masters, gdof):
    """0/1 matrix ``T`` (gdof x gdof): slave DOF takes its paired master's value."""
    is_slave = np.zeros(gdof, dtype=bool)
    is_slave[slaves] = True
    free = np.where(~is_slave)[0]
    rows = np.concatenate([free, slaves])
    cols = np.concatenate([free, masters])
    data = np.ones(rows.size)
    return sp.coo_matrix((data, (rows, cols)), shape=(gdof, gdof)).tocsr()


def build_periodic_operators(boundary, gdof):
    """Return ``(T_fb, T_lr)`` -- the front/back then left/right fold operators."""
    m = boundary.machine
    e = boundary.electric
    t_fb = _fold_operator(np.concatenate([m["period_B"], e["period_B"]]),
                          np.concatenate([m["period_F"], e["period_F"]]), gdof)
    t_lr = _fold_operator(np.concatenate([m["period_R"], e["period_R"]]),
                          np.concatenate([m["period_L"], e["period_L"]]), gdof)
    return t_fb, t_lr


def prescribed_dofs(boundary):
    """DOFs eliminated from the reduced system (fixed / slave / prescribed)."""
    m = boundary.machine
    e = boundary.electric
    return np.unique(np.concatenate([
        m["fix"], m["period_B"], m["period_R"],
        e["period_R"], e["period_B"], e["zheng"], e["fu"]]))


def apply_periodic_values(disp, boundary, voltage):
    """Copy master DOF values onto their slaves and set the prescribed potentials.

    Port of the post-solve assignment block in ``Solve3DSAW.m``.
    """
    m, e = boundary.machine, boundary.electric
    disp[m["period_R"]] = disp[m["period_L"]]
    disp[m["period_B"]] = disp[m["period_F"]]
    disp[e["period_R"]] = disp[e["period_L"]]
    disp[e["period_B"]] = disp[e["period_F"]]
    disp[e["zheng"]] = voltage
    disp[e["fu"]] = 0.0
    return disp


def lu_solve_active(a_aa, rhs):
    """Solve the reduced linear system; thin wrapper around ``spsolve``."""
    return spsolve(a_aa.tocsc(), rhs)


# ---------------------------------------------------------------------------
# 3D 频率扫描求解器（与 2D ``saw2d.sweep.FrequencySolver`` 同款加速策略：
#   * 复数系统经实数分块 [[Ar,-Ai],[Ai,Ar]] 交给 MKL PARDISO
#   * 各频点稀疏模式相同 -> PyPardisoSolver 自动复用符号分解
#   * ``n_jobs > 1`` 时多进程并行（fork 继承大矩阵，无序列化开销）
# ---------------------------------------------------------------------------
import os
import multiprocessing as mp

try:
    from pypardiso import PyPardisoSolver
    _HAVE_PARDISO = True
except Exception:                                          # pragma: no cover
    _HAVE_PARDISO = False


def _realblock(A: sp.spmatrix) -> sp.csr_matrix:
    Ar, Ai = A.real, A.imag
    out = sp.bmat([[Ar, -Ai], [Ai, Ar]], format="csr")
    out.sort_indices()
    return out


# 并行扫频共享对象（fork 子进程通过写时复制继承）
_SWEEP_3D = None


def _sweep_3d_worker(arg):
    omega, voltage = arg
    return _SWEEP_3D.solve(omega, voltage)[1:]             # (Q, Y)


class FrequencySolver3D:
    """3D 算例的频率扫描求解器（K / M 已经包含两步周期折叠）。

    Parameters
    ----------
    K, M : scipy.sparse
        **原始**全局刚度 / 质量（未折叠）。Q 的计算需要原 K。
    boundary :
        :func:`boundary_idx_vect_3ds` 返回的边界自由度容器。
    t_fb, t_lr : scipy.sparse
        两步周期折叠算子（来自 :func:`build_periodic_operators`）。
    """

    def __init__(self, K, M, boundary, t_fb, t_lr):
        self.K = K.tocsr()
        self.M = M.tocsr()
        self.boundary = boundary
        self.gdof = K.shape[0]

        # 折叠后矩阵（频率无关，只做一次）
        k_fold = (t_lr.T @ (t_fb.T @ self.K @ t_fb) @ t_lr).tocsr()
        m_fold = (t_lr.T @ (t_fb.T @ self.M @ t_fb) @ t_lr).tocsr()

        prescribed = prescribed_dofs(boundary)
        self.active = np.setdiff1d(np.arange(self.gdof), prescribed)
        self.zheng = boundary.electric["zheng"]
        self.n_act = self.active.size

        self.k_aa = k_fold[self.active][:, self.active].tocsc()
        self.m_aa = m_fold[self.active][:, self.active].tocsc()
        self.k_az = k_fold[self.active][:, self.zheng]
        self.m_az = m_fold[self.active][:, self.zheng]
        self.kz_rows = self.K[self.zheng, :].tocsr()       # 原 K 行用于 Q

        self._pardiso = None
        self._pardiso_pid = None

    def _backend(self):
        if not _HAVE_PARDISO:
            return None
        pid = os.getpid()
        if self._pardiso is None or self._pardiso_pid != pid:
            self._pardiso = PyPardisoSolver()
            self._pardiso_pid = pid
        return self._pardiso

    def solve(self, omega: float, voltage: float = 1.0):
        a_aa = (self.k_aa - omega ** 2 * self.m_aa).tocsc()
        a_az = self.k_az - omega ** 2 * self.m_az
        rhs = -voltage * np.asarray(a_az.sum(axis=1)).ravel()

        ps = self._backend()
        n = self.n_act
        if ps is not None:
            A2 = _realblock(a_aa)
            b2 = np.concatenate([rhs.real, rhs.imag])
            z2 = ps.solve(A2, b2)
            u = z2[:n] + 1j * z2[n:]
        else:
            u = spsolve(a_aa, rhs)

        disp = np.zeros(self.gdof, dtype=complex)
        disp[self.active] = u
        apply_periodic_values(disp, self.boundary, voltage)

        Q = (self.kz_rows @ disp).sum()
        Y = abs(1j * omega * Q / voltage)
        return disp, Q, Y

    def sweep(self, fre, voltage: float = 1.0, n_jobs: int = 1,
              progress: bool = True):
        """扫频，返回 ``(Q, Y)``；``n_jobs>1`` 时按频点多进程并行。"""
        fre = np.asarray(fre, dtype=float)
        omegas = 2.0 * np.pi * fre

        if n_jobs == 1:
            Q = np.zeros(fre.size, dtype=complex)
            Y = np.zeros(fre.size, dtype=float)
            for k, om in enumerate(omegas):
                _, Q[k], Y[k] = self.solve(om, voltage)
                if progress and (k % 100 == 0 or k == fre.size - 1):
                    print(f"  扫频 {k + 1:4d}/{fre.size}  "
                          f"f = {fre[k] * 1e-9:.4f} GHz  |Y| = {Y[k]:.4e}")
            return Q, Y

        global _SWEEP_3D
        _SWEEP_3D = self                                   # fork 子进程继承
        if progress:
            print(f"  并行扫频：{fre.size} 个频点，{n_jobs} 进程 ...")
        with mp.get_context("fork").Pool(n_jobs) as pool:
            res = pool.map(_sweep_3d_worker,
                           [(om, voltage) for om in omegas], chunksize=4)
        Q = np.array([r[0] for r in res], dtype=complex)
        Y = np.array([r[1] for r in res], dtype=float)
        return Q, Y


# ===========================================================================
# FP（有限器件）3D 求解器：F↔B 单向周期 + XFL / XFR 悬浮电势凝聚。
#
# 关键观察：MATLAB ``Boundary_idx3DF`` 把 XFL/XFR 节点的**电势 DOF**单独放在
# ``Boundary.electric.XFL/XFR``，并**不**进入 ``electric.period_F/B``；
# 而它们的**位移 DOF**则跟随其他 front/back 节点参与 F↔B 周期。
# 于是 T_fb（F↔B 折叠）与 T_float（XFL/XFR → 主节点）作用在不相交的 DOF
# 集合上，可以像 SP 的两步折叠一样按顺序应用。
# ===========================================================================
def build_periodic_operators_fp(boundary, gdof):
    """Return ``(T_fb, T_float)`` for FP: F↔B fold + XFL/XFR equipotential fold."""
    m = boundary.machine
    e = boundary.electric
    t_fb = _fold_operator(np.concatenate([m["period_B"], e["period_B"]]),
                          np.concatenate([m["period_F"], e["period_F"]]), gdof)

    xfl, xfr = e["XFL"], e["XFR"]
    parts_s, parts_m = [], []
    if xfl.size > 1:
        parts_s.append(xfl[1:])
        parts_m.append(np.full(xfl.size - 1, xfl[0]))
    if xfr.size > 1:
        parts_s.append(xfr[1:])
        parts_m.append(np.full(xfr.size - 1, xfr[0]))
    slaves = np.concatenate(parts_s) if parts_s else np.array([], dtype=np.int64)
    masters = np.concatenate(parts_m) if parts_m else np.array([], dtype=np.int64)
    t_float = _fold_operator(slaves, masters, gdof)
    return t_fb, t_float


def prescribed_dofs_fp(boundary):
    """Eliminated DOFs for the FP reduced system."""
    m = boundary.machine
    e = boundary.electric
    xfl, xfr = e["XFL"], e["XFR"]
    return np.unique(np.concatenate([
        m["fix"], m["period_B"], e["period_B"],
        xfl[1:] if xfl.size > 1 else np.array([], dtype=np.int64),
        xfr[1:] if xfr.size > 1 else np.array([], dtype=np.int64),
        e["zheng"], e["fu"]]))


def apply_periodic_values_fp(disp, boundary, voltage):
    """Post-solve assignment for FP: copy F→B and XFL/XFR equipotentials, set V/0."""
    m, e = boundary.machine, boundary.electric
    disp[m["period_B"]] = disp[m["period_F"]]
    disp[e["period_B"]] = disp[e["period_F"]]
    xfl, xfr = e["XFL"], e["XFR"]
    if xfl.size > 1:
        disp[xfl[1:]] = disp[xfl[0]]
    if xfr.size > 1:
        disp[xfr[1:]] = disp[xfr[0]]
    disp[e["zheng"]] = voltage
    disp[e["fu"]] = 0.0
    return disp


class FrequencySolver3D_FP:
    """FP 3D 频率扫描求解器。

    与 :class:`FrequencySolver3D` 同款加速策略（PARDISO + fork 并行扫频），
    只是预折叠用 ``T_fb @ T_float`` 替换 ``T_fb @ T_lr``，prescribed/post-solve
    走 FP 版本。
    """

    def __init__(self, K, M, boundary, t_fb, t_float):
        self.K = K.tocsr()
        self.M = M.tocsr()
        self.boundary = boundary
        self.gdof = K.shape[0]

        k_fold = (t_float.T @ (t_fb.T @ self.K @ t_fb) @ t_float).tocsr()
        m_fold = (t_float.T @ (t_fb.T @ self.M @ t_fb) @ t_float).tocsr()

        prescribed = prescribed_dofs_fp(boundary)
        self.active = np.setdiff1d(np.arange(self.gdof), prescribed)
        self.zheng = boundary.electric["zheng"]
        self.n_act = self.active.size

        self.k_aa = k_fold[self.active][:, self.active].tocsc()
        self.m_aa = m_fold[self.active][:, self.active].tocsc()
        self.k_az = k_fold[self.active][:, self.zheng]
        self.m_az = m_fold[self.active][:, self.zheng]
        self.kz_rows = self.K[self.zheng, :].tocsr()

        self._pardiso = None
        self._pardiso_pid = None

    def _backend(self):
        if not _HAVE_PARDISO:
            return None
        pid = os.getpid()
        if self._pardiso is None or self._pardiso_pid != pid:
            self._pardiso = PyPardisoSolver()
            self._pardiso_pid = pid
        return self._pardiso

    def solve(self, omega: float, voltage: float = 1.0):
        a_aa = (self.k_aa - omega ** 2 * self.m_aa).tocsc()
        a_az = self.k_az - omega ** 2 * self.m_az
        rhs = -voltage * np.asarray(a_az.sum(axis=1)).ravel()

        ps = self._backend()
        n = self.n_act
        if ps is not None:
            A2 = _realblock(a_aa)
            b2 = np.concatenate([rhs.real, rhs.imag])
            z2 = ps.solve(A2, b2)
            u = z2[:n] + 1j * z2[n:]
        else:
            u = spsolve(a_aa, rhs)

        disp = np.zeros(self.gdof, dtype=complex)
        disp[self.active] = u
        apply_periodic_values_fp(disp, self.boundary, voltage)

        Q = (self.kz_rows @ disp).sum()
        Y = abs(1j * omega * Q / voltage)
        return disp, Q, Y

    def sweep(self, fre, voltage: float = 1.0, n_jobs: int = 1,
              progress: bool = True):
        """扫频；与 SP 版本同款并行（fork 共享 ``_SWEEP_3D`` 全局）。"""
        fre = np.asarray(fre, dtype=float)
        omegas = 2.0 * np.pi * fre

        if n_jobs == 1:
            Q = np.zeros(fre.size, dtype=complex)
            Y = np.zeros(fre.size, dtype=float)
            for k, om in enumerate(omegas):
                _, Q[k], Y[k] = self.solve(om, voltage)
                if progress and (k % 20 == 0 or k == fre.size - 1):
                    print(f"  扫频 {k + 1:4d}/{fre.size}  "
                          f"f = {fre[k] * 1e-9:.4f} GHz  |Y| = {Y[k]:.4e}")
            return Q, Y

        global _SWEEP_3D
        _SWEEP_3D = self
        if progress:
            print(f"  并行扫频：{fre.size} 个频点，{n_jobs} 进程 ...")
        with mp.get_context("fork").Pool(n_jobs) as pool:
            res = pool.map(_sweep_3d_worker,
                           [(om, voltage) for om in omegas], chunksize=4)
        Q = np.array([r[0] for r in res], dtype=complex)
        Y = np.array([r[1] for r in res], dtype=float)
        return Q, Y
