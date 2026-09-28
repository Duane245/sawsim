function stiffness = formStiffnessMass2Dfi(GDof, ...
    elementNodes,numberNodes,nodeCoordinates, ...
    thickness,elemType, quadType,material_type,ME)

% compute stiffness and mass matrix
% for plane stress quadrilateral elements

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
        
        % shape functions and derivatives
        [shapeFunction,naturalDerivatives] = ...
            shapeFunctionsQ2D(xi,eta,elemType);
        
        % Jacobian matrix, inverse of Jacobian,
        % derivatives w.r.t. x,y
        [Jacob,invJacobian,XYderivatives] = ...
            Jacobian(nodeCoordinates(indice,:),naturalDerivatives);
        
        %  B matrix
        if ME == 0
            B = zeros(2,ndof);
            B(1,1:ndof) = XYderivatives(:,1)';
            B(2,1:ndof) = XYderivatives(:,2)';
        else
        end
        
        % stiffness matrix
        stiffness(elementDof,elementDof) = ...
            stiffness(elementDof,elementDof) + ...
            B'*material_type(i).eps*thickness*B*gaussWeights(q)*det(Jacob);
    end
end
end

end
