%% LT
material_type(1).rho = 7450;
C_LN = [2.32966e+011 4.68904e+010	8.02342e+010	-1.10267e+010	0	0;
4.68904e+010	2.32966e+011	8.02342e+010	1.10267e+010	0	0;
8.02342e+010	8.02342e+010	2.75364e+011	0	0	0;
-1.10267e+010	1.10267e+010	0	9.38995e+010	0	0;
0	0	0	0	9.38995e+010	-1.10267e+010;
0	0	0	0	-1.10267e+010	9.3038e+010];

e_LN = [0	0	0	0	2.59576	-1.58923;
-1.58923	1.58923	0	2.59576	0	0;
0.0821598	0.0821598	1.88197	0	0	0];

eps0 = 8.854e-12;
eps_LN = [40.9	0	0;
0	40.9	0;
0	0	43.3]*eps0;

% oula Transfer  
oula = [0;-48;0];
[C,e,eps] = oulaTransfer(oula,C_LN,e_LN,eps_LN);

%% 3D
material_type(1).C = C;
material_type(1).e = e;
material_type(1).eps = eps;
%% Al
material_type(2).rho = 2700;

E_Al = 70e9;
nu_Al = 0.33;
material_type(2).C = ComputingC(nu_Al,E_Al);

material_type(2).e = zeros(3,6);

material_type(2).eps = [1 0 0;
    0 1 0;
    0 0 1]*eps0;
