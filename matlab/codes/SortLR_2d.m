function [gamma1_L_new,gamma1_R_new] = SortLR_2d(gamma1_L,gamma1_R,nodeCoordinates)

indx_L = gamma1_L;
indx_R = gamma1_R;
%%  descend, X_V节点在上方
% [~,I_L] = sort( nodeCoordinates(indx_L,2) , 'descend');
% [~,I_R] = sort( nodeCoordinates(indx_R,2), 'descend' );

%%   X_V节点在下方 利于拼接逻辑
[~,I_L] = sort( nodeCoordinates(indx_L,2) );
[~,I_R] = sort( nodeCoordinates(indx_R,2)  );

indx_L_new = indx_L(I_L);
indx_R_new = indx_R(I_R);

gamma1_L_new = indx_L_new;
gamma1_R_new = indx_R_new;
end

