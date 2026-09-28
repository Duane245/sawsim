function [gamma1_L_new,gamma1_R_new] = SortLR_3d(gamma1_L,gamma1_R,nodeCoordinates)
cor = round(nodeCoordinates*1e9,1);

indx_L = gamma1_L;
indx_R = gamma1_R;

[~,I_L] = sort(cor(indx_L,2) + 1i*cor(indx_L,3),'ComparisonMethod','real');
[~,I_R] = sort(cor(indx_R,2) + 1i*cor(indx_R,3),'ComparisonMethod','real');

indx_L_new = indx_L(I_L);
indx_R_new = indx_R(I_R);

gamma1_L_new = indx_L_new;
gamma1_R_new = indx_R_new;
end
