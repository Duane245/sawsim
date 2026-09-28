function [C,e,eps] = oulaTransfer(oula,C_LN,e_LN,eps_LN)
phi = oula(1)*pi/180;
theta = oula(2)*pi/180;
psi =oula(3)*pi/180;

a = [cos(psi) sin(psi) 0;-sin(psi) cos(psi) 0;0 0 1] * ...
    [1 0 0;0 cos(theta) sin(theta);0 -sin(theta) cos(theta)] * ...
    [cos(phi) sin(phi) 0;-sin(phi) cos(phi) 0;0 0 1];

M1 = a.^2;
M2 = [2*a(:,2).*a(:,3) 2*a(:,1).*a(:,3) 2*a(:,1).*a(:,2)];
M3 = [a(2,:).*a(3,:);a(1,:).*a(3,:);a(1,:).*a(2,:)];
M4 = [a(2,2)*a(3,3)+a(2,3)*a(3,2) a(2,1)*a(3,3)+a(2,3)*a(3,1) a(2,2)*a(3,1)+a(2,1)*a(3,2);
    a(1,2)*a(3,3)+a(1,3)*a(3,2) a(1,3)*a(3,1)+a(1,1)*a(3,3) a(1,1)*a(3,2)+a(1,2)*a(3,1);
    a(1,2)*a(2,3)+a(1,3)*a(2,2) a(1,3)*a(2,1)+a(1,1)*a(2,3) a(1,1)*a(2,2)+a(1,2)*a(2,1)];

M = [M1 M2;M3 M4];

C = M*C_LN*M';
e = a * e_LN * M';
eps = a * eps_LN * a';

end

