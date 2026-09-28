function Boundary = Boundary_idx3DF(gamma1_XFL,gamma1_XFR,gamma1_front,gamma1_back, ...
    gamma1_2,gamma1_zheng,gamma1_fu,nodeCoordinates,numberNodes,GDofu)
%% 前后面消去电极节点
gammal_frontzheng = intersect(gamma1_front,gamma1_zheng);
gammal_backzheng = intersect(gamma1_back,gamma1_zheng);
gammal_frontfu = intersect(gamma1_front,gamma1_fu);
gammal_backfu = intersect(gamma1_back,gamma1_fu);

gamma1_front = setdiff(gamma1_front,[gammal_frontzheng;gammal_frontfu]);
gamma1_back = setdiff(gamma1_back,[gammal_backzheng;gammal_backfu]);
%% 前后面消去悬浮电势节点
gammal_frontXFL = intersect(gamma1_front,gamma1_XFL);
gammal_backXFL = intersect(gamma1_back,gamma1_XFL);
gammal_frontXFR = intersect(gamma1_front,gamma1_XFR);
gammal_backXFR = intersect(gamma1_back,gamma1_XFR);

gamma1_front = setdiff(gamma1_front,[gammal_frontXFL;gammal_frontXFR]);
gamma1_back = setdiff(gamma1_back,[gammal_backXFL;gammal_backXFR]);
%% 前后面消去底边节点
gammal_2F =intersect(gamma1_2,gamma1_front);
gammal_2b =intersect(gamma1_2,gamma1_back);

gamma1_front = setdiff(gamma1_front,gammal_2F);
gamma1_back = setdiff(gamma1_back,gammal_2b);

%% 对称排序
[gamma1_front,gamma1_back] = SortFB_3d(gamma1_front,gamma1_back,nodeCoordinates);

% 电极边界
[gammal_frontzheng,gammal_backzheng] = SortFB_3d(gammal_frontzheng,gammal_backzheng,nodeCoordinates);
[gammal_frontfu,gammal_backfu] = SortFB_3d(gammal_frontfu,gammal_backfu,nodeCoordinates);

% 悬浮边界
[gammal_frontXFL,gammal_backXFL] = SortFB_3d(gammal_frontXFL,gammal_backXFL,nodeCoordinates);
[gammal_frontXFR,gammal_backXFR] = SortFB_3d(gammal_frontXFR,gammal_backXFR,nodeCoordinates);

[gammal_2F,gammal_2b] = SortFB_3d(gammal_2F,gammal_2b,nodeCoordinates);

%% 边界条件
% 固体力学
Boundary.machine.period_F = ...
    [gamma1_front;       gamma1_front+numberNodes;        gamma1_front+2*numberNodes;
    gammal_frontzheng;   gammal_frontzheng+numberNodes;   gammal_frontzheng+2*numberNodes;
    gammal_frontfu;      gammal_frontfu+numberNodes;      gammal_frontfu+2*numberNodes;
    gammal_frontXFL;     gammal_frontXFL+numberNodes;     gammal_frontXFL+2*numberNodes;
    gammal_frontXFR;     gammal_frontXFR+numberNodes;     gammal_frontXFR+2*numberNodes];

Boundary.machine.period_B = ...
    [gamma1_back;       gamma1_back+numberNodes;        gamma1_back+2*numberNodes;
    gammal_backzheng;   gammal_backzheng+numberNodes;   gammal_backzheng+2*numberNodes;
    gammal_backfu;      gammal_backfu+numberNodes;      gammal_backfu+2*numberNodes;
    gammal_backXFL;     gammal_backXFL+numberNodes;     gammal_backXFL+2*numberNodes;
    gammal_backXFR;     gammal_backXFR+numberNodes;     gammal_backXFR+2*numberNodes;];

Boundary.machine.fix = [gamma1_2; gamma1_2+numberNodes;  gamma1_2+2*numberNodes;];

% 静电
Boundary.electric.period_F = [gamma1_front+GDofu;  gammal_2F+GDofu];
Boundary.electric.period_B = [gamma1_back+GDofu;   gammal_2b+GDofu];

Boundary.electric.zheng = gamma1_zheng+GDofu;
Boundary.electric.fu = gamma1_fu+GDofu;

Boundary.electric.XFL = gamma1_XFL+GDofu;
Boundary.electric.XFR = gamma1_XFR+GDofu;


end
