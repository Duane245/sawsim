function [massuu,stiffnessuu,stiffnessfifi,stiffnessufi,stiffnessfiu] = formStiffnessMass3D(GDofu,GDoffi,...
    elementNodes,numberNodes,nodeCoordinates,material_type)


[stiffnessuu,massuu] = formStiffnessMass3Duu(GDofu,GDoffi, ...
    elementNodes,numberNodes,nodeCoordinates,1,'H27','H20',material_type);
stiffnessfifi = formStiffnessMass3Dfi(GDoffi, ...
    elementNodes,numberNodes,nodeCoordinates,1,'H27','H20',material_type);
stiffnessufi = formStiffnessMass3Dufi(GDofu,GDoffi,...
    elementNodes,numberNodes,nodeCoordinates,1,'H27','H20',material_type);

stiffnessfiu = stiffnessufi';

end
