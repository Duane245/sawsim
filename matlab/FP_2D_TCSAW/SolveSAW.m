%% Add solver-core and mesh folders to the path
addpath('../codes');
addpath('../mesh');

% 128°YX-LiNbO3
% PML和主体分开计算，节约时间
%%
% clear memory
clear; close all
tic

ME = 0;    % 是否打开模态扩展
fre = 1.6e9:0.002e9:2e9;
%%
initial_material_parameters;     % 不同的模型需要更改
%% 加载网格
SAW_TC_PML3;
%%
readGmsh;

%%
% GDof: global number of degrees of freedom
GDofu = 2*numberNodes;
GDoffi = numberNodes;
GDof = 3*numberNodes; 
disp(['求解的自由度数:',num2str(GDof)]);
%%
Boundary = boundary_idx_2DF(gamma1_XFL,gamma1_XFR,gamma1_2,gamma1_zheng,gamma1_fu,numberNodes,GDofu,ME);
%% initialize PML

pml_width = 1.9936e-6;      % PML厚度
pml = initialPML(nodeCoordinates,gamma1_2,pml_width,msh,material_type);

%% 绘制网格
plot_Gmsh2D(msh,nodeCoordinates);
%% 构建质量、刚度矩阵

V = 1;
indx = 1;
Q = zeros(size(fre));
Y = zeros(size(fre));

%% 求解Ax=b时需要去掉的自由度 prescribedDof（固定边界和周期边界自由度）
prescribedDof = [Boundary.machine.fix;
    Boundary.electric.zheng; Boundary.electric.fu;
    Boundary.electric.XFL(2:end);Boundary.electric.XFR(2:end)];


%% calculation of the system stiffness matrix
AssemblyKM2D;

for f = fre
    
disp(f);
omega = 2*pi*f;

A = -omega^2*mass + stiffness;

%% force vector 
force = forces(GDof,A,Boundary,V);

%% 悬浮电势
A(Boundary.electric.XFL(1),:) = sum(A(Boundary.electric.XFL,:));
A(Boundary.electric.XFR(1),:) = sum(A(Boundary.electric.XFR,:));

A(:,Boundary.electric.XFL(1)) = sum(A(:,Boundary.electric.XFL),2);
A(:,Boundary.electric.XFR(1)) = sum(A(:,Boundary.electric.XFR),2);
%% 求解有限元矩阵
displacements = solution(GDof,prescribedDof,A,force);

%% 电极和悬浮电势的解
displacements(Boundary.electric.zheng) = V;
displacements(Boundary.electric.fu) = 0;
displacements(Boundary.electric.XFL(2:end)) = displacements(Boundary.electric.XFL(1));
displacements(Boundary.electric.XFR(2:end)) = displacements(Boundary.electric.XFR(1));

%% 计算电荷量和Y参数
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
