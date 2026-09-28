function [stiffness,mass] = formStiffnessMass3Dfi(GDof, ...
    elementNodes,numberNodes,nodeCoordinates, ...
    thickness,elemType, quadType,material_type)


stiffness = sparse(GDof,GDof);

% quadrature according to quadType
[gaussWeights,gaussLocations] = gaussQuadrature(quadType);

number_of_material = size(material_type,2);

for i = 1:number_of_material
for e = material_type(i).indx
    indice = elementNodes(e,:);
    elementDof = indice;
    ndof = length(indice);
    
    % cycle for Gauss point
    for q = 1:size(gaussWeights,1)
        GaussPoint = gaussLocations(q,:);
        xi = GaussPoint(1);
        eta = GaussPoint(2);
        zeta = GaussPoint(3);
        
        % shape functions and derivatives
        [shapeFunction,naturalDerivatives] = ...
            shapeFunctionsQ3D(xi,eta,zeta,elemType);
        
        % Jacobian matrix, inverse of Jacobian,
        % derivatives w.r.t. x,y
        [Jacob,invJacobian,XYderivatives] = ...
            Jacobian(nodeCoordinates(indice,:),naturalDerivatives);
        
        %  B matrix
        B = zeros(3,ndof);
        B(1,1:ndof) = XYderivatives(:,1)';
        B(2,1:ndof) = XYderivatives(:,2)';
        B(3,1:ndof) = XYderivatives(:,3)';
        
        % stiffness matrix
        stiffness(elementDof,elementDof) = ...
            stiffness(elementDof,elementDof) + ...
            B'*material_type(i).eps*thickness*B*gaussWeights(q)*det(Jacob);
    end
end
end

end
