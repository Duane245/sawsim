function pml = initialPML(nodeCoordinates,gamma1_2,pitch,msh,material_type)

pml_dmax = 1e11;
pml_n = 3;


pml_xp_low = nodeCoordinates(gamma1_2(1),2);   % 底部厚度
pml_xa_low = pml_xp_low+2*pitch;   % 底部厚度     多层结构导致底部xa不等于0 需要设置初始值


pml(3).indx = find(msh.QUADS9(:,10) == 13)';

pml(3).ya = pml_xa_low;
pml(3).yp = pml_xp_low;
pml(3).dmax = pml_dmax;
pml(3).n = pml_n;
pml(3).rho = material_type(1).rho;
pml(3).C = material_type(1).C;
pml(3).e = material_type(1).e;
pml(3).eps = material_type(1).eps;
end

