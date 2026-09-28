% calculation of the system stiffness matrix
[massuu,stiffnessuu,stiffnessfifi,stiffnessufi,stiffnessfiu] = formStiffnessMass2D(GDofu,GDoffi, ...
    elementNodes,numberNodes,nodeCoordinates,material_type,ME);

omega = 2*pi*fre(end);
[mass,stiffness] = formStiffnessMass2DPML(massuu,stiffnessuu,stiffnessfifi,stiffnessufi,stiffnessfiu,...
    elementNodes,numberNodes,nodeCoordinates,pml,omega,ME);
