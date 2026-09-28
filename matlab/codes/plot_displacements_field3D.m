function plot_displacements_field3D(displacements,nodeCoordinates,numberNodes,msh)

disptotal = real(sqrt(displacements(1:numberNodes).^2+displacements(numberNodes+1:2*numberNodes).^2+displacements(2*numberNodes+1:3*numberNodes).^2));
scaleFactor = 1e-8;
UX = real(displacements(1:numberNodes));
UY = real(displacements(numberNodes+1:2*numberNodes));
UZ = real(displacements(2*numberNodes+1:3*numberNodes));
figure
view(-45,12)
patch('Faces',msh.QUADS9(:,1:4),'Vertices',nodeCoordinates+scaleFactor*[UX UY UZ],'FaceVertexCData',disptotal,'FaceColor','interp');
axis equal
shading interp
box on;
% grid on;
% title(['特征频率=' num2str(omega_f(modeNumber)*1e-6) 'MHz'])
xlabel('\itx/\mu\itm')
ylabel('\ity/\mu\itm')
% colorbar
colormap(jet)
% axis off
end
