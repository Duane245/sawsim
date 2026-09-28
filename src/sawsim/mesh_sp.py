import gmsh

def GM(pitch, Aperture, Hidt, eta, Hidt_LT, msh_max, msh_min, msh_r, msh_f):
    import sys

    gmsh.initialize()

    gmsh.model.add("SAW_PeriodBC1")

    p = pitch
    w = 2 * p  # 波长
    d = Hidt  # 指条厚度
    h = Hidt_LT  # 压电材料高度
    MR = eta  # 金属化比例
    lc = msh_min  # 离散尺寸

    h1 = w  # pml的厚度

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

    gmsh.model.geo.addLine(13, 14, 15)
    gmsh.model.geo.addLine(1, 13, 16)
    gmsh.model.geo.addLine(14, 2, 17)

    gmsh.model.geo.addCurveLoop([8, 1, 2, 3, 4, 5, 6, 7], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)
    gmsh.model.geo.addCurveLoop([-6, 9, 10, 11], 2)
    gmsh.model.geo.addPlaneSurface([2], 2)
    gmsh.model.geo.addCurveLoop([-4, 12, 13, 14], 3)
    gmsh.model.geo.addPlaneSurface([3], 3)

    gmsh.model.geo.mesh.setTransfiniteCurve(16, 6)
    gmsh.model.geo.mesh.setTransfiniteCurve(17, 6)

    gmsh.model.geo.addCurveLoop([16, 15, 17, -1], 4)
    gmsh.model.geo.addPlaneSurface([4], 4)
    gmsh.model.geo.mesh.setTransfiniteSurface(4)
    gmsh.model.geo.mesh.setRecombine(2, 4)

    gmsh.model.geo.synchronize()

    # gmsh.model.geo.mesh.setTransfiniteCurve(16, 11)
    # gmsh.model.geo.mesh.setTransfiniteCurve(17, 11)

    # Recombine

    # gmsh.model.geo.mesh.setTransfiniteSurface(1, "Left", [1, 2, 3, 4])
    gmsh.model.geo.mesh.setRecombine(2, 1)


    gmsh.model.geo.mesh.setRecombine(2, 2)
    gmsh.model.geo.mesh.setRecombine(2, 3)
    gmsh.model.geo.mesh.setRecombine(2, 4)

    gmsh.model.geo.synchronize()

    gmsh.model.addPhysicalGroup(2, [2, 3], 15)
    gmsh.model.addPhysicalGroup(2, [1], 16)

    gmsh.model.addPhysicalGroup(1, [6, 9, 10, 11], 17)
    gmsh.model.addPhysicalGroup(1, [4, 12, 13, 14], 18)
    gmsh.model.addPhysicalGroup(1, [8, 16], 19)
    gmsh.model.addPhysicalGroup(1, [17, 2], 20)
    gmsh.model.addPhysicalGroup(1, [15], 21)

    gmsh.model.addPhysicalGroup(2, [4], 22)  # 基底

    gmsh.option.setNumber("Mesh.Algorithm", 8)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)  # or 3
    gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 1)

    # gmsh.option.setNumber("Mesh.Smoothing", 200)
    gmsh.model.mesh.generate(2)

    # Set the element order and the desired interpolation order:
    elementOrder = 2
    gmsh.model.mesh.setOrder(elementOrder)




    # if '-nopopup' not in sys.argv:
    #     gmsh.fltk.initialize()
    # gmsh.write("mesh.jpg")






def build_mesh():
    """SAW_PeriodBC1: 调用 GM(...) 构建 2D 网格(从 MATLAB 仓库 .py 复制并函数化)。"""
    return GM(1.085, 0, 0.17, 0.5, 8, 0,0.5,0,0)


if __name__ == "__main__":
    import sys
    build_mesh()
    gmsh.write("SAW_PeriodBC1.m")
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()
    gmsh.finalize()
