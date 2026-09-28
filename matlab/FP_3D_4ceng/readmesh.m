nodeCoordinates = msh.POS(:,1:3)*1e-6;
elementNodes = msh.HEXAS27(:,1:27);

numberNodes = msh.nbNod;
numberElements = size(elementNodes,1);

material_type(1).indx = find(msh.HEXAS27(:,28) == 7)';
material_type(2).indx = find(msh.HEXAS27(:,28) == 8)';
material_type(3).indx = find(msh.HEXAS27(:,28) == 9)';
material_type(4).indx = find(msh.HEXAS27(:,28) == 10)';
material_type(5).indx = find(msh.HEXAS27(:,28) == 11)';

[gamma1_XFL,gamma1_XFR,gamma1_front,gamma1_back,gamma1_2,gamma1_zheng,gamma1_fu] = ...
    findSAWBoundary3DF(msh);
