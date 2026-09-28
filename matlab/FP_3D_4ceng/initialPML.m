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

pml(6).name = 'left1';
pml(7).name = 'right1';

pml(8).name = 'left2';
pml(9).name = 'right2';

pml(10).name = 'left3';
pml(11).name = 'right3';

pml(1).indx = find(msh.HEXAS27(:,28) == 1001)';
pml(2).indx = find(msh.HEXAS27(:,28) == 1010)';
pml(3).indx = find(msh.HEXAS27(:,28) == 1003)';
pml(4).indx = find(msh.HEXAS27(:,28) == 1011)';
pml(5).indx = find(msh.HEXAS27(:,28) == 1005)';

pml(6).indx = find(msh.HEXAS27(:,28) == 1002)';
pml(7).indx = find(msh.HEXAS27(:,28) == 1004)';

pml(8).indx = find(msh.HEXAS27(:,28) == 1006)';
pml(9).indx = find(msh.HEXAS27(:,28) == 1007)';

pml(10).indx = find(msh.HEXAS27(:,28) == 1008)';
pml(11).indx = find(msh.HEXAS27(:,28) == 1009)';

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
pml(2).rho = material_type(5).rho;
pml(2).C = material_type(5).C;
pml(2).e = material_type(5).e;
pml(2).eps = material_type(5).eps;

pml(3).za = pml_low_xa;
pml(3).zp = pml_low_xp;
pml(3).dmax = pml_dmax;
pml(3).n = pml_n;
pml(3).rho = material_type(5).rho;
pml(3).C = material_type(5).C;
pml(3).e = material_type(5).e;
pml(3).eps = material_type(5).eps;

pml(4).xa = pml_right_xa;
pml(4).xp = pml_right_xp;
pml(4).za = pml_low_xa;
pml(4).zp = pml_low_xp;
pml(4).dmax = pml_dmax;
pml(4).n = pml_n;
pml(4).rho = material_type(5).rho;
pml(4).C = material_type(5).C;
pml(4).e = material_type(5).e;
pml(4).eps = material_type(5).eps;

pml(5).xa = pml_right_xa;
pml(5).xp = pml_right_xp;
pml(5).dmax = pml_dmax;
pml(5).n = pml_n;
pml(5).rho = material_type(1).rho;
pml(5).C = material_type(1).C;
pml(5).e = material_type(1).e;
pml(5).eps = material_type(1).eps;

pml(6).xa = pml_left_xa;
pml(6).xp = pml_left_xp;
pml(6).dmax = pml_dmax;
pml(6).n = pml_n;
pml(6).rho = material_type(3).rho;
pml(6).C = material_type(3).C;
pml(6).e = material_type(3).e;
pml(6).eps = material_type(3).eps;

pml(7).xa = pml_right_xa;
pml(7).xp = pml_right_xp;
pml(7).dmax = pml_dmax;
pml(7).n = pml_n;
pml(7).rho = material_type(3).rho;
pml(7).C = material_type(3).C;
pml(7).e = material_type(3).e;
pml(7).eps = material_type(3).eps;

pml(8).xa = pml_left_xa;
pml(8).xp = pml_left_xp;
pml(8).dmax = pml_dmax;
pml(8).n = pml_n;
pml(8).rho = material_type(4).rho;
pml(8).C = material_type(4).C;
pml(8).e = material_type(4).e;
pml(8).eps = material_type(4).eps;

pml(9).xa = pml_right_xa;
pml(9).xp = pml_right_xp;
pml(9).dmax = pml_dmax;
pml(9).n = pml_n;
pml(9).rho = material_type(4).rho;
pml(9).C = material_type(4).C;
pml(9).e = material_type(4).e;
pml(9).eps = material_type(4).eps;

pml(10).xa = pml_left_xa;
pml(10).xp = pml_left_xp;
pml(10).dmax = pml_dmax;
pml(10).n = pml_n;
pml(10).rho = material_type(5).rho;
pml(10).C = material_type(5).C;
pml(10).e = material_type(5).e;
pml(10).eps = material_type(5).eps;

pml(11).xa = pml_right_xa;
pml(11).xp = pml_right_xp;
pml(11).dmax = pml_dmax;
pml(11).n = pml_n;
pml(11).rho = material_type(5).rho;
pml(11).C = material_type(5).C;
pml(11).e = material_type(5).e;
pml(11).eps = material_type(5).eps;
