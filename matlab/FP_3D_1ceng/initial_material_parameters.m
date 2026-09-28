%% 压电材料
material_type(1).rho = 4700;
C_LN = [2.02897e+011	5.29177e+010	7.49098e+010	8.99874e+009	0	0;
    5.29177e+010	2.02897e+011	7.49098e+010	-8.99874e+009	0	0;
    7.49098e+010	7.49098e+010	2.43075e+011	0	0	0;
    8.99874e+009	-8.99874e+009	0	5.99034e+010	0	0;
    0	0	0	0	5.99018e+010	8.98526e+009;
    0	0	0	0	8.98526e+009	7.48772e+010];

e_LN = [0,0,0,0,3.69594,-2.53384;
    -2.53764	2.53764	0	3.69548	0	0;
    0.193644	0.193644	1.30863	0	0	0];

eps0 = 8.854e-12;
eps_LN = [43.6 0 0;
    0 43.6 0;
    0 0 29.16]*eps0;

% oula Transfer  
oula = [0;38;0];
[C,e,eps] = oulaTransfer(oula,C_LN,e_LN,eps_LN);

% 3D
material_type(1).C = C;
material_type(1).e = e;
material_type(1).eps = eps;
%% 电极
material_type(2).rho = 2700;

E_Al = 70e9;
nu_Al = 0.33;
material_type(2).C = ComputingC(nu_Al,E_Al);

material_type(2).e = zeros(3,6);

material_type(2).eps = [1 0 0;
    0 1 0;
    0 0 1]*eps0;
