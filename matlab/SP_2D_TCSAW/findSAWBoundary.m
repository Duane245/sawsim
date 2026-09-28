function [gamma1_2,gamma1_L,gamma1_R,gamma1_zheng,gamma1_fu] = findSAWBoundary(msh)
indx_left = find(msh.LINES3(:,4) == 19)';
indx_bottom = find(msh.LINES3(:,4) == 21)';
indx_right = find(msh.LINES3(:,4) == 20)';

indx_zheng = find(msh.LINES3(:,4) == 17)';
indx_fu = find(msh.LINES3(:,4) == 18)';


gamma1_2 = unique(msh.LINES3(indx_bottom,1:3));
gamma1_L = unique(msh.LINES3(indx_left,1:3));
gamma1_R = unique(msh.LINES3(indx_right,1:3));

gamma1_zheng = unique(msh.LINES3(indx_zheng,1:3));
gamma1_fu = unique(msh.LINES3(indx_fu,1:3));
end

