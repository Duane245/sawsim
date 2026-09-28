"""saw2d.saw3d —— 3D Hex27 压电耦合有限元（基于 P9_codes_vect_Python 移植）。

P9 的 3D 引擎是经过 MATLAB Y11.mat 完整校核过的实现（含 ``boundaryPeriodic1_3D``
顺序凝聚、``shapeFunctionsQ3D`` H27 形函数 + ``sortSF27`` 重排、
``formStiffnessMass3DPML*`` 的 6×6 PML 拉伸张量等细节）；
本子包直接复用这一套作为 P10 3D 算例的底层。

模块
----
mesh_io   —— Gmsh ``.m`` 网格解析（``msh.QUADS9`` 面 + ``msh.HEXAS27`` 体）
elements  —— Hex27 形函数与 3×3×3 高斯积分
boundary  —— 周期 BC 索引、L↔R / F↔B 对称排序
assembly  —— 向量化组装 K / M（含 PML、列缩放）
bc_solve  —— 两步 Bloch 折叠算子 ``T_fb``、``T_lr`` 与有源域 LU 求解
"""

from .mesh_io import read_gmsh_m, Mesh
from .gmsh_io import harvest_3d_mesh, verify_against_m
from .elements import quadrature_volume_h27, local_basis_volume_h27
from .boundary import (find_saw_boundary_3ds, boundary_idx_vect_3ds,
                       find_saw_boundary_3df, boundary_idx_vect_3df,
                       sort_lr_3d, sort_fb_3d, Boundary)
from .assembly import form_stiffness_mass_3d, KM_SCALE
from .bc_solve import (build_periodic_operators, prescribed_dofs,
                       apply_periodic_values, lu_solve_active,
                       FrequencySolver3D,
                       build_periodic_operators_fp, prescribed_dofs_fp,
                       apply_periodic_values_fp, FrequencySolver3D_FP)

__all__ = [
    "read_gmsh_m", "Mesh",
    "harvest_3d_mesh", "verify_against_m",
    "quadrature_volume_h27", "local_basis_volume_h27",
    "find_saw_boundary_3ds", "boundary_idx_vect_3ds",
    "find_saw_boundary_3df", "boundary_idx_vect_3df",
    "sort_lr_3d", "sort_fb_3d", "Boundary",
    "form_stiffness_mass_3d", "KM_SCALE",
    "build_periodic_operators", "prescribed_dofs",
    "apply_periodic_values", "lu_solve_active",
    "FrequencySolver3D",
    "build_periodic_operators_fp", "prescribed_dofs_fp",
    "apply_periodic_values_fp", "FrequencySolver3D_FP",
]
