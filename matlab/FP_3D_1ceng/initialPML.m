%% PML 参数
pml_dmax = 1e11;
pml_n = 3;

pml_left_xa = min(nodeCoordinates(gamma1_2,1))+pml_width;
pml_left_xp = min(nodeCoordinates(gamma1_2,1));

pml_low_xa = min(nodeCoordinates(gamma1_2,3))+pml_width;
pml_low_xp = min(nodeCoordinates(gamma1_2,3));

pml_right_xa = max(nodeCoordinates(gamma1_2,1))-pml_width; % 右侧
pml_right_xp = max(nodeCoordinates(gamma1_2,1)); % 右侧

pml(1).name = 'left';
pml(2).name = 'leftlow';
pml(3).name = 'low';
pml(4).name = 'rightlow';
pml(5).name = 'right';

pml(1).indx = find(msh.HEXAS27(:,28) == 1001)';
pml(2).indx = find(msh.HEXAS27(:,28) == 1002)';
pml(3).indx = find(msh.HEXAS27(:,28) == 1003)';
pml(4).indx = find(msh.HEXAS27(:,28) == 1004)';
pml(5).indx = find(msh.HEXAS27(:,28) == 1005)';

pml(1).xa = pml_left_xa;
pml(1).xp = pml_left_xp;
pml(1).dmax = pml_dmax;
pml(1).n = pml_n;
pml(1).rho = material_type(1).rho;
pml(1).C = material_type(1).C;
pml(1).e = material_type(1).e;
pml(1).eps = material_type(1).eps;

pml(2).xa = pml_left_xa;
pml(2).xp = pml_left_xp;
pml(2).za = pml_low_xa;
pml(2).zp = pml_low_xp;
pml(2).dmax = pml_dmax;
pml(2).n = pml_n;
pml(2).rho = material_type(1).rho;
pml(2).C = material_type(1).C;
pml(2).e = material_type(1).e;
pml(2).eps = material_type(1).eps;

pml(3).za = pml_low_xa;
pml(3).zp = pml_low_xp;
pml(3).dmax = pml_dmax;
pml(3).n = pml_n;
pml(3).rho = material_type(1).rho;
pml(3).C = material_type(1).C;
pml(3).e = material_type(1).e;
pml(3).eps = material_type(1).eps;

pml(4).xa = pml_right_xa;
pml(4).xp = pml_right_xp;
pml(4).za = pml_low_xa;
pml(4).zp = pml_low_xp;
pml(4).dmax = pml_dmax;
pml(4).n = pml_n;
pml(4).rho = material_type(1).rho;
pml(4).C = material_type(1).C;
pml(4).e = material_type(1).e;
pml(4).eps = material_type(1).eps;

pml(5).xa = pml_right_xa;
pml(5).xp = pml_right_xp;
pml(5).dmax = pml_dmax;
pml(5).n = pml_n;
pml(5).rho = material_type(1).rho;
pml(5).C = material_type(1).C;
pml(5).e = material_type(1).e;
pml(5).eps = material_type(1).eps;
