"""SP_3D_1ceng 用 Hex27 网格的 Gmsh Python 构建脚本。

复制自 MATLAB 仓库 ``P10_codes_Gmsh_PMLT9_1/mesh/SAW_3D_Hex7_LTPML.py``，
原脚本顶层执行 + ``gmsh.write(".m")``;此处把建模主体包成 :func:`build_mesh`，
便于 Python 求解器直接 ``import`` + ``harvest_3d_mesh()`` 走 Gmsh API 直读路径
(参见 :mod:`saw2d.saw3d.gmsh_io`)。

此副本由统一参数接口调用，保留原默认网格。
"""
import gmsh
import sys
import math


def build_mesh(config):
    """构建 SP_3D_1ceng 用 Hex27 网格并 ``generate(3) + setOrder(2)``。

    调用方在本函数返回后,从当前 ``gmsh`` 会话用
    :func:`saw2d.saw3d.gmsh_io.harvest_3d_mesh` 抽取节点 / 单元数据,
    然后自行 ``gmsh.finalize()``。
    """
    gmsh.initialize()
    gmsh.model.add("SAW_3D_Hex7_LTPML")

    # LT
    p = config.pitch_um
    w = 2 * p                                              # 波长
    d = config.electrode_um

    h1 = config.substrate_um
    h2 = 2 * p
    h = h1 + h2                                            # 压电材料高度

    MR = config.metal_ratio
    lc = config.mesh_um
    width = config.aperture_um

    NN = max(1, math.ceil(d / .17 * 0.217 / lc - 1e-12))
    NN1 = max(1, math.ceil(30 * h1 / 6.51 * 0.217 / lc - 1e-12))
    NN2 = max(1, math.ceil(10 * h2 / 2.17 * 0.217 / lc - 1e-12))

    gmsh.model.geo.addPoint(0, 0, h, lc, 1)
    gmsh.model.geo.addPoint(w, 0, h, lc, 2)
    gmsh.model.geo.addPoint(0, width, h, lc, 3)
    gmsh.model.geo.addPoint(w, width, h, lc, 4)

    gmsh.model.geo.addPoint(w / 4 - w / 4 * MR, 0, h, lc, 5)
    gmsh.model.geo.addPoint(w / 4 + w / 4 * MR, 0, h, lc, 6)
    gmsh.model.geo.addPoint(w / 4 - w / 4 * MR, width, h, lc, 7)
    gmsh.model.geo.addPoint(w / 4 + w / 4 * MR, width, h, lc, 8)

    gmsh.model.geo.addPoint(w / 4 * 3 - w / 4 * MR, 0, h, lc, 9)
    gmsh.model.geo.addPoint(w / 4 * 3 + w / 4 * MR, 0, h, lc, 10)
    gmsh.model.geo.addPoint(w / 4 * 3 - w / 4 * MR, width, h, lc, 11)
    gmsh.model.geo.addPoint(w / 4 * 3 + w / 4 * MR, width, h, lc, 12)

    gmsh.model.geo.addLine(1, 5, 1)
    gmsh.model.geo.addLine(5, 6, 2)
    gmsh.model.geo.addLine(6, 9, 3)
    gmsh.model.geo.addLine(9, 10, 4)
    gmsh.model.geo.addLine(10, 2, 5)
    gmsh.model.geo.addLine(2, 4, 6)
    gmsh.model.geo.addLine(4, 12, 7)
    gmsh.model.geo.addLine(12, 11, 8)
    gmsh.model.geo.addLine(11, 8, 9)
    gmsh.model.geo.addLine(8, 7, 10)
    gmsh.model.geo.addLine(7, 3, 11)
    gmsh.model.geo.addLine(3, 1, 12)
    gmsh.model.geo.addLine(5, 7, 13)
    gmsh.model.geo.addLine(6, 8, 14)
    gmsh.model.geo.addLine(9, 11, 15)
    gmsh.model.geo.addLine(10, 12, 16)

    gmsh.model.geo.addCurveLoop([1, 13, 11, 12], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)
    gmsh.model.geo.addCurveLoop([2, 14, 10, -13], 2)
    gmsh.model.geo.addPlaneSurface([2], 2)
    gmsh.model.geo.addCurveLoop([3, 15, 9, -14], 3)
    gmsh.model.geo.addPlaneSurface([3], 3)
    gmsh.model.geo.addCurveLoop([4, 16, 8, -15], 4)
    gmsh.model.geo.addPlaneSurface([4], 4)
    gmsh.model.geo.addCurveLoop([5, 6, 7, -16], 5)
    gmsh.model.geo.addPlaneSurface([5], 5)

    gmsh.model.geo.synchronize()

    gmsh.model.geo.mesh.setTransfiniteCurve(12, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(13, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(14, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(15, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(16, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(6, 2)

    gmsh.model.geo.extrude([(2, 1), (2, 2), (2, 3), (2, 4), (2, 5)],
                           0, 0, -h1, [NN1], [], True)
    gmsh.model.geo.extrude([(2, 2), (2, 4)], 0, 0, d, [NN], [], True)
    gmsh.model.geo.extrude([(2, 38), (2, 60), (2, 82), (2, 104), (2, 126)],
                           0, 0, -h2, [NN2], [], True)

    gmsh.model.geo.synchronize()

    gmsh.model.mesh.setTransfiniteSurface(1)
    gmsh.model.mesh.setRecombine(2, 1)
    gmsh.model.mesh.setTransfiniteSurface(2)
    gmsh.model.mesh.setRecombine(2, 2)
    gmsh.model.mesh.setTransfiniteSurface(3)
    gmsh.model.mesh.setRecombine(2, 3)
    gmsh.model.mesh.setTransfiniteSurface(4)
    gmsh.model.mesh.setRecombine(2, 4)
    gmsh.model.mesh.setTransfiniteSurface(5)
    gmsh.model.mesh.setRecombine(2, 5)

    # 物理组(与 .m 解析路径完全一致;不可改动数值,下游 find_saw_boundary_3ds
    # 与 saw3d 各算例的 hex_tag/quad_tag 索引依赖这些编号)
    gmsh.model.addPhysicalGroup(3, [1, 2, 3, 4, 5], 7)                      # 压电体
    gmsh.model.addPhysicalGroup(3, [6, 7], 8)                               # 电极体
    gmsh.model.addPhysicalGroup(3, [8, 9, 10, 11, 12], 9)                   # 基底体

    gmsh.model.addPhysicalGroup(2, [37, 191], 1)                            # 左平面
    gmsh.model.addPhysicalGroup(2, [117, 271], 2)                           # 右平面
    gmsh.model.addPhysicalGroup(2, [33, 55, 77, 99, 121, 143,
                                    165, 187, 209, 231, 253, 275], 3)       # 后平面
    gmsh.model.addPhysicalGroup(2, [25, 47, 69, 91, 113, 135,
                                    157, 179, 201, 223, 245, 267], 4)       # 前平面
    gmsh.model.addPhysicalGroup(2, [192, 214, 236, 258, 280], 5)            # 底平面
    gmsh.model.addPhysicalGroup(2, [2, 148, 135, 139, 143, 147], 7)         # 正电极
    gmsh.model.addPhysicalGroup(2, [4, 170, 157, 161, 165, 169], 8)         # 负电极
    gmsh.model.addPhysicalGroup(2, [1, 3, 5], 100)                          # 画图平面

    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.setOrder(2)

