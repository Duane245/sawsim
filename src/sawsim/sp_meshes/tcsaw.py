import gmsh
import sys
import math



def build_mesh(pitch=.9968, electrode=.16633, substrate=15.9488, metal_ratio=.46, mesh_um=.1, coating_inner=.72144, coating_outer=.04):
    """SAW_PeriodBC1_TC: 2D Gmsh 模型构建(从 MATLAB 仓库 .py 复制并函数化,flat 风格)。"""
    gmsh.initialize()

    gmsh.model.add("SAW_PeriodBC1_TC")


    w = 2 * pitch  # 波长
    p = w/2
    # a = 1.2  # 指条宽度
    d = electrode   # 指条厚度
    h = substrate / 4  # 压电材料高度
    MR = metal_ratio   # 金属化比例

    lc = mesh_um

    h1 = substrate * 3 / 4
    hpml = 2*w

    hsio = coating_inner
    hsin = coating_outer

    gmsh.model.geo.addPoint(0, 0, 0, lc, 1)
    gmsh.model.geo.addPoint(w, 0, 0, lc, 2)
    gmsh.model.geo.addPoint(w, h, 0, lc, 3)
    gmsh.model.geo.addPoint(0, h, 0, lc, 4)

    gmsh.model.geo.addPoint(w / 4 - w / 4 * MR, h, 0, lc, 5)
    gmsh.model.geo.addPoint(w / 4 + w / 4 * MR, h, 0, lc, 6)
    gmsh.model.geo.addPoint(w / 4 * 3 - w / 4 * MR, h, 0, lc, 7)
    gmsh.model.geo.addPoint(w / 4 * 3 + w / 4 * MR, h, 0, lc, 8)

    gmsh.model.geo.addPoint(w / 4 - w / 4 * MR, h + d, 0, lc, 9)
    gmsh.model.geo.addPoint(w / 4 + w / 4 * MR, h + d, 0, lc, 10)
    gmsh.model.geo.addPoint(w / 4 * 3 - w / 4 * MR, h + d, 0, lc, 11)
    gmsh.model.geo.addPoint(w / 4 * 3 + w / 4 * MR, h + d, 0, lc, 12)

    gmsh.model.geo.addPoint(0, -h1, 0, lc, 13)
    gmsh.model.geo.addPoint(w, -h1, 0, lc, 14)

    gmsh.model.geo.addPoint(0, -h1-hpml, 0, lc, 15)
    gmsh.model.geo.addPoint(w, -h1-hpml, 0, lc, 16)

    gmsh.model.geo.addPoint(0, h+hsio, 0, lc, 17)
    gmsh.model.geo.addPoint(w, h+hsio, 0, lc, 18)

    gmsh.model.geo.addPoint(0, h+hsio+hsin, 0, lc, 19)
    gmsh.model.geo.addPoint(w, h+hsio+hsin, 0, lc, 20)

    gmsh.model.geo.addPoint(0, h + d, 0, lc, 21)
    gmsh.model.geo.addPoint(w, h + d, 0, lc, 22)

    gmsh.model.geo.addLine(1, 2, 1)
    gmsh.model.geo.addLine(2, 3, 2)
    gmsh.model.geo.addLine(3, 8, 3)
    gmsh.model.geo.addLine(8, 7, 4)
    gmsh.model.geo.addLine(7, 6, 5)
    gmsh.model.geo.addLine(6, 5, 6)
    gmsh.model.geo.addLine(5, 4, 7)
    gmsh.model.geo.addLine(4, 1, 8)
    gmsh.model.geo.addLine(6, 10, 9)
    gmsh.model.geo.addLine(10, 9, 10)
    gmsh.model.geo.addLine(9, 5, 11)

    gmsh.model.geo.addLine(8, 12, 12)
    gmsh.model.geo.addLine(12, 11, 13)
    gmsh.model.geo.addLine(11, 7, 14)

    gmsh.model.geo.addLine(1, 13, 15)
    gmsh.model.geo.addLine(13, 14, 16)
    gmsh.model.geo.addLine(14, 2, 17)

    gmsh.model.geo.addLine(13, 15, 18)
    gmsh.model.geo.addLine(15, 16, 19)
    gmsh.model.geo.addLine(16, 14, 20)

    # gmsh.model.geo.addLine(3, 18, 21)
    gmsh.model.geo.addLine(18, 17, 22)
    # gmsh.model.geo.addLine(17, 4, 23)

    gmsh.model.geo.addLine(18, 20, 24)
    gmsh.model.geo.addLine(20, 19, 25)
    gmsh.model.geo.addLine(19, 17, 26)

    #
    gmsh.model.geo.addLine(9, 21, 27)
    gmsh.model.geo.addLine(21, 4, 28)

    gmsh.model.geo.addLine(11, 10, 29)
    gmsh.model.geo.addLine(3, 22, 30)
    gmsh.model.geo.addLine(22, 12, 31)

    gmsh.model.geo.addLine(21, 17, 32)
    gmsh.model.geo.addLine(22, 18, 33)

    gmsh.model.geo.addCurveLoop([8, 1, 2, 3, 4, 5, 6, 7], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)
    gmsh.model.geo.addCurveLoop([-6, 9, 10, 11], 2)
    gmsh.model.geo.addPlaneSurface([2], 2)
    gmsh.model.geo.addCurveLoop([-4, 12, 13, 14], 3)
    gmsh.model.geo.addPlaneSurface([3], 3)

    gmsh.model.geo.addCurveLoop([15, 16, 17, -1], 4)
    gmsh.model.geo.addPlaneSurface([4], 4)

    gmsh.model.geo.addCurveLoop([18, 19, 20, -16], 5)
    gmsh.model.geo.addPlaneSurface([5], 5)

    # gmsh.model.geo.addCurveLoop([21, 22, 23, -7, -11, -10, -9, -5, -14, -13, -12, -3], 6)
    # gmsh.model.geo.addPlaneSurface([6], 6)

    gmsh.model.geo.addCurveLoop([24, 25, 26, -22], 7)
    gmsh.model.geo.addPlaneSurface([7], 7)

    # 温补层
    gmsh.model.geo.addCurveLoop([27, 28, -7, -11], 8)
    gmsh.model.geo.addPlaneSurface([8], 8)

    gmsh.model.geo.addCurveLoop([-5, -14, 29, -9], 9)
    gmsh.model.geo.addPlaneSurface([9], 9)

    gmsh.model.geo.addCurveLoop([30, 31, -12, -3], 10)
    gmsh.model.geo.addPlaneSurface([10], 10)

    gmsh.model.geo.addCurveLoop([-27, -10, -29, -13, -31, 33, 22, -32], 11)
    gmsh.model.geo.addPlaneSurface([11], 11)



    # pml
    gmsh.model.geo.mesh.setTransfiniteCurve(18, 11)
    gmsh.model.geo.mesh.setTransfiniteCurve(20, 11)

    # gmsh.model.geo.mesh.setTransfiniteCurve(15, 46)
    # gmsh.model.geo.mesh.setTransfiniteCurve(17, 46)

    # gmsh.model.geo.mesh.setTransfiniteCurve(2, 17,"Progression", 0.8)
    # gmsh.model.geo.mesh.setTransfiniteCurve(8, 17,"Progression", 1.2)

    NN = max(2, math.ceil((w / 4 - w / 4 * MR)/lc))
    # >= 2 elements per electrode and per inner gap: at least 8 elements per wavelength (2 p) across.
    NN1 = max(3, math.ceil(p*MR/lc))
    NN2 = max(3, math.ceil(p*(1-MR)/lc))

    NN3 = NN + (NN1-1) + (NN2-1) + (NN1-1) + (NN-1)        #3 + (5-1) + (5-1) + (5-1) + (3-1)

    gmsh.model.geo.mesh.setTransfiniteCurve(5, NN2)

    gmsh.model.geo.mesh.setTransfiniteCurve(6, NN1)
    gmsh.model.geo.mesh.setTransfiniteCurve(4, NN1)
    gmsh.model.geo.mesh.setTransfiniteCurve(10, NN1)
    gmsh.model.geo.mesh.setTransfiniteCurve(13, NN1)

    gmsh.model.geo.mesh.setTransfiniteCurve(7, NN)
    gmsh.model.geo.mesh.setTransfiniteCurve(3, NN)

    gmsh.model.geo.mesh.setTransfiniteCurve(22, NN3)
    gmsh.model.geo.mesh.setTransfiniteCurve(25, NN3)

    ## 设置边界点的个数
    gmsh.model.geo.mesh.setTransfiniteCurve(1, NN3)
    gmsh.model.geo.mesh.setTransfiniteCurve(16, NN3)
    gmsh.model.geo.mesh.setTransfiniteCurve(19, NN3)

    gmsh.model.geo.mesh.setTransfiniteCurve(26, 3)
    gmsh.model.geo.mesh.setTransfiniteCurve(24, 3)


    # Recombine
    gmsh.model.geo.mesh.setTransfiniteSurface(1,"Left",[1, 2, 3, 4])
    gmsh.model.geo.mesh.setRecombine(2, 1)

    gmsh.model.geo.mesh.setTransfiniteSurface(2)
    gmsh.model.geo.mesh.setRecombine(2, 2)

    gmsh.model.geo.mesh.setTransfiniteSurface(3)
    gmsh.model.geo.mesh.setRecombine(2, 3)

    gmsh.model.geo.mesh.setTransfiniteSurface(4)
    gmsh.model.geo.mesh.setRecombine(2, 4)

    gmsh.model.geo.mesh.setTransfiniteSurface(5)
    gmsh.model.geo.mesh.setRecombine(2, 5)

    # gmsh.model.geo.mesh.setTransfiniteSurface(6,"Left",[4, 3, 18, 17])
    gmsh.model.geo.mesh.setRecombine(2, 6)

    gmsh.model.geo.mesh.setTransfiniteSurface(7)
    gmsh.model.geo.mesh.setRecombine(2, 7)

    # Match every electrode-height edge; otherwise changed mesh sizes leave triangles.
    electrode_points = max(2, math.ceil(d/lc) + 1)
    if electrode_points != 3:
        for curve in (9,11,12,14,28,30):
            gmsh.model.geo.mesh.setTransfiniteCurve(curve, electrode_points)

    # 温补层
    gmsh.model.geo.mesh.setTransfiniteCurve(28, electrode_points)
    gmsh.model.geo.mesh.setTransfiniteCurve(27, NN)

    gmsh.model.geo.mesh.setTransfiniteCurve(29, NN2)
    gmsh.model.geo.mesh.setTransfiniteCurve(30, electrode_points)

    gmsh.model.geo.mesh.setTransfiniteCurve(31, NN)


    NN4 = max(2, math.ceil((hsio-d)/lc))
    gmsh.model.geo.mesh.setTransfiniteCurve(32, NN4)
    gmsh.model.geo.mesh.setTransfiniteCurve(33, NN4)

    gmsh.model.geo.mesh.setTransfiniteSurface(8)
    gmsh.model.geo.mesh.setRecombine(2, 8)

    gmsh.model.geo.mesh.setTransfiniteSurface(9)
    gmsh.model.geo.mesh.setRecombine(2, 9)

    gmsh.model.geo.mesh.setTransfiniteSurface(10)
    gmsh.model.geo.mesh.setRecombine(2, 10)

    gmsh.model.geo.mesh.setTransfiniteSurface(11,"Left",[21, 22, 18, 17])
    gmsh.model.geo.mesh.setRecombine(2, 11)

    gmsh.model.geo.synchronize()

    gmsh.model.addPhysicalGroup(2, [2, 3], 15, name='电极')
    gmsh.model.addPhysicalGroup(2, [1, 4], 16, name='压电')

    # gmsh.model.addPhysicalGroup(2, [4], 14, name='压电1')
    gmsh.model.addPhysicalGroup(2, [5], 13, name='PML')

    gmsh.model.addPhysicalGroup(2, [8, 9, 10, 11], 12, name='温补层')
    gmsh.model.addPhysicalGroup(2, [7], 11, name='TRIMM')

    gmsh.model.addPhysicalGroup(1, [6, 9, 10, 11], 17, name='正电极')
    gmsh.model.addPhysicalGroup(1, [4, 12, 13, 14], 18, name='负电极')
    gmsh.model.addPhysicalGroup(1, [8, 15, 18, 28, 32, 26], 19, name='左边界')
    gmsh.model.addPhysicalGroup(1, [2, 17, 20, 30, 33, 24], 20, name='右边界')
    gmsh.model.addPhysicalGroup(1, [19], 21, name='固定边界')


    # gmsh.option.setNumber("Mesh.Algorithm", 8)
    # gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1) # or 3
    # gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 2) # or 3
    # gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 1)
    gmsh.model.mesh.generate(2)


    # Set the element order and the desired interpolation order:
    elementOrder = 2
    gmsh.model.mesh.setOrder(elementOrder)


if __name__ == "__main__":
    import sys
    build_mesh()
    gmsh.write("SAW_PeriodBC1_TC.m")
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()
    gmsh.finalize()
