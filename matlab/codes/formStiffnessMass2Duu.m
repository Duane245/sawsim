function [stiffness,mass] = formStiffnessMass2Duu(GDof,GDoffi, ...
    elementNodes,numberNodes,nodeCoordinates, ...
    thickness,elemType, quadType,material_type,ME)

% compute stiffness and mass matrix
% for plane stress quadrilateral elements

% Sparse Matrix
stiffness = sparse(GDof,GDof);
mass = sparse(GDof+GDoffi,GDof+GDoffi);


% quadrature according to quadType
[gaussWeights,gaussLocations] = gaussQuadrature(quadType);

number_of_material = size(material_type,2);

for i = 1:number_of_material
for e = material_type(i).indx
    indice = elementNodes(e,:);
    if ME == 0
        elementDof1 = [indice(1) indice(1)+numberNodes,...
            indice(2) indice(2)+numberNodes,...
            indice(3) indice(3)+numberNodes,...
            indice(4) indice(4)+numberNodes,...
            indice(5) indice(5)+numberNodes,...
            indice(6) indice(6)+numberNodes,...
            indice(7) indice(7)+numberNodes,...
            indice(8) indice(8)+numberNodes,...
            indice(9) indice(9)+numberNodes];
    else
    end
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
            B = zeros(3,2*ndof);
            B(1,2*(1:ndof)-1)         = XYderivatives(:,1)';
            B(2,2*(1:ndof))           = XYderivatives(:,2)';
            B(3,2*(1:ndof)-1)         = XYderivatives(:,2)';
            B(3,2*(1:ndof))           = XYderivatives(:,1)';
        else
        end
        
        % stiffness matrix
        stiffness(elementDof1,elementDof1) = ...
            stiffness(elementDof1,elementDof1) + ...
            B'*material_type(i).C*thickness*B*gaussWeights(q)*det(Jacob);
        % mass matrix
        mass(indice,indice)=mass(indice,indice) + ...
            shapeFunction*shapeFunction'* ...
            material_type(i).rho*thickness*gaussWeights(q)*det(Jacob);
        mass(indice+numberNodes,indice+numberNodes) = ...
            mass(indice+numberNodes,indice+numberNodes) + ...
            shapeFunction*shapeFunction'* ...
            material_type(i).rho*thickness*gaussWeights(q)*det(Jacob);
        if ME == 1
        end
        
    end
end
end

end
