function [gamma1_f_new,gamma1_b_new] = SortFB_3d(gamma1_front,gamma1_back,nodeCoordinates)
cor = round(nodeCoordinates*1e9,1);


indx_f = gamma1_front;
indx_b = gamma1_back;

[~,I_f] = sort(cor(indx_f,1) + 1i*cor(indx_f,3),'ComparisonMethod','real');
[~,I_b] = sort(cor(indx_b,1) + 1i*cor(indx_b,3),'ComparisonMethod','real');

indx_f_new = indx_f(I_f);
indx_b_new = indx_b(I_b);

gamma1_f_new = indx_f_new;
gamma1_b_new = indx_b_new;
end
