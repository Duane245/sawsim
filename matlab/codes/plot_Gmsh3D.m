function  plot_Gmsh3D(msh,nodeCoordinates)
figure;
patch('Faces',msh.QUADS9(:,1:4),'Vertices',nodeCoordinates*1e6,'facecolor','c','Linewidth',1)
axis equal

% box on;
set(gca,'linewidth',2,'fontsize',18)

xlim([min(nodeCoordinates(:,1)*1e6),max(nodeCoordinates(:,1)*1e6)])
zlim([min(nodeCoordinates(:,3)*1e6),max(nodeCoordinates(:,3)*1e6)])
view(-45,12)

title('Meshing')
xlabel('\itx/\mu\itm')
ylabel('\ity/\mu\itm')
end
