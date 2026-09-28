function stiffness = boundaryPeriodic2D(stiffness,GDof,Boundary)
% function [stiffness,mass] = boundaryPeriodic1(stiffness,mass,GDof,numberNodes,gamma1_L,gamma1_R,gamma11,gamma12,gamma21,gamma22)
gamma1_L1 = [Boundary.machine.period_L;         Boundary.electric.period_L];
gamma1_R1 = [Boundary.machine.period_R;         Boundary.electric.period_R];

activeDof = setdiff((1:GDof)', [gamma1_L1;gamma1_R1]);

stiffness(gamma1_L1,gamma1_L1) = stiffness(gamma1_L1,gamma1_L1) ...
    + stiffness(gamma1_L1,gamma1_R1)...
    + stiffness(gamma1_R1,gamma1_L1) ...
    + stiffness(gamma1_R1,gamma1_R1);

stiffness(gamma1_L1,activeDof) = stiffness(gamma1_L1,activeDof)...
    + stiffness(gamma1_R1,activeDof);

stiffness(activeDof,gamma1_L1) = stiffness(activeDof,gamma1_L1)...
    + stiffness(activeDof,gamma1_R1);

end

