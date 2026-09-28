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

%     0.61 1.11  0;
%     0 0 0.261]*1e11;

material_type(2).e = zeros(3,6);

material_type(2).eps = [1 0 0;
    0 1 0;
    0 0 1]*eps0;
%% Si
material_type(3).rho = 2330;

% material_type(3).C = ComputingC(nu,E);

C_Si = [166	64	64	0	0	0;
64	166	64	0	0	0;
64	64	166	0	0	0;
0	0	0	80	0	0;
0	0	0	0	80	0;
0	0	0	0	0	80]*1e9;
material_type(3).C = C_Si;


material_type(3).e = zeros(3,6);

% material_type(3).eps = [11.7 0 0;
%     0 11.7 0;
%     0 0 11.7]*eps0;
material_type(3).eps = [11.68 0 0;
    0 11.68 0;
    0 0 11.68]*eps0;
