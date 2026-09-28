%% Add solver-core and mesh folders to the path
addpath('../codes');
addpath('../mesh');

% 128°YX-LiNbO3
%%
% clear memory
clear; close all

%%
pml_width = 2e-6;      % PML厚度
fre = 1.8e9:0.001e9:2.2e9;

%%
initial_material_parameters;
%% mesh generation
FP_3D_1ceng;
%% read mesh
readmesh;
%% GDof: global number of degrees of freedom
GDofu = 3*numberNodes;    
GDoffi = numberNodes;     
GDof = 4*numberNodes; 
disp(['求解自由度' num2str(GDof)])
%% initialize PML
initialPML;
%% plot 3D model
plot_Gmsh3D(msh,nodeCoordinates);
%%
plot_nodes27(nodeCoordinates,elementNodes(material_type(1).indx,:))
% plot_nodes27(nodeCoordinates,elementNodes(pml(5).indx,:))
%% 设置边界序号
Boundary = Boundary_idx3DF(gamma1_XFL,gamma1_XFR,gamma1_front,gamma1_back, ...
    gamma1_2,gamma1_zheng,gamma1_fu,nodeCoordinates,numberNodes,GDofu);
%%    
V = 1;
indx = 1;
Q = zeros(size(fre));
Y = zeros(size(fre));
tic
%% calculation of the system stiffness matrix
AssemblyKM3D;
%% 求解Ax=b时需要去掉的自由度 prescribedDof（固定边界和周期边界自由度）
prescribedDof = ...
    [Boundary.machine.fix;
    Boundary.machine.period_B;
    Boundary.electric.period_B;
    Boundary.electric.zheng; Boundary.electric.fu;
    Boundary.electric.XFL(2:end);Boundary.electric.XFR(2:end)];

for f = fre
    
disp(f*1e-9);
omega = 2*pi*f;
A = -omega^2*mass + stiffness;
 
%% boundary conditions
A = boundaryPeriodic1_3DF(A,GDof,Boundary);   %注意固定边界处的电势自由度需要周期处理
%% 悬浮电势
A(Boundary.electric.XFL(1),:) = sum(A(Boundary.electric.XFL,:));
A(Boundary.electric.XFR(1),:) = sum(A(Boundary.electric.XFR,:));

A(:,Boundary.electric.XFL(1)) = sum(A(:,Boundary.electric.XFL),2);
A(:,Boundary.electric.XFR(1)) = sum(A(:,Boundary.electric.XFR),2);
%% force vector 
force = forces(GDof,A,Boundary,V);
%% solution
displacements = solution(GDof,prescribedDof,A,force);
%% 周期边界赋值
displacements(Boundary.machine.period_B) = displacements(Boundary.machine.period_F);
displacements(Boundary.electric.period_B) = displacements(Boundary.electric.period_F);
%% 电极和悬浮电势的解
displacements(Boundary.electric.zheng) = V;
displacements(Boundary.electric.fu) = 0;
displacements(Boundary.electric.XFL(2:end)) = displacements(Boundary.electric.XFL(1));
displacements(Boundary.electric.XFR(2:end)) = displacements(Boundary.electric.XFR(1));
%% 计算导纳
qs1 = stiffness(Boundary.electric.zheng,:)*displacements;
Q(indx) = sum(qs1);
Y(indx) = abs(1i*omega*Q(indx)/(V));
indx = indx + 1;
end
time = toc;
%%
fprintf('历时: %6.0f seconds, ',time);
%% 绘制位移场
plot_displacements_field3D(displacements,nodeCoordinates,numberNodes,msh)
%% 绘制电势场
plot_phi_field3D(displacements,nodeCoordinates,numberNodes,msh)
%% 绘制导纳曲线
plotY11(fre,Y)
%% 保存变量
save Y11.mat Q Y fre time
