%% Add solver-core and mesh folders to the path
addpath('../codes');
addpath('../mesh');

% 128°YX-LiNbO3
%%
% clear memory
clear; close all
%%
ME = 0;    % 是否打开模态扩展
fre = 16e8:0.02e8:20e8;
%%
initial_material_parameters; 
%% mesh generation
SAW_PeriodBC1_TC; % 非结构化网格
%%
readGmsh;
%%
% GDof: global number of degrees of freedom
GDofu = 2*numberNodes;
GDoffi = numberNodes;
GDof = 3*numberNodes; 
%%
Boundary = boundary_idx_2DS(gamma1_2,gamma1_L,gamma1_R,gamma1_zheng,gamma1_fu, ...
    nodeCoordinates,numberNodes,GDofu,ME);

%% PML
pitch = 1.9936e-6;
pml = initialPML(nodeCoordinates,gamma1_2,pitch,msh,material_type);
%%
plot_Gmsh2D(msh,nodeCoordinates);

%%
V = 0.1;
indx = 1;
Q = zeros(size(fre));
Y = zeros(size(fre));
tic
%% calculation of the system stiffness matrix
AssemblyKM2D;

%% 求解Ax=b时需要去掉的自由度 prescribedDof（固定边界和周期边界自由度）
prescribedDof = [Boundary.machine.fix;
    Boundary.machine.period_R;
    Boundary.electric.period_R;
    Boundary.electric.zheng; 
    Boundary.electric.fu];

for f = fre

disp(f*1e-9);
omega = 2*pi*f;

A = -omega^2*mass + stiffness;

% boundary conditions 
A = boundaryPeriodic2D(A,GDof,Boundary);
%% force vector 
force = forces(GDof,A,Boundary,V);

% solution
displacements = solution(GDof,prescribedDof,A,force);
%% 周期边界赋值
displacements(Boundary.machine.period_R) = displacements(Boundary.machine.period_L);
displacements(Boundary.electric.period_R) = displacements(Boundary.electric.period_L);

displacements(Boundary.electric.zheng) = V;
displacements(Boundary.electric.fu) = 0;
%% 0.6
qs1 = stiffness(Boundary.electric.zheng,:)*displacements;
Q(indx) = sum(qs1);
Y(indx) = abs(1i*omega*Q(indx)/(V));
indx = indx + 1;
end
toc;
%% 绘制位移场
plot_displacements_field2D(displacements,nodeCoordinates,numberNodes,msh)
%% 绘制电势场
plot_phi_field2D(displacements,nodeCoordinates,numberNodes,msh)
%% 绘制导纳曲线
plotY11(fre,Y)
%% 保存变量
save Y11.mat Q Y fre
