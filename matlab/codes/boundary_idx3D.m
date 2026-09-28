function Boundary = boundary_idx3D(gamma1_2,gamma1_L,gamma1_R,gamma1_front,gamma1_back, ...
    gamma1_zheng,gamma1_fu,nodeCoordinates,numberNodes,GDofu)
%% 消去电极节点
gammal_frontzheng = intersect(gamma1_front,gamma1_zheng);
gammal_backzheng = intersect(gamma1_back,gamma1_zheng);
gammal_frontfu = intersect(gamma1_front,gamma1_fu);
gammal_backfu = intersect(gamma1_back,gamma1_fu);

gamma1_front = setdiff(gamma1_front,[gammal_frontzheng;gammal_frontfu]);
gamma1_back = setdiff(gamma1_back,[gammal_backzheng;gammal_backfu]);

%% 消去底边节点
gammal_2F =intersect(gamma1_2,gamma1_front);
gammal_2b =intersect(gamma1_2,gamma1_back);
gammal_2L =intersect(gamma1_2,gamma1_L);
gammal_2R =intersect(gamma1_2,gamma1_R);

gammal_Lb_e = intersect(gamma1_L,gamma1_back);
gammal_Rb_e = intersect(gamma1_R,gamma1_back);

gammal_2Lb = intersect(gamma1_2,gammal_Lb_e);
gammal_2Rb = intersect(gamma1_2,gammal_Rb_e);

gammal_2L_e = setdiff(gammal_2L,gammal_2Lb);
gammal_2R_e = setdiff(gammal_2R,gammal_2Rb);

%%
gamma1_front = setdiff(gamma1_front,gammal_2F);
gamma1_back = setdiff(gamma1_back,gammal_2b);
gamma1_L = setdiff(gamma1_L,gammal_2L);
gamma1_R = setdiff(gamma1_R,gammal_2R);

%% 消去周期边界点
gammal_LF = intersect(gamma1_L,gamma1_front);
gammal_RF = intersect(gamma1_R,gamma1_front);
gammal_Lb = intersect(gamma1_L,gamma1_back);
gammal_Rb = intersect(gamma1_R,gamma1_back);

% gamma1_front = setdiff(gamma1_front,[gammal_RF;gammal_LF]);
% gamma1_back = setdiff(gamma1_back,[gammal_Rb;gammal_Lb]);
% gamma1_L = setdiff(gamma1_L,[gammal_Lb;gammal_LF]);
% gamma1_R = setdiff(gamma1_R,[gammal_Rb;gammal_RF]);

gamma1_L = setdiff(gamma1_L,gammal_Lb);
gamma1_R = setdiff(gamma1_R,gammal_Rb);

%% 对称排序
[gamma1_L,gamma1_R] = SortLR_3d(gamma1_L,gamma1_R,nodeCoordinates);
[gamma1_front,gamma1_back] = SortFB_3d(gamma1_front,gamma1_back,nodeCoordinates);

[gammal_2F,gammal_2b] = SortFB_3d(gammal_2F,gammal_2b,nodeCoordinates);

% 周期边界
[gammal_2L_e,gammal_2R_e] = SortLR_3d(gammal_2L_e,gammal_2R_e,nodeCoordinates);

% 电极边界
[gammal_frontzheng,gammal_backzheng] = SortFB_3d(gammal_frontzheng,gammal_backzheng,nodeCoordinates);
[gammal_frontfu,gammal_backfu] = SortFB_3d(gammal_frontfu,gammal_backfu,nodeCoordinates);

%% 边界条件
% 固体力学
Boundary.machine.period_F = ...
    [gamma1_front;       gamma1_front+numberNodes;        gamma1_front+2*numberNodes;
    gammal_frontzheng;   gammal_frontzheng+numberNodes;   gammal_frontzheng+2*numberNodes;
    gammal_frontfu;      gammal_frontfu+numberNodes;      gammal_frontfu+2*numberNodes];

Boundary.machine.period_B = ...
    [gamma1_back;       gamma1_back+numberNodes;        gamma1_back+2*numberNodes;
    gammal_backzheng;   gammal_backzheng+numberNodes;   gammal_backzheng+2*numberNodes;
    gammal_backfu;      gammal_backfu+numberNodes;      gammal_backfu+2*numberNodes];

Boundary.machine.period_L = ...
    [gamma1_L;       gamma1_L+numberNodes;        gamma1_L+2*numberNodes];

Boundary.machine.period_R = ...
    [gamma1_R;       gamma1_R+numberNodes;        gamma1_R+2*numberNodes];

Boundary.machine.fix = [gamma1_2; gamma1_2+numberNodes;  gamma1_2+2*numberNodes;];

% 静电
Boundary.electric.period_F = [gamma1_front+GDofu;  gammal_2F+GDofu];
Boundary.electric.period_B = [gamma1_back+GDofu;   gammal_2b+GDofu];

Boundary.electric.period_L = [gamma1_L+GDofu;   gammal_2L_e+GDofu];
Boundary.electric.period_R = [gamma1_R+GDofu;   gammal_2R_e+GDofu];

Boundary.electric.zheng = gamma1_zheng+GDofu;
Boundary.electric.fu = gamma1_fu+GDofu;
end
