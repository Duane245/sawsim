function [stiffness] = boundaryPeriodic1_3DF(stiffness,GDof,Boundary)
% function [stiffness,mass] = boundaryPeriodic1(stiffness,mass,GDof,numberNodes,gamma1_L,gamma1_R,gamma11,gamma12,gamma21,gamma22)

gamma1_L1 = [Boundary.machine.period_F;Boundary.electric.period_F];

gamma1_R1 = [Boundary.machine.period_B;Boundary.electric.period_B];

gamma1_21 = Boundary.machine.fix;

activeDof = setdiff((1:GDof)', [gamma1_L1;gamma1_R1;gamma1_21]);

stiffness(gamma1_L1,gamma1_L1) = stiffness(gamma1_L1,gamma1_L1) ...
    + stiffness(gamma1_L1,gamma1_R1)...
    + stiffness(gamma1_R1,gamma1_L1) ...
    + stiffness(gamma1_R1,gamma1_R1);

stiffness(gamma1_L1,activeDof) = stiffness(gamma1_L1,activeDof)...
    + stiffness(gamma1_R1,activeDof);

stiffness(activeDof,gamma1_L1) = stiffness(activeDof,gamma1_L1)...
    + stiffness(activeDof,gamma1_R1);


end
