%% Add solver-core and mesh folders to the path
addpath('../codes');
addpath('../mesh');

% 128°YX-LiNbO3
%%
% clear memory
clear; close all
%%
pitch = 1.085e-6;
fre = 1.5e9:0.001e9:2.7e9;

%%
initial_material_parameters;
%% mesh generation
SP_3D_1ceng;
%% read mesh
readGmsh;
%% GDof: global number of degrees of freedom
GDofu = 3*numberNodes;
GDoffi = numberNodes;     % phi的自由度
GDof = GDofu+GDoffi;     % ux uy uz phi
%% Boundaru indx
Boundary = boundary_idx3D(gamma1_2,gamma1_L,gamma1_R,gamma1_front,gamma1_back, ...
    gamma1_zheng,gamma1_fu,nodeCoordinates,numberNodes,GDofu);
%% PML
pml = initialPML(nodeCoordinates,gamma1_2,pitch,msh,material_type);
%% plot 3D model
plot_Gmsh3D(msh,nodeCoordinates);
% 
plot_nodes27(nodeCoordinates,elementNodes(material_type(1).indx,:))
%%
V = 1;
indx = 1;
tic
%% calculation of the system stiffness matrix
AssemblyKM3D;

%% 求解Ax=b时需要去掉的自由度 prescribedDof（固定边界和周期边界自由度）
prescribedDof = [Boundary.machine.fix;
    Boundary.machine.period_B;
    Boundary.machine.period_R;
    Boundary.electric.period_R;
    Boundary.electric.period_B;
    Boundary.electric.zheng; 
    Boundary.electric.fu];

for f = fre

disp(f*1e-9);
omega = 2*pi*f;

A = -omega^2*mass + stiffness;
 
%% boundary conditions
A = boundaryPeriodic1_3D(A,GDof,Boundary);
%% force vector 
force = forces(GDof,A,Boundary,V);
%% solution
displacements = solution(GDof,prescribedDof,A,force);

%% 周期边界赋值
displacements(Boundary.machine.period_R) = displacements(Boundary.machine.period_L);
displacements(Boundary.machine.period_B) = displacements(Boundary.machine.period_F);

displacements(Boundary.electric.period_R) = displacements(Boundary.electric.period_L);
displacements(Boundary.electric.period_B) = displacements(Boundary.electric.period_F);

displacements(Boundary.electric.zheng) = V;
displacements(Boundary.electric.fu) = 0;
qs1 = stiffness(Boundary.electric.zheng,:)*displacements;
Q(indx) = sum(qs1);
Y(indx) = abs(1i*omega*Q(indx)/(V));
indx = indx + 1;
end
time = toc;
%%
fprintf('历时: %6.0f seconds',time);

%% 绘制位移场
plot_displacements_field3D(displacements,nodeCoordinates,numberNodes,msh)
%% 绘制电势场
plot_phi_field3D(displacements,nodeCoordinates,numberNodes,msh)
%% 绘制导纳曲线
plotY11(fre,Y)
%% 保存变量
save Y11.mat Q Y fre time
