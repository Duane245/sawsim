function C_Al = ComputingC2D(nu,E)
C_Al = [(1-nu)*E/((1-2*nu)*(1+nu)),nu*E/((1-2*nu)*(1+nu)) nu*E/((1-2*nu)*(1+nu)) 0 0 0;
    nu*E/((1-2*nu)*(1+nu)) (1-nu)*E/((1-2*nu)*(1+nu)) nu*E/((1-2*nu)*(1+nu)) 0 0 0;
    nu*E/((1-2*nu)*(1+nu)) nu*E/((1-2*nu)*(1+nu)) (1-nu)*E/((1-2*nu)*(1+nu)) 0 0 0;
    0 0 0 E/2/(1+nu) 0 0;
    0 0 0 0 E/2/(1+nu) 0;
    0 0 0 0 0 E/2/(1+nu)];

C_Al = [C_Al(1,1) C_Al(1,2) C_Al(1,6);
    C_Al(2,1) C_Al(2,2) C_Al(2,6); 
    C_Al(6,1) C_Al(6,2) C_Al(6,6)];
end

