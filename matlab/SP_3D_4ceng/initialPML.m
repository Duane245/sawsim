function pml = initialPML(nodeCoordinates,gamma1_2,pitch,msh,material_type)
pml_dmax = 1e11;
pml_n = 3;


pml_xp_low = nodeCoordinates(gamma1_2(1),3);   % 底部厚度     多层结构导致底部xa不等于0 需要设置初始值
pml_xa_low = pml_xp_low+2*pitch;   % 底部厚度

pml(3).indx = find(msh.HEXAS27(:,28) == 12)';

pml(3).za = pml_xa_low;
pml(3).zp = pml_xp_low;
pml(3).dmax = pml_dmax;
pml(3).n = pml_n;
pml(3).rho = material_type(5).rho;
pml(3).C = material_type(5).C;
pml(3).e = material_type(5).e;
pml(3).eps = material_type(5).eps;
end
