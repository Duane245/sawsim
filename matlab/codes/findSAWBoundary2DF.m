function [gamma1_2,gamma1_zheng,gamma1_fu,gamma1_XFL,gamma1_XFR] = findSAWBoundary2DF(msh)
indx_bottom = find(msh.LINES3(:,4) == 7)';
indx_XFL = find(msh.LINES3(:,4) == 3)';
indx_XFR = find(msh.LINES3(:,4) == 4)';

indx_zheng = find(msh.LINES3(:,4) == 5)';
indx_fu = find(msh.LINES3(:,4) == 6)';


gamma1_2 = unique(msh.LINES3(indx_bottom,1:3));
gamma1_XFL = unique(msh.LINES3(indx_XFL,1:3));
gamma1_XFR = unique(msh.LINES3(indx_XFR,1:3));

gamma1_zheng = unique(msh.LINES3(indx_zheng,1:3));
gamma1_fu = unique(msh.LINES3(indx_fu,1:3));
end

