"""SAW_TF_PeriodBC1 —— SP_2D_2ceng (LT + Al + Si) 结构化网格,对齐
``P10_codes_2d_RefMesh_PMLT9/P16_2d_2ceng_SP1/refmesh.mat``。

复刻参考网格的拓扑 + 节点分布:
  * x 方向 9 个 p/4 等分切线 (0, p/4, p/2, ..., 2p) → 8 列, 每列 p/4 宽
  * 衬底分 3 个 y 带 (LT/Si/PML), 每列内独立 transfinite:
      - LT (-0.6 → 0):     3 行 (Ny=4)
      - Si (-8.93 → -0.6): 31 行 (Ny=32)
      - PML (-11.10 → -8.93): 8 行 (Ny=9)
  * Al 电极 (2 个齿) 位于 y=0..0.17 区间, x 在 [p/4, 3p/4] 与 [5p/4, 7p/4],
    每齿 2 元素宽 × 1 元素高 = 2 元素,两齿共 4 个 Al 元素

总元素数: 8×3 + 8×31 + 8×8 + 4 = 24 + 248 + 64 + 4 = **340**, 与参考网格一致。
"""

import gmsh
import sys
import math


def GM(pitch, _Aperture, Hidt, MR, Hidt_LT, Hidt_Si, mesh_um=0.5, *_unused):
    """Structured-grid build that mirrors the reference element distribution.

    ``_Aperture`` 保留兼容；mesh_um 控制相对原始结构化网格的细化。
    金属化率改变指条边缘；默认参数保持原始节点及单元分布。
    ``Hidt`` = Al 厚, ``MR`` = 金属化率, ``Hidt_LT`` = LT 厚, ``Hidt_Si`` = Si 厚。
    """
    p = pitch
    w = 2 * p                                              # unit-cell width
    yLT_top = 0.0
    yLT_bot = -Hidt_LT                                     # -0.6
    ySi_bot = yLT_bot - Hidt_Si                            # -8.93
    yPML_bot = ySi_bot - w                                 # -11.10  (PML 厚 = 2 pitch)
    yAl_top = Hidt                                         # +0.17

    # 9 个 x 切线: 0, p/4, p/2, 3p/4, p, 5p/4, 3p/2, 7p/4, 2p
    nx_cuts = 9
    xs = [i * w / 8 for i in range(nx_cuts)] if MR == .5 else [0, p*(1-MR)/2, p/2, p*(1+MR)/2, p, p*(3-MR)/2, 1.5*p, p*(3+MR)/2, 2*p]               # [0, p/4, ..., 2p]

    # 齿覆盖范围 (MR=0.5):
    # 齿 1: x = p/4 → 3p/4 (xi=1 → xi=3)  ⇒ 占 strip 1, 2
    # 齿 2: x = 5p/4 → 7p/4 (xi=5 → xi=7)  ⇒ 占 strip 5, 6
    tooth1_xis = (1, 3)                                    # left, right (column index)
    tooth2_xis = (5, 7)
    tooth_xi_mid = {1: 2, 5: 6}                            # 中间 x 索引 (齿内 2 个 strip 之间)

    # 每方向 transfinite 节点数 (= 元素数 + 1)
    Nx_strip = 1 + max(1, math.ceil(.5 / mesh_um - 1e-12))                                           # 1 element per strip in x
    Ny_LT = 1 + max(1, math.ceil(3 * Hidt_LT / 0.6 * .5 / mesh_um - 1e-12))                                              # 3 elem in LT y
    Ny_Si = 1 + max(1, math.ceil(31 * Hidt_Si / 8.33 * .5 / mesh_um - 1e-12))                                             # 31 elem in Si y
    Ny_PML = 1 + max(1, math.ceil(8 * w / 2.17 * .5 / mesh_um - 1e-12))                                             # 8 elem in PML y
    Ny_Al = 1 + max(1, math.ceil(1 * Hidt / 0.17 * .5 / mesh_um - 1e-12))                                              # 1 elem in Al y

    gmsh.initialize()
    gmsh.model.add("SAW_TF_PeriodBC1")
    geo = gmsh.model.geo

    lc = p                                                 # dummy; transfinite overrides

    # ---- 点
    # 衬底: 4 个 y 层 × 9 个 x 切 = 36 点
    y_levels = [yPML_bot, ySi_bot, yLT_bot, yLT_top]       # li=0..3
    pid_grid = {}                                          # (li, xi) -> point id
    for li, y in enumerate(y_levels):
        for xi, x in enumerate(xs):
            pid_grid[(li, xi)] = geo.addPoint(x, y, 0, lc)

    # Al 顶点: 6 个 (齿内 3 x 点 × 2 齿)
    al_top_pid = {}                                        # xi -> point id at yAl_top
    for xi in (1, 2, 3, 5, 6, 7):
        al_top_pid[xi] = geo.addPoint(xs[xi], yAl_top, 0, lc)

    # ---- 线
    # 水平线: 4 个 y 层 × (nx_cuts-1) 段 = 32 段
    hline = {}                                             # (li, xi) -> line from (li,xi)→(li,xi+1)
    for li in range(4):
        for xi in range(nx_cuts - 1):
            hline[(li, xi)] = geo.addLine(pid_grid[(li, xi)],
                                          pid_grid[(li, xi + 1)])

    # 垂直线 (衬底内部): 3 个 y 段 × 9 个 x 切 = 27 段
    vline = {}                                             # (li, xi) -> line from (li,xi)→(li+1,xi)
    for li in range(3):
        for xi in range(nx_cuts):
            vline[(li, xi)] = geo.addLine(pid_grid[(li, xi)],
                                          pid_grid[(li + 1, xi)])

    # Al 顶部水平线: 每齿 2 段 = 4 段
    al_hline = {}                                          # xi -> al_top[xi]→al_top[xi+1]
    for left in (1, 5):                                    # 齿左索引
        for xi in (left, left + 1):
            al_hline[xi] = geo.addLine(al_top_pid[xi], al_top_pid[xi + 1])

    # Al 侧边垂直线 (含齿中点): 6 段 (xi=1,2,3,5,6,7)
    al_vline = {}                                          # xi -> pid_grid[(3,xi)] → al_top[xi]
    for xi in (1, 2, 3, 5, 6, 7):
        al_vline[xi] = geo.addLine(pid_grid[(3, xi)], al_top_pid[xi])

    # ---- 曲面 (每个 cell 都是 transfinite quad)
    pml_surf, si_surf, lt_surf, al_surf = [], [], [], []

    # 衬底 8 列 × 3 区域
    for xi in range(nx_cuts - 1):
        # PML cell  (li=0 → li=1)
        cl = geo.addCurveLoop([hline[(0, xi)], vline[(0, xi + 1)],
                               -hline[(1, xi)], -vline[(0, xi)]])
        s = geo.addPlaneSurface([cl])
        pml_surf.append(s)
        # Si cell  (li=1 → li=2)
        cl = geo.addCurveLoop([hline[(1, xi)], vline[(1, xi + 1)],
                               -hline[(2, xi)], -vline[(1, xi)]])
        s = geo.addPlaneSurface([cl])
        si_surf.append(s)
        # LT cell  (li=2 → li=3)
        cl = geo.addCurveLoop([hline[(2, xi)], vline[(2, xi + 1)],
                               -hline[(3, xi)], -vline[(2, xi)]])
        s = geo.addPlaneSurface([cl])
        lt_surf.append(s)

    # Al cells (每齿 2 个 = 共 4 个)
    for xi in (1, 2, 5, 6):
        cl = geo.addCurveLoop([hline[(3, xi)], al_vline[xi + 1],
                               -al_hline[xi], -al_vline[xi]])
        s = geo.addPlaneSurface([cl])
        al_surf.append(s)

    # ---- Transfinite 设置
    # 水平段: 每段 Nx_strip=2 点 (1 element)
    for li in range(4):
        for xi in range(nx_cuts - 1):
            geo.mesh.setTransfiniteCurve(hline[(li, xi)], Nx_strip)
    for xi in (1, 2, 5, 6):
        geo.mesh.setTransfiniteCurve(al_hline[xi], Nx_strip)

    # 垂直段: 按所属区域
    for xi in range(nx_cuts):
        geo.mesh.setTransfiniteCurve(vline[(0, xi)], Ny_PML)
        geo.mesh.setTransfiniteCurve(vline[(1, xi)], Ny_Si)
        geo.mesh.setTransfiniteCurve(vline[(2, xi)], Ny_LT)
    for xi in (1, 2, 3, 5, 6, 7):
        geo.mesh.setTransfiniteCurve(al_vline[xi], Ny_Al)

    for s in pml_surf + si_surf + lt_surf + al_surf:
        geo.mesh.setTransfiniteSurface(s)
        geo.mesh.setRecombine(2, s)

    geo.synchronize()

    # ---- 物理组 (与 SP_2D_2ceng/solve_saw.py 的 material_index 映射对齐)
    gmsh.model.addPhysicalGroup(2, al_surf, 15)            # Al
    gmsh.model.addPhysicalGroup(2, lt_surf, 16)            # LT 压电
    gmsh.model.addPhysicalGroup(2, si_surf, 22)            # Si 基底
    gmsh.model.addPhysicalGroup(2, pml_surf, 23)           # 底部 PML

    # 边界线 (与 sweep.bc_periodic 默认 tag 对齐: 17=zheng, 18=fu, 19=L, 20=R, 21=底固定)
    L_lines = [vline[(li, 0)] for li in range(3)]
    R_lines = [vline[(li, nx_cuts - 1)] for li in range(3)]
    bot_lines = [hline[(0, xi)] for xi in range(nx_cuts - 1)]

    # 电极: LT-Al 接触面 + 齿三面 (与 SP_2D_1ceng 等其他算例约定一致)
    zheng_lines = [hline[(3, 1)], hline[(3, 2)],           # LT-Al 接触 (齿 1 下)
                   al_vline[1], al_vline[3],               # 齿 1 左 / 右
                   al_hline[1], al_hline[2]]               # 齿 1 顶
    fu_lines = [hline[(3, 5)], hline[(3, 6)],
                al_vline[5], al_vline[7],
                al_hline[5], al_hline[6]]

    gmsh.model.addPhysicalGroup(1, zheng_lines, 17)        # 正电极
    gmsh.model.addPhysicalGroup(1, fu_lines, 18)           # 负电极
    gmsh.model.addPhysicalGroup(1, L_lines, 19)            # 左边界
    gmsh.model.addPhysicalGroup(1, R_lines, 20)            # 右边界
    gmsh.model.addPhysicalGroup(1, bot_lines, 21)          # 底部固定

    # ---- 网格生成
    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.setOrder(2)


def build_mesh():
    """SAW_TF_PeriodBC1: 结构化网格(对齐 P16_2d_2ceng_SP1 参考网格)。

    几何:pitch=1.085 μm, Al=0.17 μm, LT=0.6 μm, Si=8.33 μm, PML=2*pitch=2.17 μm,
    MR=0.5。元素分布:LT 8×3=24, Si 8×31=248, PML 8×8=64, Al 4 → **共 340 elem**。
    """
    return GM(1.085, 0, 0.17, 0.5, 0.6, 8.33, 0.5)


if __name__ == "__main__":
    build_mesh()
    gmsh.write("SAW_TF_PeriodBC1.m")
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()
    gmsh.finalize()
