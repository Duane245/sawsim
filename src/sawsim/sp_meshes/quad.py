"""SAW_PeriodBC1_4ceng —— SP_2D_4ceng (LT + Al + SiO2 + PolySi + Si) 结构化网格。

对齐
``P10_codes_2d_RefMesh_PMLT9_python/P18_2d_4ceng_SP/refmesh.mat``:

  * 单周期(SP)单元 2 pitch 宽
  * 9 个 p/4 等分 x 切线 → 8 列 strip(每列 p/4 = 0.2713 μm 宽)
  * 衬底从顶到底 5 个 y 带,每列内独立 transfinite:
      - LT      y ∈ [-0.6,   0.0]      0.6 μm,  3 行(Ny=4)
      - SiO2    y ∈ [-1.1,  -0.6]      0.5 μm,  2 行(Ny=3)
      - PolySi  y ∈ [-2.1,  -1.1]      1.0 μm,  4 行(Ny=5)
      - Si      y ∈ [-9.93, -2.1]      7.83 μm, 29 行(Ny=30)
      - PML     y ∈ [-12.10, -9.93]    2.17 μm, 8 行(Ny=9)
  * Al 两齿 (MR=0.5) 在 y ∈ [0, 0.17], 每齿 2 元素宽 × 1 高,共 4 个 Al 元素

元素总数: 8 × (3 + 2 + 4 + 29 + 8) + 4 = 8 × 46 + 4 = **372**, 节点 **1601**
—— 与 P18 参考网格一致。
"""

import gmsh
import sys
import math


def GM(pitch, MR, Hidt,
       H_LT, H_SiO2, H_PolySi, H_Si, H_PML, mesh_um=0.5):
    p = pitch
    w = 2 * p
    # y 切线 (top → bottom)
    yLT_top = 0.0
    yLT_bot = -H_LT
    ySiO2_bot = yLT_bot - H_SiO2
    yPolySi_bot = ySiO2_bot - H_PolySi
    ySi_bot = yPolySi_bot - H_Si
    yPML_bot = ySi_bot - H_PML
    yAl_top = Hidt

    # 9 个 x 切线: 0, p/4, p/2, 3p/4, p, 5p/4, 3p/2, 7p/4, 2p
    nx_cuts = 9
    xs = [i * w / 8 for i in range(nx_cuts)] if MR == .5 else [0, p*(1-MR)/2, p/2, p*(1+MR)/2, p, p*(3-MR)/2, 1.5*p, p*(3+MR)/2, 2*p]

    # 每方向 transfinite 节点数(= 元素数 + 1)
    Nx_strip = 1 + max(1, math.ceil(.5 / mesh_um - 1e-12))
    Ny = {key: 1 + max(1, math.ceil(rows * height / default * .5 / mesh_um - 1e-12))
          for key, rows, height, default in [("PML",8,H_PML,2.17),("Si",29,H_Si,7.83),
          ("PolySi",4,H_PolySi,1.),("SiO2",2,H_SiO2,.5),("LT",3,H_LT,.6),("Al",1,Hidt,.17)]}

    gmsh.initialize()
    gmsh.model.add("SAW_PeriodBC1_4ceng")
    geo = gmsh.model.geo
    lc = p

    # ---- 点
    # 6 个 y 层 × 9 个 x 切 = 54 衬底点
    y_levels = [yPML_bot, ySi_bot, yPolySi_bot, ySiO2_bot, yLT_bot, yLT_top]
    pid_grid = {}                                          # (li, xi) -> pid
    for li, y in enumerate(y_levels):
        for xi, x in enumerate(xs):
            pid_grid[(li, xi)] = geo.addPoint(x, y, 0, lc)

    # Al 顶点(6 个,齿内 3 个 × 2 齿)
    al_top_pid = {}
    for xi in (1, 2, 3, 5, 6, 7):
        al_top_pid[xi] = geo.addPoint(xs[xi], yAl_top, 0, lc)

    # ---- 线
    # 水平线: 6 个 y 层 × (nx_cuts-1) 段 = 48 段
    hline = {}                                             # (li, xi) -> line li 层第 xi 段
    for li in range(len(y_levels)):
        for xi in range(nx_cuts - 1):
            hline[(li, xi)] = geo.addLine(pid_grid[(li, xi)],
                                          pid_grid[(li, xi + 1)])

    # 垂直线(衬底内 5 个 y 段 × 9 个 x 切 = 45 段)
    vline = {}                                             # (li, xi) -> line li→li+1 at xi
    for li in range(len(y_levels) - 1):
        for xi in range(nx_cuts):
            vline[(li, xi)] = geo.addLine(pid_grid[(li, xi)],
                                          pid_grid[(li + 1, xi)])

    # Al 顶部水平 + 侧边垂直
    al_hline = {}
    for left in (1, 5):
        for xi in (left, left + 1):
            al_hline[xi] = geo.addLine(al_top_pid[xi], al_top_pid[xi + 1])

    al_vline = {}
    for xi in (1, 2, 3, 5, 6, 7):
        al_vline[xi] = geo.addLine(pid_grid[(5, xi)], al_top_pid[xi])

    # ---- 曲面(每 cell 为 transfinite quad)
    pml_surf, si_surf, polysi_surf, sio2_surf, lt_surf, al_surf = [], [], [], [], [], []

    # 衬底 8 列 × 5 区域(从下到上: PML, Si, PolySi, SiO2, LT)
    region_lists = [pml_surf, si_surf, polysi_surf, sio2_surf, lt_surf]
    for xi in range(nx_cuts - 1):
        for li in range(len(y_levels) - 1):
            cl = geo.addCurveLoop([hline[(li, xi)], vline[(li, xi + 1)],
                                   -hline[(li + 1, xi)], -vline[(li, xi)]])
            s = geo.addPlaneSurface([cl])
            region_lists[li].append(s)

    # Al cells (每齿 2 个)
    for xi in (1, 2, 5, 6):
        cl = geo.addCurveLoop([hline[(5, xi)], al_vline[xi + 1],
                               -al_hline[xi], -al_vline[xi]])
        s = geo.addPlaneSurface([cl])
        al_surf.append(s)

    # ---- Transfinite
    # 水平段: 每段 1 元素 (Nx_strip=2 points)
    for li in range(len(y_levels)):
        for xi in range(nx_cuts - 1):
            geo.mesh.setTransfiniteCurve(hline[(li, xi)], Nx_strip)
    for xi in (1, 2, 5, 6):
        geo.mesh.setTransfiniteCurve(al_hline[xi], Nx_strip)

    # 垂直段: 按所属区域(li=0..1: PML, 1..2: Si, 2..3: PolySi, 3..4: SiO2, 4..5: LT)
    region_ny = [Ny["PML"], Ny["Si"], Ny["PolySi"], Ny["SiO2"], Ny["LT"]]
    for li, npts in enumerate(region_ny):
        for xi in range(nx_cuts):
            geo.mesh.setTransfiniteCurve(vline[(li, xi)], npts)
    for xi in (1, 2, 3, 5, 6, 7):
        geo.mesh.setTransfiniteCurve(al_vline[xi], Ny["Al"])

    for s in pml_surf + si_surf + polysi_surf + sio2_surf + lt_surf + al_surf:
        geo.mesh.setTransfiniteSurface(s)
        geo.mesh.setRecombine(2, s)

    geo.synchronize()

    # ---- 物理组(与 SP_2D_4ceng/solve_saw.py 的 material_index 映射对齐)
    gmsh.model.addPhysicalGroup(2, al_surf, 15)            # Al
    gmsh.model.addPhysicalGroup(2, lt_surf, 16)            # LT 压电
    gmsh.model.addPhysicalGroup(2, sio2_surf, 22)          # SiO2
    gmsh.model.addPhysicalGroup(2, polysi_surf, 23)        # Poly-Si
    gmsh.model.addPhysicalGroup(2, si_surf, 24)            # Si
    gmsh.model.addPhysicalGroup(2, pml_surf, 25)           # 底部 PML

    # 边界线(与 sweep.bc_periodic 默认 tag 对齐)
    L_lines = [vline[(li, 0)] for li in range(5)]
    R_lines = [vline[(li, nx_cuts - 1)] for li in range(5)]
    bot_lines = [hline[(0, xi)] for xi in range(nx_cuts - 1)]

    # 电极: LT-Al 接触面 + 齿三面
    zheng_lines = [hline[(5, 1)], hline[(5, 2)],
                   al_vline[1], al_vline[3],
                   al_hline[1], al_hline[2]]
    fu_lines = [hline[(5, 5)], hline[(5, 6)],
                al_vline[5], al_vline[7],
                al_hline[5], al_hline[6]]

    gmsh.model.addPhysicalGroup(1, zheng_lines, 17)        # 正电极
    gmsh.model.addPhysicalGroup(1, fu_lines, 18)           # 负电极
    gmsh.model.addPhysicalGroup(1, L_lines, 19)            # 左周期
    gmsh.model.addPhysicalGroup(1, R_lines, 20)            # 右周期
    gmsh.model.addPhysicalGroup(1, bot_lines, 21)          # 底部固定

    gmsh.model.mesh.generate(2)
    gmsh.model.mesh.setOrder(2)


def build_mesh():
    """SAW_PeriodBC1_4ceng: 结构化网格,对齐 P18_2d_4ceng_SP 参考网格。

    几何: pitch=1.085 μm, MR=0.5, Al=0.17 μm,
    LT=0.6, SiO2=0.5, PolySi=1.0, Si=7.83, PML=2.17 μm (= 2 pitch)。
    元素分布: LT 8×3=24, SiO2 8×2=16, PolySi 8×4=32, Si 8×29=232,
    PML 8×8=64, Al 4 → **共 372 elem, 1601 nodes**。
    """
    return GM(pitch=1.085, MR=0.5, Hidt=0.17,
              H_LT=0.6, H_SiO2=0.5, H_PolySi=1.0, H_Si=7.83, H_PML=2.17)


if __name__ == "__main__":
    build_mesh()
    gmsh.write("SAW_PeriodBC1_4ceng.m")
    if "-nopopup" not in sys.argv:
        gmsh.fltk.run()
    gmsh.finalize()
