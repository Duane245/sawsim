function [stiffness,mass] = formStiffnessMass2DPMLuu(stiffness, mass,...
    elementNodes,numberNodes,nodeCoordinates, ...
    thickness,elemType, quadType,pml,omega,ME)

% compute stiffness and mass matrix
% for plane stress quadrilateral elements

% quadrature according to quadType
[gaussWeights,gaussLocations] = gaussQuadrature(quadType);

number_of_boundary = size(pml,2);

for i = 1:number_of_boundary
for e = pml(i).indx
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
        % updating C,rho
        if i == 1 || i == 5 || i == 6|| i == 7 || i == 8 || i == 9 || i == 10 || i == 11
            x1 = nodeCoordinates(indice(end),1);
            d_x1 = pml(i).dmax * ( 1 - (x1-pml(i).xp)^2/(pml(i).xa-pml(i).xp)^2 )^pml(i).n;
            alpha1 = 1 + d_x1/(1i*omega);
            alpha2 = 1;
            alpha3 = 1;
        end
        if i == 3
            y1 = nodeCoordinates(indice(end),2);
            d_y1 = pml(i).dmax * ( 1 - (y1-pml(i).yp)^2/(pml(i).ya-pml(i).yp)^2 )^pml(i).n;
            alpha1 = 1;
            alpha2 = 1 + d_y1/(1i*omega);
            alpha3 = 1;
        end
        if i == 2 || i == 4
            x1 = nodeCoordinates(indice(end),1);
            d_x1 = pml(i).dmax * ( 1 - (x1-pml(i).xp)^2/(pml(i).xa-pml(i).xp)^2 )^pml(i).n;
            y1 = nodeCoordinates(indice(end),2);
            d_y1 = pml(i).dmax * ( 1 - (y1-pml(i).yp)^2/(pml(i).ya-pml(i).yp)^2 )^pml(i).n;
            alpha1 = 1 + d_x1/(1i*omega);
            alpha2 = 1 + d_y1/(1i*omega);
            alpha3 = 1;
        end
        
        
        rho1 = pml(i).rho*alpha1*alpha2*alpha3;
        if ME == 0
            C_piezoelectric1 = pml(i).C .* [alpha2*alpha3/alpha1 alpha3 alpha2*alpha3/alpha1;
                alpha3 alpha1*alpha3/alpha2 alpha3;
                alpha3 alpha1*alpha3/alpha2 alpha3];
        else
        end
        
        % stiffness matrix
        stiffness(elementDof1,elementDof1) = ...
            stiffness(elementDof1,elementDof1) + ...
            B'*C_piezoelectric1*thickness*B*gaussWeights(q)*det(Jacob);
        % mass matrix
        mass(indice,indice)=mass(indice,indice) + ...
            shapeFunction*shapeFunction'* ...
            rho1*thickness*gaussWeights(q)*det(Jacob);
        mass(indice+numberNodes,indice+numberNodes) = ...
            mass(indice+numberNodes,indice+numberNodes) + ...
            shapeFunction*shapeFunction'* ...
            rho1*thickness*gaussWeights(q)*det(Jacob);
        if ME == 1
        end
        
    end
end
end


end
