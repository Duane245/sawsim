function [gamma1_L,gamma1_R,gamma1_front,gamma1_back,gamma1_2,gamma1_zheng,gamma1_fu] = findSAWBoundary3DS(msh)
indx_left = find(msh.QUADS9(:,10) == 1)';

indx_right = find(msh.QUADS9(:,10) == 2)';

indx_front = find(msh.QUADS9(:,10) == 4)';
indx_back = find(msh.QUADS9(:,10) == 3)';

indx_bottom = find(msh.QUADS9(:,10) == 5)';

indx_zheng = find(msh.QUADS9(:,10) == 7)';
indx_fu = find(msh.QUADS9(:,10) == 8)';

gamma1_2 = unique(msh.QUADS9(indx_bottom,1:9));

gamma1_L = unique(msh.QUADS9(indx_left,1:9),"stable");
gamma1_R = unique(msh.QUADS9(indx_right,1:9),"stable");

gamma1_front = unique(msh.QUADS9(indx_front,1:9),"stable");
gamma1_back = unique(msh.QUADS9(indx_back,1:9),"stable");

gamma1_zheng = unique(msh.QUADS9(indx_zheng,1:9));
gamma1_fu = unique(msh.QUADS9(indx_fu,1:9));
end
