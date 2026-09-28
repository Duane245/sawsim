import gmsh
import sys

def GM(pitch, Aperture, Hidt, eta, Hidt_LT, Hidt_SiO2, Hidt_poly_Si, msh_max, msh_min, msh_r, msh_f):
    gmsh.initialize()

    gmsh.model.add("SAW_PeriodBC1_LT42")

    p = pitch
    w = 2 * p  # 波长
    # a = 1.2  # 指条宽度
    d = Hidt  # 指条厚度
    h = Hidt_LT  # 压电材料高度
    MR = eta  # 金属化比例

    h1 = Hidt_SiO2
    h2 = Hidt_SiO2 + Hidt_poly_Si
    h3 = Hidt_SiO2 + Hidt_poly_Si + w

    lc1 = msh_min

    gmsh.model.geo.addPoint(0, 0, 0, lc1, 1)
    gmsh.model.geo.addPoint(w, 0, 0, lc1, 2)
    gmsh.model.geo.addPoint(w, h, 0, lc1, 3)
    gmsh.model.geo.addPoint(0, h, 0, lc1, 4)

    gmsh.model.geo.addPoint(w / 4 - w / 4 * MR, h, 0, lc1, 5)
    gmsh.model.geo.addPoint(w / 4 + w / 4 * MR, h, 0, lc1, 6)
    gmsh.model.geo.addPoint(w / 4 * 3 - w / 4 * MR, h, 0, lc1, 7)
    gmsh.model.geo.addPoint(w / 4 * 3 + w / 4 * MR, h, 0, lc1, 8)

    gmsh.model.geo.addPoint(w / 4 - w / 4 * MR, h + d, 0, lc1, 9)
    gmsh.model.geo.addPoint(w / 4 + w / 4 * MR, h + d, 0, lc1, 10)
    gmsh.model.geo.addPoint(w / 4 * 3 - w / 4 * MR, h + d, 0, lc1, 11)
    gmsh.model.geo.addPoint(w / 4 * 3 + w / 4 * MR, h + d, 0, lc1, 12)

    gmsh.model.geo.addPoint(0, -h1, 0, lc1, 13)
    gmsh.model.geo.addPoint(w, -h1, 0, lc1, 14)

    gmsh.model.geo.addPoint(0, -h2, 0, lc1, 15)
    gmsh.model.geo.addPoint(w, -h2, 0, lc1, 16)

    gmsh.model.geo.addPoint(0, -h3, 0, lc1, 17)
    gmsh.model.geo.addPoint(w, -h3, 0, lc1, 18)

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

    gmsh.model.geo.addLine(13, 15, 18)
    gmsh.model.geo.addLine(15, 16, 19)
    gmsh.model.geo.addLine(16, 14, 20)

    gmsh.model.geo.addLine(15, 17, 21)
    gmsh.model.geo.addLine(17, 18, 22)
    gmsh.model.geo.addLine(18, 16, 23)

    gmsh.model.geo.addCurveLoop([8, 1, 2, 3, 4, 5, 6, 7], 1)
    gmsh.model.geo.addPlaneSurface([1], 1)
    gmsh.model.geo.addCurveLoop([-6, 9, 10, 11], 2)
    gmsh.model.geo.addPlaneSurface([2], 2)
    gmsh.model.geo.addCurveLoop([-4, 12, 13, 14], 3)
    gmsh.model.geo.addPlaneSurface([3], 3)

    gmsh.model.geo.addCurveLoop([16, 15, 17, -1], 4)
    gmsh.model.geo.addPlaneSurface([4], 4)

    gmsh.model.geo.addCurveLoop([18, 19, 20, -15], 5)
    gmsh.model.geo.addPlaneSurface([5], 5)

    gmsh.model.geo.mesh.setTransfiniteCurve(21, 6)
    gmsh.model.geo.mesh.setTransfiniteCurve(23, 6)

    gmsh.model.geo.addCurveLoop([21, 22, 23, -19], 6)
    gmsh.model.geo.addPlaneSurface([6], 6)
    gmsh.model.geo.mesh.setTransfiniteSurface(6)
    gmsh.model.geo.mesh.setRecombine(2, 6)

    # Recombine
    gmsh.model.geo.mesh.setRecombine(2, 1)
    gmsh.model.geo.mesh.setRecombine(2, 2)
    gmsh.model.geo.mesh.setRecombine(2, 3)
    gmsh.model.geo.mesh.setRecombine(2, 4)
    gmsh.model.geo.mesh.setRecombine(2, 5)
    gmsh.model.geo.mesh.setRecombine(2, 6)

    gmsh.model.geo.synchronize()

    gmsh.model.addPhysicalGroup(2, [2, 3], 15)  # Al
    gmsh.model.addPhysicalGroup(2, [1], 16)  # 压电

    gmsh.model.addPhysicalGroup(1, [6, 9, 10, 11], 17)  # 正电极
    gmsh.model.addPhysicalGroup(1, [4, 12, 13, 14], 18)  # 负电极
    gmsh.model.addPhysicalGroup(1, [8, 16, 18, 21], 19)  # 左边界
    gmsh.model.addPhysicalGroup(1, [17, 2, 20, 23], 20)  # 右边界
    gmsh.model.addPhysicalGroup(1, [22], 21)  # 固定边界

    gmsh.model.addPhysicalGroup(2, [4], 22)  # 基底 SiO2
    gmsh.model.addPhysicalGroup(2, [5], 23)  # 基底 poly-Si
    gmsh.model.addPhysicalGroup(2, [6], 24)  # pml

    gmsh.option.setNumber("Mesh.Algorithm", 8)
    gmsh.option.setNumber("Mesh.RecombinationAlgorithm", 1)  # or 3
    gmsh.option.setNumber("Mesh.SubdivisionAlgorithm", 1)
    gmsh.model.mesh.generate(2)

    # Set the element order and the desired interpolation order:
    elementOrder = 2
    gmsh.model.mesh.setOrder(elementOrder)



    # if '-nopopup' not in sys.argv:
    #     gmsh.fltk.initialize()

    # v = gmsh.view.getTags()
    # gmsh.graphics.draw()
    # gmsh.write("mesh.jpg")




def build_mesh():
    """SAW_PeriodBC1_LT42: 调用 GM(...) 构建 2D 网格(从 MATLAB 仓库 .py 复制并函数化)。"""
    return GM(1.085, 0, 0.17, 0.5, 0.6, 0.5,6.9,0,0.5,0.2,0)


if __name__ == "__main__":
    import sys
    build_mesh()
    gmsh.write("SAW_PeriodBC1_LT42.m")
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()
    gmsh.finalize()
