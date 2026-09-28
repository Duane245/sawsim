function stiffness = formStiffnessMass3DPMLufi(stiffness, ...
    elementNodes,numberNodes,nodeCoordinates, ...
    thickness,elemType, quadType,pml,omega)


% quadrature according to quadType
[gaussWeights,gaussLocations] = gaussQuadrature(quadType);

number_of_boundary = size(pml,2);

for i = 1:number_of_boundary
for e = pml(i).indx
    indice = elementNodes(e,:);
    elementDof1 = [indice(1) indice(1)+numberNodes indice(1)+2*numberNodes,...
        indice(2) indice(2)+numberNodes indice(2)+2*numberNodes,...
        indice(3) indice(3)+numberNodes indice(3)+2*numberNodes,...
        indice(4) indice(4)+numberNodes indice(4)+2*numberNodes,...
        indice(5) indice(5)+numberNodes indice(5)+2*numberNodes,...
        indice(6) indice(6)+numberNodes indice(6)+2*numberNodes,...
        indice(7) indice(7)+numberNodes indice(7)+2*numberNodes,...
        indice(8) indice(8)+numberNodes indice(8)+2*numberNodes,...
        indice(9) indice(9)+numberNodes indice(9)+2*numberNodes,...
        indice(10) indice(10)+numberNodes indice(10)+2*numberNodes,...
        indice(11) indice(11)+numberNodes indice(11)+2*numberNodes,...
        indice(12) indice(12)+numberNodes indice(12)+2*numberNodes,...
        indice(13) indice(13)+numberNodes indice(13)+2*numberNodes,...
        indice(14) indice(14)+numberNodes indice(14)+2*numberNodes,...
        indice(15) indice(15)+numberNodes indice(15)+2*numberNodes,...
        indice(16) indice(16)+numberNodes indice(16)+2*numberNodes,...
        indice(17) indice(17)+numberNodes indice(17)+2*numberNodes,...
        indice(18) indice(18)+numberNodes indice(18)+2*numberNodes,...
        indice(19) indice(19)+numberNodes indice(19)+2*numberNodes,...
        indice(20) indice(20)+numberNodes indice(20)+2*numberNodes,...
        indice(21) indice(21)+numberNodes indice(21)+2*numberNodes,...
        indice(22) indice(22)+numberNodes indice(22)+2*numberNodes,...
        indice(23) indice(23)+numberNodes indice(23)+2*numberNodes,...
        indice(24) indice(24)+numberNodes indice(24)+2*numberNodes,...
        indice(25) indice(25)+numberNodes indice(25)+2*numberNodes,...
        indice(26) indice(26)+numberNodes indice(26)+2*numberNodes,...
        indice(27) indice(27)+numberNodes indice(27)+2*numberNodes];
    elementDoffi = indice;
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
        B = zeros(6,3*ndof);
        B(1,3*(1:ndof)-2)         = XYderivatives(:,1)';
        B(2,3*(1:ndof)-1)         = XYderivatives(:,2)';
        B(3,3*(1:ndof))           = XYderivatives(:,3)';
        
        B(4,3*(1:ndof)-1)         = XYderivatives(:,3)';
        B(4,3*(1:ndof))           = XYderivatives(:,2)';
        
        B(5,3*(1:ndof)-2)         = XYderivatives(:,3)';
        B(5,3*(1:ndof))           = XYderivatives(:,1)';
        
        B(6,3*(1:ndof)-2)         = XYderivatives(:,2)';
        B(6,3*(1:ndof)-1)         = XYderivatives(:,1)';
        
        Bfi = zeros(3,ndof);
        Bfi(1,1:ndof) = XYderivatives(:,1)';
        Bfi(2,1:ndof) = XYderivatives(:,2)';
        Bfi(3,1:ndof) = XYderivatives(:,3)';
        
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
        
        C_piezoelectric1 = pml(i).e .* [alpha2*alpha3/alpha1 alpha3 alpha2 alpha2 alpha2 alpha3;
            alpha3 alpha1*alpha3/alpha2 alpha1 alpha1 alpha1 alpha1*alpha3/alpha2;
            alpha2 alpha1 alpha1*alpha2/alpha3 alpha1*alpha2/alpha3 alpha1*alpha2/alpha3 alpha1];
        
        
        % stiffness matrix
        stiffness(elementDof1,elementDoffi) = ...
            stiffness(elementDof1,elementDoffi) + ...
            B'*C_piezoelectric1'*thickness*Bfi*gaussWeights(q)*det(Jacob);
        
    end
end
end
    
    
end
