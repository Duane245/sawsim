function stiffness = formStiffnessMass3DPMLfi(stiffness, ...
    elementNodes,nodeCoordinates, ...
    thickness,elemType, quadType,pml,omega)


% quadrature according to quadType
[gaussWeights,gaussLocations] = gaussQuadrature(quadType);

number_of_boundary = size(pml,2);

for i = 1:number_of_boundary
for e = pml(i).indx
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
        
        
        % updating C
        if i == 1 || i == 5 || i == 6|| i == 7 || i == 8 || i == 9 || i == 10 || i == 11
            x1 = nodeCoordinates(indice(end),1);
            d_x1 = pml(i).dmax * ( 1 - (x1-pml(i).xp)^2/(pml(i).xa-pml(i).xp)^2 )^pml(i).n;
            alpha1 = 1 + d_x1/(1i*omega);
            alpha2 = 1;
            alpha3 = 1;
        end
        if i == 3
            z1 = nodeCoordinates(indice(end),3);
            d_z1 = pml(i).dmax * ( 1 - (z1-pml(i).zp)^2/(pml(i).za-pml(i).zp)^2 )^pml(i).n;
            alpha1 = 1;
            alpha2 = 1;
            alpha3 = 1 + d_z1/(1i*omega);
        end
        if i == 2 || i == 4
            x1 = nodeCoordinates(indice(end),1);
            d_x1 = pml(i).dmax * ( 1 - (x1-pml(i).xp)^2/(pml(i).xa-pml(i).xp)^2 )^pml(i).n;
            z1 = nodeCoordinates(indice(end),3);
            d_z1 = pml(i).dmax * ( 1 - (z1-pml(i).zp)^2/(pml(i).za-pml(i).zp)^2 )^pml(i).n;
            alpha1 = 1 + d_x1/(1i*omega);
            alpha2 = 1;
            alpha3 = 1 + d_z1/(1i*omega);
        end
        
        C_piezoelectric1 = pml(i).eps .* [alpha2*alpha3/alpha1 alpha3 alpha2;
            alpha3 alpha1*alpha3/alpha2 alpha1;
            alpha2 alpha1 alpha1*alpha2/alpha3];
        
        % stiffness matrix
        stiffness(elementDof,elementDof) = ...
            stiffness(elementDof,elementDof) + ...
            B'*C_piezoelectric1*thickness*B*gaussWeights(q)*det(Jacob);
    end
end
end


end
