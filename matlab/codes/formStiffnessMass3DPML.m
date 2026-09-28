function [massuu,stiffness] = formStiffnessMass3DPML(massuu,...
    stiffnessuu,stiffnessfifi,stiffnessufi,stiffnessfiu,...
    elementNodes,numberNodes,nodeCoordinates,pml,omega)
[stiffnessuu,massuu] = formStiffnessMass3DPMLuu(stiffnessuu, massuu, ...
    elementNodes,numberNodes,nodeCoordinates,1,'H27','H20',pml,omega);

stiffnessfifi = formStiffnessMass3DPMLfi(stiffnessfifi, ...
    elementNodes,nodeCoordinates,1,'H27','H20',pml,omega);

stiffnessufi = formStiffnessMass3DPMLufi(stiffnessufi,...
    elementNodes,numberNodes,nodeCoordinates,1,'H27','H20',pml,omega);

stiffnessfiu = formStiffnessMass3DPMLfiu(stiffnessfiu, ...
    elementNodes,numberNodes,nodeCoordinates,1,'H27','H20',pml,omega);

scale = 6.173191780858575e-11;
stiffnessuu = stiffnessuu * scale;
stiffnessfiu = stiffnessfiu * scale;
massuu = massuu * scale;

stiffness = [stiffnessuu stiffnessufi;stiffnessfiu -stiffnessfifi];

end
