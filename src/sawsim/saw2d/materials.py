"""材料库：晶体张量、欧拉角旋转与材料参数。

对应 MATLAB 的 ``oulaTransfer.m`` / ``ComputingC.m`` /
``initial_material_parameters_ME.m``。

本模块只实现 **ME=1（2.5D / 模态扩展）** 所需的全张量形式：
每个材料给出 ``C`` (6x6)、``e`` (3x6)、``eps`` (3x3)、``rho``。
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

EPS0 = 8.854e-12  # 真空介电常数 F/m


@dataclass
class Material:
    """单一材料的本构参数（器件坐标系下，已完成欧拉角旋转）。"""

    rho: float           # 密度 kg/m^3
    C: np.ndarray        # 刚度矩阵 6x6 (Pa)
    e: np.ndarray        # 压电耦合 3x6 (C/m^2)
    eps: np.ndarray      # 介电常数 3x3 (F/m)


def oula_transfer(oula, C_xtal, e_xtal, eps_xtal):
    """欧拉角旋转：把晶轴张量旋转到器件坐标系。

    使用 内禀 ZXZ：A = Rz(alpha) Rx(beta) Rz(gamma)。
    A 将源材料坐标中的分量映射到器件（全局）坐标；不同于历史 MATLAB 欧拉角符号及次序。

    Parameters
    ----------
    oula : array_like, shape (3,)
        欧拉角 [alpha, beta, gamma]（API 别名 phi, theta, psi），单位 **度**。
    C_xtal : ndarray (6,6)
    e_xtal : ndarray (3,6)
    eps_xtal : ndarray (3,3)

    Returns
    -------
    (C, e, eps) : 旋转后的张量。
    """
    a = rotation_matrix(oula)

    M1 = a ** 2
    M2 = np.column_stack([2 * a[:, 1] * a[:, 2],
                          2 * a[:, 0] * a[:, 2],
                          2 * a[:, 0] * a[:, 1]])
    M3 = np.vstack([a[1, :] * a[2, :],
                    a[0, :] * a[2, :],
                    a[0, :] * a[1, :]])
    M4 = np.array([
        [a[1, 1] * a[2, 2] + a[1, 2] * a[2, 1],
         a[1, 0] * a[2, 2] + a[1, 2] * a[2, 0],
         a[1, 1] * a[2, 0] + a[1, 0] * a[2, 1]],
        [a[0, 1] * a[2, 2] + a[0, 2] * a[2, 1],
         a[0, 2] * a[2, 0] + a[0, 0] * a[2, 2],
         a[0, 0] * a[2, 1] + a[0, 1] * a[2, 0]],
        [a[0, 1] * a[1, 2] + a[0, 2] * a[1, 1],
         a[0, 2] * a[1, 0] + a[0, 0] * a[1, 2],
         a[0, 0] * a[1, 1] + a[0, 1] * a[1, 0]],
    ])
    M = np.block([[M1, M2], [M3, M4]])

    C = M @ C_xtal @ M.T
    e = a @ e_xtal @ M.T
    eps = a @ eps_xtal @ a.T
    return C, e, eps


def computing_C_isotropic(nu: float, E: float) -> np.ndarray:
    """各向同性材料的 6x6 刚度矩阵（对应 MATLAB ``ComputingC.m``）。"""
    f = E / ((1 - 2 * nu) * (1 + nu))
    c11, c12 = (1 - nu) * f, nu * f
    c44 = E / 2 / (1 + nu)
    C = np.zeros((6, 6))
    C[:3, :3] = c12
    C[0, 0] = C[1, 1] = C[2, 2] = c11
    C[3, 3] = C[4, 4] = C[5, 5] = c44
    return C


# ---------------------------------------------------------------------------
# 晶体常数（与 initial_material_parameters_ME.m 完全一致）
# ---------------------------------------------------------------------------
_C_LN = np.array([
    [2.32966e11, 4.68904e10, 8.02342e10, -1.10267e10, 0, 0],
    [4.68904e10, 2.32966e11, 8.02342e10, 1.10267e10, 0, 0],
    [8.02342e10, 8.02342e10, 2.75364e11, 0, 0, 0],
    [-1.10267e10, 1.10267e10, 0, 9.38995e10, 0, 0],
    [0, 0, 0, 0, 9.38995e10, -1.10267e10],
    [0, 0, 0, 0, -1.10267e10, 9.3038e10],
])
_E_LN = np.array([
    [0, 0, 0, 0, 2.59576, -1.58923],
    [-1.58923, 1.58923, 0, 2.59576, 0, 0],
    [0.0821598, 0.0821598, 1.88197, 0, 0, 0],
])
_EPS_LN = np.diag([40.9, 40.9, 43.3]) * EPS0


def material_set_ME(oula=(0.0, -42.0, 0.0)):
    """返回 SP_2D_1ceng / FP_2D_1ceng 等单层算例的材料库 ``[衬底, 电极]``。

    与 ``initial_material_parameters_ME.m`` 对应：
    ``material[0]`` 为原 SP 基准压电数据（rho=7450，材料身份未核实；欧拉角 ``oula``），
    ``material[1]`` 为铝电极。
    """
    C, e, eps = oula_transfer(oula, _C_LN, _E_LN, _EPS_LN)
    substrate = Material(rho=7450.0, C=C, e=e, eps=eps)
    al = Material(
        rho=2700.0,
        C=computing_C_isotropic(nu=0.33, E=70e9),
        e=np.zeros((3, 6)),
        eps=np.eye(3) * EPS0,
    )
    return [substrate, al]


# ---------------------------------------------------------------------------
# 多层算例（ME=1）所需的额外材料
# ---------------------------------------------------------------------------
def _iso_ME(*, rho: float, E: float, nu: float, eps_r: float) -> Material:
    """各向同性 ME=1 材料（完整 6x6 刚度，e=0，eps=eps_r*eps0*I）。"""
    return Material(rho=rho, C=computing_C_isotropic(nu, E),
                    e=np.zeros((3, 6)),
                    eps=np.eye(3) * eps_r * EPS0)


# 各向异性单晶硅刚度（C44=51e9，与 MATLAB FP_2D_*ceng 一致）
_C_SI = np.array([
    [166e9, 64e9,  64e9,  0,    0,    0],
    [64e9,  195e9, 35e9,  0,    0,    0],
    [64e9,  35e9,  195e9, 0,    0,    0],
    [0,     0,     0,     51e9, 0,    0],
    [0,     0,     0,     0,    80e9, 0],
    [0,     0,     0,     0,    0,    80e9],
])


def _Si_aniso_ME(*, rho: float, eps_r: float) -> Material:
    """各向异性单晶硅 ME=1 材料。"""
    return Material(rho=rho, C=_C_SI.copy(),
                    e=np.zeros((3, 6)),
                    eps=np.eye(3) * eps_r * EPS0)


# 标准材料（用于多层算例）
def mat_LN(oula=(0.0, -42.0, 0.0)) -> Material:
    """历史兼容名称；原 SP 基准数据，材料身份未核实。"""
    return material_set_ME(oula)[0]


def mat_Al() -> Material:
    return material_set_ME()[1]


def mat_SiO2() -> Material:
    """SiO2（各向同性，E=70 GPa，nu=0.17，rho=2200，eps_r=4.2）。"""
    return _iso_ME(rho=2200.0, E=70e9, nu=0.17, eps_r=4.2)


def mat_PolySi(E: float = 169e9) -> Material:
    """Poly-Si（各向同性，nu=0.22，rho=2320，eps_r=4.5）；``E`` 默认 169 GPa。"""
    return _iso_ME(rho=2320.0, E=E, nu=0.22, eps_r=4.5)


def mat_Si_anisotropic(*, rho: float = 2329.0,
                       eps_r: float = 11.7) -> Material:
    """各向异性单晶硅（FP_*ceng 用）。"""
    return _Si_aniso_ME(rho=rho, eps_r=eps_r)


def mat_Si_isotropic() -> Material:
    """各向同性硅（SP_2D_4ceng 顶层 Si：E=170 GPa，nu=0.28，rho=2329，eps_r=11.7）。"""
    return _iso_ME(rho=2329.0, E=170e9, nu=0.28, eps_r=11.7)


# ---------------------------------------------------------------------------
# 2D 平面分析（ME=0）所需的材料：C 为 3x3, e 为 2x3, eps 为 2x2
# ---------------------------------------------------------------------------
def computing_C_2D(nu: float, E: float) -> np.ndarray:
    """ComputingC2D.m 等价：6x6 各向同性 -> 3x3 (Voigt 1,2,6)。"""
    full = computing_C_isotropic(nu, E)
    return full[np.ix_([0, 1, 5], [0, 1, 5])]


def _iso_2D(*, rho: float, E: float, nu: float, eps_r: float) -> Material:
    """各向同性 ME=0 材料（3x3 C，2x3 e=0，2x2 eps）。"""
    return Material(rho=rho, C=computing_C_2D(nu, E),
                    e=np.zeros((2, 3)),
                    eps=np.eye(2) * eps_r * EPS0)


# TCSAW 用 LN-like 压电晶体张量（已在器件坐标系，取 Voigt 1,3,5 = xz 平面）
_C_TCSAW_LN = np.array([
    [198.39e9,    66.06504972696650e9, 53.78495027303350e9, 7.175389491196900e9, 0, 0],
    [66.06504972696650e9, 186.14867147956400e9, 80.48455717136180e9,
     5.542848560608170e9, 0, 0],
    [53.78495027303350e9, 80.48455717136180e9, 209.43221417771200e9,
     6.468545399123780e9, 0, 0],
    [7.175389491196900e9, 5.542848560608170e9, 6.468545399123780e9,
     75.00455717136180e9, 0, 0],
    [0, 0, 0, 0, 56.48843724569100e9, -3.684464518666250e9],
    [0, 0, 0, 0, -3.684464518666250e9, 74.99656275430900e9],
])
_E_TCSAW_LN = np.array([
    [0, 0, 0, 0, 4.40335738810247, 0.287999501116610],
    [-1.75215342736883, 4.56647020909682, -1.38801517685763,
     0.308578173488658, 0, 0],
    [1.69598300904214, -2.39879620557167, 2.59557935534160,
     0.652137751627810, 0, 0],
])
_EPS_TCSAW_LN = np.array([
    [45.6, 0, 0],
    [0, 38.6099004836340, -9.27617536580478],
    [0, -9.27617536580478, 33.2900995163660],
]) * EPS0


def mat_TCSAW_LN_2D(oula=(0.0, 0.0, 0.0)) -> Material:
    """TCSAW LN-like 压电衬底（ME=0，取 Voigt (1,3,5)=xz 平面，与 MATLAB 一致）。"""
    C, e, eps = oula_transfer(oula, _C_TCSAW_LN, _E_TCSAW_LN, _EPS_TCSAW_LN)
    idx_strain = [0, 2, 4]                                 # Voigt 1,3,5 -> 0,2,4
    idx_field = [0, 2]                                     # 电场分量 x,z
    return Material(rho=4628.0,
                    C=C[np.ix_(idx_strain, idx_strain)],
                    e=e[np.ix_(idx_field, idx_strain)],
                    eps=eps[np.ix_(idx_field, idx_field)])


def mat_Cu_2D() -> Material:
    """Cu 电极（ME=0，rho=8960，E=120 GPa，nu=0.34）。"""
    return _iso_2D(rho=8960.0, E=120e9, nu=0.34, eps_r=1.0)


def mat_SiO2_2D() -> Material:
    """SiO2（ME=0，rho=2200，E=70 GPa，nu=0.17，eps_r=4.2）。"""
    return _iso_2D(rho=2200.0, E=70e9, nu=0.17, eps_r=4.2)


def mat_SiN_2D() -> Material:
    """SiN（ME=0，rho=3100，E=160 GPa，nu=0.23，eps_r=9.7）。"""
    return _iso_2D(rho=3100.0, E=160e9, nu=0.23, eps_r=9.7)


def rotation_matrix(oula):
    """Intrinsic ZXZ, local/source-to-global/device, angles in degrees.

    ``oula = (alpha, beta, gamma)`` (API aliases phi, theta, psi), with
    A = Rz(alpha) Rx(beta) Rz(gamma). Historical angles (p, t, s) describe
    the same orientation as the new (-s, -t, -p), for identical source axes.
    """
    # Preserve source arithmetic order: Hex regression amplifies even 1 ulp
    # differences from np.deg2rad for the historical 48-degree orientation.
    alpha, beta, gamma = np.asarray(oula, dtype=float) * np.pi / 180.0
    def rz(angle):
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    c, s = np.cos(beta), np.sin(beta)
    rx = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    return rz(alpha) @ rx @ rz(gamma)


def selected_materials(substrate_id='sp_baseline', electrode_id='al', oula=(0.0,-42.0,0.0)):
    """Load versioned library data; task builders use their pinned snapshots."""
    from sawsim.material_library import get_record
    from sawsim.material_runtime import from_record
    substrate_record=get_record(substrate_id)
    electrode_record=get_record(electrode_id)
    if 'substrate' not in substrate_record['roles'] or 'electrode' not in electrode_record['roles']:
        raise ValueError('Material role mismatch')
    raw=from_record(substrate_record)
    C,e,eps=oula_transfer(oula,raw.C,raw.e,raw.eps)
    return [Material(raw.rho,C,e,eps),from_record(electrode_record)],raw


def project_xy_plane_strain(material):
    """Project already rotated full tensors to uz=0, Ez=0 in the device xy plane.

    Engineering shear is gamma_xy; no Schur complement (not plane stress).
    This is distinct from the historical TC-SAW xz-plane ME0 material helper.
    """
    strain = [0, 1, 5]
    electric = [0, 1]
    return Material(material.rho, material.C[np.ix_(strain,strain)],
                    material.e[np.ix_(electric,strain)],material.eps[np.ix_(electric,electric)])


def layer_material(material_id):
    """Load passive layer data from the local material library."""
    from sawsim.material_library import get_record
    from sawsim.material_runtime import from_record
    record=get_record(material_id)
    if 'layer' not in record['roles']:
        raise ValueError('Material is not a passive layer: '+material_id)
    return from_record(record)


def project_xz_plane_strain(material):
    """TC source xz plane mapped to local mesh xy, after source-frame rotation."""
    strain=[0,2,4]
    electric=[0,2]
    return Material(material.rho,material.C[np.ix_(strain,strain)],
                    material.e[np.ix_(electric,strain)],material.eps[np.ix_(electric,electric)])


def mat_Si_cubic_hex():
    """Original SP_3D_2ceng cubic Si dataset (not isotropic: C44 != (C11-C12)/2)."""
    C=np.zeros((6,6));C[:3,:3]=64e9
    C[0,0]=C[1,1]=C[2,2]=166e9
    C[3,3]=C[4,4]=C[5,5]=80e9
    return Material(2330.0,C,np.zeros((3,6)),np.eye(3)*11.68*EPS0)
