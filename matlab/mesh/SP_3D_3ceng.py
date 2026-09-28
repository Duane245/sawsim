import gmsh
import math
import os
import sys

gmsh.initialize()

gmsh.model.add("SP_3D_3ceng")

# LT
p = 1.085
w = 2 * p  # 波长
d = 0.17  # 指条厚度

h1 = 0.6
h2 = 0.5
h3 = 6*p
h4 = 2*p
h = h1 + h2 + h3 + h4  # 压电材料高度

MR = 0.5  # 金属化比例
lc = 2 * p / 10  # 离散尺寸
width = 2 * p / 10

NN = 1
NN1 = 3
NN2 = 3
NN3 = 30
NN4 = 11

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

gmsh.model.geo.extrude([(2, 1), (2, 2), (2, 3), (2, 4), (2, 5)], 0, 0, -h1, [NN1], [], True)
gmsh.model.geo.extrude([(2, 2), (2, 4)], 0, 0, d, [NN], [], True)

gmsh.model.geo.extrude([(2, 38), (2, 60), (2, 82), (2, 104), (2, 126)], 0, 0, -h2, [NN2], [], True)
gmsh.model.geo.extrude([(2, 192), (2, 214), (2, 236), (2, 258), (2, 280)], 0, 0, -h3, [NN3], [], True)

gmsh.model.geo.extrude([(2, 302), (2, 324), (2, 346), (2, 368), (2, 390)], 0, 0, -h4, [NN4], [], True)

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

gmsh.model.addPhysicalGroup(3, [1, 2, 3, 4, 5], 7)  # 压电体
gmsh.model.addPhysicalGroup(3, [6, 7], 8)  # 电极体
gmsh.model.addPhysicalGroup(3, [8, 9, 10, 11, 12], 9)  # 基底体
gmsh.model.addPhysicalGroup(3, [13, 14, 15, 16, 17], 10)  # 基底体1
gmsh.model.addPhysicalGroup(3, [18, 19, 20, 21, 22], 11)  # 基底体2

gmsh.model.addPhysicalGroup(2, [37, 191, 301, 411], 1)  # 左平面
gmsh.model.addPhysicalGroup(2, [117, 271, 381, 491], 2)  # 右平面

gmsh.model.addPhysicalGroup(2, [33, 55, 77, 99, 121, 143, 165, 187, 209, 231, 253, 275, 297, 319, 341, 363, 385, 407, 429, 451, 473, 495], 3)  # 后平面
gmsh.model.addPhysicalGroup(2, [25, 47, 69, 91, 113, 135, 157, 179, 201, 223, 245, 267, 289, 311, 333, 355, 377, 399, 421, 443, 465, 487], 4)  # 前平面

gmsh.model.addPhysicalGroup(2, [412, 434, 456, 478, 500], 5)  # 底平面

gmsh.model.addPhysicalGroup(2, [2, 148, 135, 139, 143, 147], 7)  # 正电极
gmsh.model.addPhysicalGroup(2, [4, 170, 157, 161, 165, 169], 8)  # 负电极

gmsh.model.addPhysicalGroup(2, [1, 3, 5], 100)  # 画图平面

gmsh.model.mesh.generate(3)

elementOrder = 2
gmsh.model.mesh.setOrder(elementOrder)

gmsh.write("SP_3D_3ceng.m")

# Launch the GUI to see the results:
if '-nopopup' not in sys.argv:
    gmsh.fltk.run()

gmsh.finalize()
