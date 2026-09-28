function plot_nodes27(nodeCoordinates,elementNodes)
Xm = nodeCoordinates(elementNodes(1,:),1);
Ym = nodeCoordinates(elementNodes(1,:),2);
Zm = nodeCoordinates(elementNodes(1,:),3);
figure
scatter3(Xm, Ym, Zm, 10, 'filled', 'MarkerFaceColor', 'r', 'MarkerEdgeColor', 'r');
hold on
text(Xm,Ym,Zm,num2cell(1:27));
% axis equal
view(-45,12)
end
