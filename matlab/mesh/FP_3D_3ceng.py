import gmsh
import math
import os
import sys
import numpy as np

def GM(pitch, n_idt, Aperture, eta, Hidt, Hidt_LT,Hidt_LT2, Hidt_LT3,Hidt_PML, n_f, n_we, msh_max, msh_min, msh_r, msh_f):
    gmsh.initialize()

    gmsh.model.add("FP_3D_3ceng")

    # 算例一
    n_f = int(n_f)  # 对称结构 单侧悬浮电势的种类数
    n_we = int(n_we)  # 对称结构 单侧电极的种类数

    w = 2 * pitch  # 波长
    d = Hidt  # 指条厚度
    h = Hidt_LT  # 压电材料高度
    h2 = Hidt_LT2  # 压电材料第二层高度
    h3 = Hidt_LT3  # 压电材料第三层高度
    h_pml = Hidt_PML  # 压电材料高度

    nn = len(n_idt)
    idx_e = math.floor(nn/2)  # 向下取整
    Nidt_e = n_idt[idx_e]
    p = pitch[idx_e]

    lc = msh_min  # or 0.3
    # lc = 2 * p / 6  # 离散尺寸

    width = 0.2
    # NN = 20
    # NN = 20
    # NN_ed = 1
    NN = math.ceil(h/lc)
    NN_ed = math.ceil(d/lc)
    NN2 = math.ceil(h2/lc)
    NN3 = math.ceil(h3/lc)
    NN_PML = 10  # 固定十层

    nn = len(n_idt)

    n_w1 = n_idt[n_f:(n_f + n_we)]
    n_w2 = n_idt[(n_f + n_we)+1:(n_f + 2*n_we)+1]

    Nidt_WL = np.sum(n_w1)  # 左半边加权电极的个数
    Nidt_WR = np.sum(n_w2)  # 右半边加权电极的个数

    nn = len(n_idt)
    idx_e = math.floor(nn/2)  # 向下取整
    Nidt_e = n_idt[idx_e]
    p = pitch[idx_e]

    Nidt = Nidt_WL + Nidt_e + Nidt_WR

    N_zheng = math.ceil(Nidt / 2)  # 正电极根数 向上取整
    N_fu = math.floor(Nidt / 2)

    N_side = 3 * p  # 两侧附加宽度
    N_IDT = np.sum(n_idt)

    N_fl = np.sum(n_idt[0:n_f])  # 左侧反射栅的根数
    N_fr = np.sum(n_idt[-n_f:])  # 右侧反射栅的根数


    # # PML厚度
    pml = 2 * p  # or 2
    # 器件x方向最大值
    xmax = np.sum(n_idt * pitch) + 2 * N_side

    # 质量矩阵组装 网格
    # p = 2
    # w = 2 * p  # 波长
    # d = 0.12  # 指条厚度
    # h = 8  # 压电材料高度
    # MR = 0.6  # 金属化比例
    # width = 0.2
    #
    # lc = 0.01  # 离散尺寸
    # # NN = 20
    # NN = 50
    # NN_ed = int(d/lc)

    # LT
    # p = 1.085
    # w = 2 * p  # 波长
    # d = 0.17  # 指条厚度
    # h = 8  # 压电材料高度
    # MR = 0.5  # 金属化比例
    # lc = 2*p/10  # 离散尺寸
    # width = 2*p/20
    # NN = 40
    # NN_ed = 1


    # 压电平面中的点
    gmsh.model.geo.addPoint(0, 0, h+pml, lc, 1)
    gmsh.model.geo.addPoint(xmax, 0, h+pml, lc, 2)
    gmsh.model.geo.addPoint(0, width, h+pml, lc, 3)
    gmsh.model.geo.addPoint(xmax, width, h+pml, lc, 4)

    # PML中的点
    gmsh.model.geo.addPoint(0 - pml, 0, h+pml, lc, 5)
    gmsh.model.geo.addPoint(xmax + pml, 0, h+pml, lc, 6)
    gmsh.model.geo.addPoint(0 - pml, width, h+pml, lc, 7)
    gmsh.model.geo.addPoint(xmax + pml, width, h+pml, lc, 8)

    # 悬浮电极起始点
    node = 1
    x1 = N_side
    idx_node = 0
    for idx in range(0, nn):
        if idx == 0:
            x1 = x1 + pitch[idx] / 2 * (1 - eta[idx])
            # x2 = width
            for t in range(1, n_idt[idx] + 1):
                gmsh.model.geo.addPoint(x1, 0, h+pml, lc, 4 * (t + node) + 1)
                gmsh.model.geo.addPoint(x1 + pitch[idx] * eta[idx], 0, h+pml, lc, 4 * (t + node) + 2)
                gmsh.model.geo.addPoint(x1, width, h+pml, lc, 4 * (t + node) + 3)
                gmsh.model.geo.addPoint(x1 + pitch[idx] * eta[idx], width, h+pml, lc, 4 * (t + node) + 4)

                x1 = x1 + pitch[idx]
        else:
            x1 = x1 - pitch[idx - 1] / 2 * ((1 - eta[idx - 1])) + pitch[idx] / 2 * ((1 - eta[idx]))
            # x2 = h
            idx_node = idx_node + n_idt[idx - 1]
            for t in range(1, n_idt[idx] + 1):
                gmsh.model.geo.addPoint(x1, 0, h+pml, lc, 4 * (t + node + idx_node) + 1)
                gmsh.model.geo.addPoint(x1 + pitch[idx] * eta[idx], 0, h+pml, lc, 4 * (t + node + idx_node) + 2)
                gmsh.model.geo.addPoint(x1, width, h+pml, lc, 4 * (t + node + idx_node) + 3)
                gmsh.model.geo.addPoint(x1 + pitch[idx] * eta[idx], width, h+pml, lc, 4 * (t + node + idx_node) + 4)

                x1 = x1 + pitch[idx]

    # 增加电极线
    for t in range(1, N_IDT + 1):
        gmsh.model.geo.addLine(4 * (t + node) + 1, 4 * (t + node) + 2, 1 + 4 * (t - 1))
        gmsh.model.geo.addLine(4 * (t + node) + 2, 4 * (t + node) + 4, 2 + 4 * (t - 1))
        gmsh.model.geo.addLine(4 * (t + node) + 4, 4 * (t + node) + 3, 3 + 4 * (t - 1))
        gmsh.model.geo.addLine(4 * (t + node) + 3, 4 * (t + node) + 1, 4 + 4 * (t - 1))

    # 增加电极之间的线
    for t in range(1, N_IDT):
        gmsh.model.geo.addLine(4 * (t + node) + 2, 4 * (t + node) + 2 + 3, (2 * t - 1) + 4 * N_IDT)
        gmsh.model.geo.addLine(4 * (t + node) + 2 + 2 + 3, 4 * (t + node) + 2 + 2, 2 * t + 4 * N_IDT)

    # 增加压电外围线
    gmsh.model.geo.addLine(1, 9, 5000)
    gmsh.model.geo.addLine(4 * N_IDT + 6, 2, 5001)
    gmsh.model.geo.addLine(2, 4, 5002)
    gmsh.model.geo.addLine(4, 4 * N_IDT + 8, 5003)
    gmsh.model.geo.addLine(4 * 1 + 7, 3, 5004)
    gmsh.model.geo.addLine(3, 1, 5005)

   # 增加PML线
    gmsh.model.geo.addLine(5, 1, 5006)
    gmsh.model.geo.addLine(2, 6, 5007)
    gmsh.model.geo.addLine(6, 8, 5008)
    gmsh.model.geo.addLine(8, 4, 5009)
    gmsh.model.geo.addLine(3, 7, 5010)
    gmsh.model.geo.addLine(7, 5, 5011)

    # 增加电极 curve loop and plane
    for t in range(1, N_IDT + 1):
        gmsh.model.geo.addCurveLoop([1 + 4 * (t - 1), 2 + 4 * (t - 1), 3 + 4 * (t - 1), 4 + 4 * (t - 1)], t)
        gmsh.model.geo.addPlaneSurface([t], t)

    gmsh.model.geo.synchronize()

    # 增加电极间 curve loop and plane
    for t in range(1, N_IDT):
        gmsh.model.geo.addCurveLoop([(2 * t - 1) + 4 * N_IDT, -(4 + 4 * t), 2 * t + 4 * N_IDT, -(2 + 4 * (t - 1))], t + N_IDT)
        gmsh.model.geo.addPlaneSurface([t + N_IDT], t + N_IDT)

    gmsh.model.geo.synchronize()

    # 增加side curve loop and plane
    # gmsh.model.geo.addCurveLoop([5000, -4, 5004, 5005], 2*N_IDT)
    # gmsh.model.geo.addPlaneSurface([2*N_IDT], 2*N_IDT)
    gmsh.model.geo.addCurveLoop([5000, -4, 5004, 5005], N_IDT + N_IDT)
    gmsh.model.geo.addPlaneSurface([N_IDT + N_IDT], N_IDT + N_IDT)
    gmsh.model.geo.addCurveLoop([5001, 5002, 5003, -(2 + 4 * (N_IDT-1))], N_IDT + N_IDT + 1)
    gmsh.model.geo.addPlaneSurface([N_IDT + N_IDT + 1], N_IDT + N_IDT + 1)

    gmsh.model.geo.synchronize()

    # 增加pml curve loop and plane
    gmsh.model.geo.addCurveLoop([5006, -5005, 5010, 5011], N_IDT + N_IDT + 2)
    gmsh.model.geo.addPlaneSurface([N_IDT + N_IDT + 2], N_IDT + N_IDT + 2)
    gmsh.model.geo.addCurveLoop([5007, 5008, 5009, -5002], N_IDT + N_IDT + 3)
    gmsh.model.geo.addPlaneSurface([N_IDT + N_IDT + 3], N_IDT + N_IDT + 3)

    gmsh.model.geo.synchronize()


    #限制前后平面之间没有点

    for t in range(1, N_IDT + 1):
        gmsh.model.geo.mesh.setTransfiniteCurve(2 + 4 * (t - 1), 2)
        gmsh.model.geo.mesh.setTransfiniteCurve(4 + 4 * (t - 1), 2)

    gmsh.model.geo.mesh.setTransfiniteCurve(5002, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(5005, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(5008, 2)
    gmsh.model.geo.mesh.setTransfiniteCurve(5011, 2)
    #左右两侧pml 控制为10列
    gmsh.model.geo.mesh.setTransfiniteCurve(5006, 11)
    gmsh.model.geo.mesh.setTransfiniteCurve(5007, 11)
    gmsh.model.geo.mesh.setTransfiniteCurve(5009, 11)
    gmsh.model.geo.mesh.setTransfiniteCurve(5010, 11)
    gmsh.model.geo.synchronize()

    complement_idt_tags = []  # 电极体
    complement_pe_tags = []  # 压电体
    complement_pe2_tags = []  # 第二层-二氧化硅层
    complement_pe3_tags = []  # 第三层-硅层
    complement_pml_low_tags = []  # pml体 底low
    complement_pml_left_tags = []  # pml体 左0 上
    complement_pml_left1_tags = []  # pml体 左1 中
    complement_pml_left2_tags = []  # pml体 左2 中
    complement_pml_left3_tags = []  # pml体 左2 下
    complement_pml_right_tags = []  # pml体 右0 上
    complement_pml_right1_tags = []  # pml体 右1 中
    complement_pml_right2_tags = []  # pml体 右2 中
    complement_pml_right3_tags = []  # pml体 右2 下

   # complement_side_tags = []  # side体

    boundary_idt_lists = []
    boundary_idt_tags = []      # 总电极列表 包含反射栅和正负电极
    boundary_idt_p_tags = []    # 正电极
    boundary_idt_n_tags = []    # 负电极
    boundary_front_tags = []
    boundary_rear_tags = []
    boundary_left_tags = []
    boundary_right_tags = []
    boundary_other_tags = []
    boundary_bottom_tags = []


    # 拉伸电极
    for t in range(1, N_IDT + 1):
        ov = gmsh.model.geo.extrude([(2, t)], 0, 0, d, [NN_ed], [], True)
        # 电极体
        complement_idt_tags.append(ov[1][1])
        # 电极面 6面
        boundary_idt_tags.append(t)
        boundary_idt_tags.append(ov[0][1])
        boundary_idt_tags.append(ov[2][1])
        boundary_idt_tags.append(ov[3][1])
        boundary_idt_tags.append(ov[4][1])
        boundary_idt_tags.append(ov[5][1])
        # boundary_idt_lists.append(boundary_idt_tags)

        # 前后面
        boundary_front_tags.append(ov[2][1])  # 从前逆时针
        boundary_rear_tags.append(ov[4][1])

        # boundary_idt_tags = []

    gmsh.model.geo.synchronize()

    # 拉伸整体
    for t in range(1, N_IDT + N_IDT + 4):
        ov = gmsh.model.geo.extrude([(2, t)], 0, 0, -h, [NN], [], True)
        #拉伸第二层
        ov2 = gmsh.model.geo.extrude([ov[0]], 0, 0, -h2, [NN2], [], True)
        # 拉伸第三层
        ov3 = gmsh.model.geo.extrude([ov2[0]], 0, 0, -h3, [NN3], [], True)
        # 拉伸pml
        ov4 = gmsh.model.geo.extrude([ov3[0]], 0, 0, -h_pml, [NN_PML], [], True)

        # 电极+电极间的面
        if t < (2 * N_IDT + 2):
            complement_pe_tags.append(ov[1][1])
            complement_pe2_tags.append(ov2[1][1])
            complement_pe3_tags.append(ov3[1][1])
            complement_pml_low_tags.append(ov4[1][1])
        # elif t == 2 * N_IDT or t == (2 * N_IDT + 1):
        #     # complement_side_tags.append(ov[1][1])
        #     complement_pe_tags.append(ov[1][1])
        #     complement_pml_low_tags.append(ov2[1][1])
        elif t == (2 * N_IDT + 2):
            complement_pml_left_tags.append(ov[1][1])
            complement_pml_left1_tags.append(ov2[1][1])
            complement_pml_left2_tags.append(ov3[1][1])
            complement_pml_left3_tags.append(ov4[1][1])
        elif t == (2 * N_IDT + 3):
            complement_pml_right_tags.append(ov[1][1])
            complement_pml_right1_tags.append(ov2[1][1])
            complement_pml_right2_tags.append(ov3[1][1])
            complement_pml_right3_tags.append(ov4[1][1])

        boundary_front_tags.append(ov[2][1])
        boundary_front_tags.append(ov2[2][1])
        boundary_front_tags.append(ov3[2][1])
        boundary_front_tags.append(ov4[2][1])
        boundary_rear_tags.append(ov[4][1])
        boundary_rear_tags.append(ov2[4][1])
        boundary_rear_tags.append(ov3[4][1])
        boundary_rear_tags.append(ov4[4][1])

        # if t == (2 * N_IDT + 2):
        #     boundary_left_tags.append(ov[5][1])
        #     boundary_left_tags.append(ov2[5][1])
        # if t == (2 * N_IDT + 3):
        #     boundary_right_tags.append(ov[3][1])
        #     boundary_right_tags.append(ov2[3][1])

        # 左右边界都放在一起  再加除电极外的所有上表面
        if t > N_IDT and t < 2 * N_IDT+4 :
            boundary_other_tags.append(t)

        if t == (2 * N_IDT + 2):
            boundary_other_tags.append(ov[5][1])
            boundary_other_tags.append(ov2[5][1])
            boundary_other_tags.append(ov3[5][1])
            boundary_other_tags.append(ov4[5][1])
        if t == (2 * N_IDT + 3):
            boundary_other_tags.append(ov[3][1])
            boundary_other_tags.append(ov2[3][1])
            boundary_other_tags.append(ov3[3][1])
            boundary_other_tags.append(ov4[3][1])

        boundary_bottom_tags.append(ov4[0][1])

    gmsh.model.geo.synchronize()


    # 网格
    for t in range(1, N_IDT + N_IDT + 4):
        gmsh.model.mesh.setTransfiniteSurface(t)
        gmsh.model.mesh.setRecombine(2, t)

    gmsh.model.addPhysicalGroup(3, complement_pe_tags, 7, name="压电")  # 压电平面
    gmsh.model.addPhysicalGroup(3, complement_idt_tags, 8, name="电极")
    gmsh.model.addPhysicalGroup(3, complement_pe2_tags, 9, name="二氧化硅")  # 第二层
    gmsh.model.addPhysicalGroup(3, complement_pe3_tags, 10, name="硅")  # 第三层
    # gmsh.model.addPhysicalGroup(3, complement_side_tags, 9, name="side")
    # left-PML
    gmsh.model.addPhysicalGroup(3, complement_pml_left_tags, 1001, name="pml_left")
    # left-PML-1
    gmsh.model.addPhysicalGroup(3, complement_pml_left1_tags, 1002, name="pml_left1")
    # left-PML-2
    gmsh.model.addPhysicalGroup(3, complement_pml_left2_tags, 1006, name="pml_left2")
    # left-PML-3
    gmsh.model.addPhysicalGroup(3, complement_pml_left3_tags, 1008, name="pml_left3")
    # low-PML
    gmsh.model.addPhysicalGroup(3, complement_pml_low_tags, 1003, name="pml_low")
    # right-PML-3
    gmsh.model.addPhysicalGroup(3, complement_pml_right3_tags, 1009, name="pml_right3")
    # right-PML-2
    gmsh.model.addPhysicalGroup(3, complement_pml_right2_tags, 1007, name="pml_right2")
    # right-PML-1
    gmsh.model.addPhysicalGroup(3, complement_pml_right1_tags, 1004, name="pml_right1")
    # right-PML
    gmsh.model.addPhysicalGroup(3, complement_pml_right_tags, 1005, name="pml_right")


    # gmsh.model.addPhysicalGroup(2, boundary_left_tags, 1, name="左平面")  # 左平面
    # gmsh.model.addPhysicalGroup(2, boundary_right_tags, 2, name="右平面")  # 右平面
    gmsh.model.addPhysicalGroup(2, boundary_other_tags, 2)  # 右平面  此分组不命名
    gmsh.model.addPhysicalGroup(2, boundary_rear_tags, 3, name="后平面")  # 后平面
    gmsh.model.addPhysicalGroup(2, boundary_front_tags, 4, name="前平面")  # 前平面
    gmsh.model.addPhysicalGroup(2, boundary_bottom_tags, 5, name="底平面")  # 底平面

    # boundary_idt_fl_tags = boundary_idt_tags[0:6 * N_fl]
    gmsh.model.addPhysicalGroup(2, boundary_idt_tags[0:6*N_fl], 6, name="左反射栅")  # 左反射栅
    # boundary_idt_fr_tags = boundary_idt_tags[-6 * N_fr:]
    gmsh.model.addPhysicalGroup(2, boundary_idt_tags[-6 * N_fr:], 7, name="右反射栅")  # 右反射栅

    for t in range(0, N_zheng):
        boundary_idt_p_tags.extend(boundary_idt_tags[6 * N_fl + 12 * t: 6 * N_fl + 6 + 12 * t])
    gmsh.model.addPhysicalGroup(2, boundary_idt_p_tags, 8, name="正电极")  # 正电极
    for t in range(0, N_fu):
        boundary_idt_n_tags.extend(boundary_idt_tags[6 * N_fl + 6 + 12 * t: 6 * N_fl + 12 + 12 * t])
    gmsh.model.addPhysicalGroup(2, boundary_idt_n_tags, 9, name="负电极")  # 负电极

    gmsh.model.mesh.generate(3)

    elementOrder = 2
    gmsh.model.mesh.setOrder(elementOrder)


    gmsh.write("FP_3D_3ceng.m")

    # Launch the GUI to see the results:
    if '-nopopup' not in sys.argv:
        gmsh.fltk.run()

    gmsh.finalize()

# pitch = np.array([1, 2, 1, 2, 1, 2, 1, 2, 1])
# n_idt = np.array([4, 4, 3, 4, 5, 4, 3, 2, 1])
# eta = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
# n_f = 2
# n_we = 2

# n_f = 1
# n_we = 3

pitch = np.array([1, 1, 1])  # 左悬浮电势 中间IDT 右悬浮电势
n_idt = np.array([6, 13, 6])  # 对应根数
eta = np.array([0.5, 0.5, 0.5])   # 对应金属化率
# n_idt = np.array([2, 3, 2])  # 对应根数
# eta = np.array([0.2, 0.8, 0.2])   # 对应金属化率
n_f = 1   # 对称结构 单侧悬浮电势的种类数
n_we = 0   # 对称结构 单侧电极的种类数

msh = GM(pitch, n_idt, 2, eta, 0.2, 0.6, 0.5,6.9,1.085*2, n_f, n_we, 0, 0.15, 0, 0)
