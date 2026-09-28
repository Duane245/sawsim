function [shape,naturalDerivatives] = ...
    shapeFunctionsQ3D(xi,eta,zeta,elemType)
% shape function and derivatives for Q4, Q8 and Q9 elements
% shape: Shape functions
% naturalDerivatives: derivatives w.r.t. xi and eta
% xi, eta: natural coordinates (-1 ... +1)

switch elemType
    case 'Q4' % Q4 element
        shape = 1/4*[(1-xi)*(1-eta); (1+xi)*(1-eta);
            (1+xi)*(1+eta); (1-xi)*(1+eta)];
        
        naturalDerivatives = 1/4*[
            -(1-eta), -(1-xi); 1-eta,   -(1+xi);
            1+eta ,    1+xi; -(1+eta),  1-xi];
   
    case 'Q8' % Q8 element  3D
%             -(1+xi)*(1-eta)*(1-xi+eta);
%             -(1+xi)*(1+eta)*(1-xi-eta);
%             -(1-xi)*(1+eta)*(1+xi-eta);
%             2*(1-xi*xi)*(1-eta);
%             2*(1+xi)*(1-eta*eta);
%             2*(1-xi*xi)*(1+eta);
%             2*(1-xi)*(1-eta*eta)];
%         
%             -(eta+2*xi)*(eta-1), -(2*eta+xi)*(xi-1);
%             (eta-2*xi)*(eta-1),  (2*eta-xi)*(xi+1);
%             (eta+2*xi)*(eta+1),  (2*eta+xi)*(xi+1);
%             -(eta-2*xi)*(eta+1), -(xi-1)*(2*eta-xi);
%             4*xi*(eta-1),    2*(xi^2-1);
%             2*(1-eta^2), -4*eta*(xi+1);
%             -4*xi*(eta+1), 2*(1-xi^2);
%             2*(eta^2-1), 4*eta*(xi-1)];
        
        shape = 1/8*[(1-xi)*(1-eta)*(1-zeta); 
            (1-xi)*(1-eta)*(1+zeta);
            (1+xi)*(1-eta)*(1+zeta); 
            (1+xi)*(1-eta)*(1-zeta);
            (1-xi)*(1+eta)*(1-zeta);
            (1-xi)*(1+eta)*(1+zeta);
            (1+xi)*(1+eta)*(1+zeta);
            (1+xi)*(1+eta)*(1-zeta)];
        
        naturalDerivatives = 1/8*[
            -(1-eta)*(1-zeta), -(1-xi)*(1-zeta), -(1-xi)*(1-eta); 
            -(1-eta)*(1+zeta), -(1-xi)*(1+zeta), (1-xi)*(1-eta);
            (1-eta)*(1+zeta),  -(1+xi)*(1+zeta), (1+xi)*(1-eta); 
            (1-eta)*(1-zeta),  -(1+xi)*(1-zeta), -(1+xi)*(1-eta);
            -(1+eta)*(1-zeta), (1-xi)*(1-zeta),  -(1-xi)*(1+eta);
            -(1+eta)*(1+zeta), (1-xi)*(1+zeta),  (1-xi)*(1+eta);
            (1+eta)*(1+zeta),  (1+xi)*(1+zeta),  (1+xi)*(1+eta);
            (1+eta)*(1-zeta),  (1+xi)*(1-zeta),  -(1+xi)*(1+eta)];
        
    case 'H20' 
        shape = [1/8*(1-xi)*(1-eta)*(1-zeta)*(-xi-eta-zeta-2);
            1/4*(1-xi)*(1-eta)*(1-zeta^2);
            1/8*(1-xi)*(1-eta)*(1+zeta)*(-xi-eta+zeta-2);
            1/4*(1-xi^2)*(1-eta)*(1+zeta);
            1/8*(1+xi)*(1-eta)*(1+zeta)*(xi-eta+zeta-2);
            1/4*(1+xi)*(1-eta)*(1-zeta^2);
            1/8*(1+xi)*(1-eta)*(1-zeta)*(xi-eta-zeta-2);
            1/4*(1-xi^2)*(1-eta)*(1-zeta);
            1/4*(1-xi)*(1-eta^2)*(1-zeta);
            1/4*(1-xi)*(1-eta^2)*(1+zeta);
            1/4*(1+xi)*(1-eta^2)*(1+zeta);
            1/4*(1+xi)*(1-eta^2)*(1-zeta);
            1/8*(1-xi)*(1+eta)*(1-zeta)*(-xi+eta-zeta-2);
            1/4*(1-xi)*(1+eta)*(1-zeta^2);
            1/8*(1-xi)*(1+eta)*(1+zeta)*(-xi+eta+zeta-2);
            1/4*(1-xi^2)*(1+eta)*(1+zeta);
            1/8*(1+xi)*(1+eta)*(1+zeta)*(xi+eta+zeta-2);
            1/4*(1+xi)*(1+eta)*(1-zeta^2);
            1/8*(1+xi)*(1+eta)*(1-zeta)*(xi+eta-zeta-2);
            1/4*(1-xi^2)*(1+eta)*(1-zeta)];
        
        shape = sortSF(shape);
        
        naturalDerivatives = [
            -1/8*(1-eta)*(1-zeta)*(-xi-eta-zeta-2)-1/8*(1-xi)*(1-eta)*(1-zeta),-1/8*(1-xi)*(1-zeta)*(-xi-eta-zeta-2)-1/8*(1-xi)*(1-eta)*(1-zeta),-1/8*(1-xi)*(1-eta)*(-xi-eta-zeta-2)-1/8*(1-xi)*(1-eta)*(1-zeta);
            -1/4*(1-eta)*(1-zeta^2),-1/4*(1-xi)*(1-zeta^2),-1/4*(1-xi)*(1-eta)*2*zeta;
            -1/8*(1-eta)*(1+zeta)*(-xi-eta+zeta-2)-1/8*(1-xi)*(1-eta)*(1+zeta),-1/8*(1-xi)*(1+zeta)*(-xi-eta+zeta-2)-1/8*(1-xi)*(1-eta)*(1+zeta),1/8*(1-xi)*(1-eta)*(-xi-eta+zeta-2)+1/8*(1-xi)*(1-eta)*(1+zeta);
            -1/4*2*xi*(1-eta)*(1+zeta),-1/4*(1-xi^2)*(1+zeta),1/4*(1-xi^2)*(1-eta);
            1/8*(1-eta)*(1+zeta)*(xi-eta+zeta-2)+1/8*(1+xi)*(1-eta)*(1+zeta),-1/8*(1+xi)*(1+zeta)*(xi-eta+zeta-2)-1/8*(1+xi)*(1-eta)*(1+zeta),1/8*(1+xi)*(1-eta)*(xi-eta+zeta-2)+1/8*(1+xi)*(1-eta)*(1+zeta);
            1/4*(1-eta)*(1-zeta^2),-1/4*(1+xi)*(1-zeta^2),-1/4*(1+xi)*(1-eta)*2*zeta;
            1/8*(1-eta)*(1-zeta)*(xi-eta-zeta-2)+1/8*(1+xi)*(1-eta)*(1-zeta),-1/8*(1+xi)*(1-zeta)*(xi-eta-zeta-2)-1/8*(1+xi)*(1-eta)*(1-zeta),-1/8*(1+xi)*(1-eta)*(xi-eta-zeta-2)-1/8*(1+xi)*(1-eta)*(1-zeta);
            -1/4*2*xi*(1-eta)*(1-zeta),-1/4*(1-xi^2)*(1-zeta),-1/4*(1-xi^2)*(1-eta);
            -1/4*(1-eta^2)*(1-zeta),-1/4*(1-xi)*2*eta*(1-zeta),-1/4*(1-xi)*(1-eta^2);
            -1/4*(1-eta^2)*(1+zeta),-1/4*(1-xi)*2*eta*(1+zeta),1/4*(1-xi)*(1-eta^2);
            1/4*(1-eta^2)*(1+zeta),-1/4*(1+xi)*2*eta*(1+zeta),1/4*(1+xi)*(1-eta^2);
            1/4*(1-eta^2)*(1-zeta),-1/4*(1+xi)*2*eta*(1-zeta),-1/4*(1+xi)*(1-eta^2);
            -1/8*(1+eta)*(1-zeta)*(-xi+eta-zeta-2)-1/8*(1-xi)*(1+eta)*(1-zeta),1/8*(1-xi)*(1-zeta)*(-xi+eta-zeta-2)+1/8*(1-xi)*(1+eta)*(1-zeta),-1/8*(1-xi)*(1+eta)*(-xi+eta-zeta-2)-1/8*(1-xi)*(1+eta)*(1-zeta);
            -1/4*(1+eta)*(1-zeta^2),1/4*(1-xi)*(1-zeta^2),-1/4*(1-xi)*(1+eta)*2*zeta;
            -1/8*(1+eta)*(1+zeta)*(-xi+eta+zeta-2)-1/8*(1-xi)*(1+eta)*(1+zeta),1/8*(1-xi)*(1+zeta)*(-xi+eta+zeta-2)+1/8*(1-xi)*(1+eta)*(1+zeta),1/8*(1-xi)*(1+eta)*(-xi+eta+zeta-2)+1/8*(1-xi)*(1+eta)*(1+zeta);
            -1/4*2*xi*(1+eta)*(1+zeta),1/4*(1-xi^2)*(1+zeta),1/4*(1-xi^2)*(1+eta);
            1/8*(1+eta)*(1+zeta)*(xi+eta+zeta-2)+1/8*(1+xi)*(1+eta)*(1+zeta),1/8*(1+xi)*(1+zeta)*(xi+eta+zeta-2)+1/8*(1+xi)*(1+eta)*(1+zeta),1/8*(1+xi)*(1+eta)*(xi+eta+zeta-2)+1/8*(1+xi)*(1+eta)*(1+zeta);
            1/4*(1+eta)*(1-zeta^2),1/4*(1+xi)*(1-zeta^2),-1/4*(1+xi)*(1+eta)*2*zeta;
            1/8*(1+eta)*(1-zeta)*(xi+eta-zeta-2)+1/8*(1+xi)*(1+eta)*(1-zeta),1/8*(1+xi)*(1-zeta)*(xi+eta-zeta-2)+1/8*(1+xi)*(1+eta)*(1-zeta),-1/8*(1+xi)*(1+eta)*(xi+eta-zeta-2)-1/8*(1+xi)*(1+eta)*(1-zeta);
            -1/4*2*xi*(1+eta)*(1-zeta),1/4*(1-xi^2)*(1-zeta),-1/4*(1-xi^2)*(1+eta)];
        
        naturalDerivatives = sortSF(naturalDerivatives);
        
        case 'H27'
            shape = ...
[      xi * (xi-1)       * eta * (eta-1)       * zeta * (zeta-1) / 8.0;
(xi+1) * xi             * eta * (eta-1)       * zeta * (zeta-1) / 8.0;
(xi+1) * xi       * (eta+1) * eta             * zeta * (zeta-1) / 8.0;
      xi * (xi-1) * (eta+1) * eta             * zeta * (zeta-1) / 8.0;
      xi * (xi-1)       * eta * (eta-1) * (zeta+1) * zeta       / 8.0;
(xi+1) * xi             * eta * (eta-1) * (zeta+1) * zeta       / 8.0;
(xi+1) * xi       * (eta+1) * eta       * (zeta+1) * zeta       / 8.0;
      xi * (xi-1) * (eta+1) * eta       * (zeta+1) * zeta       / 8.0;

- (xi+1)       * (xi-1)       * eta * (eta-1)       * zeta * (zeta-1) / 4.0;
- (xi+1) * xi       * (eta+1)       * (eta-1)       * zeta * (zeta-1) / 4.0;
- (xi+1)       * (xi-1) * (eta+1) * eta             * zeta * (zeta-1) / 4.0;
-       xi * (xi-1) * (eta+1)       * (eta-1)       * zeta * (zeta-1) / 4.0;
-       xi * (xi-1)       * eta * (eta-1) * (zeta+1)       * (zeta-1) / 4.0;
- (xi+1) * xi             * eta * (eta-1) * (zeta+1)       * (zeta-1) / 4.0;
- (xi+1) * xi       * (eta+1) * eta       * (zeta+1)       * (zeta-1) / 4.0;
-       xi * (xi-1) * (eta+1) * eta       * (zeta+1)       * (zeta-1) / 4.0;
- (xi+1)       * (xi-1)       * eta * (eta-1) * (zeta+1) * zeta       / 4.0;
- (xi+1) * xi       * (eta+1)       * (eta-1) * (zeta+1) * zeta       / 4.0;
- (xi+1)       * (xi-1) * (eta+1) * eta       * (zeta+1) * zeta       / 4.0;
-       xi * (xi-1) * (eta+1)       * (eta-1) * (zeta+1) * zeta       / 4.0;

  (xi+1)       * (xi-1) * (eta+1)       * (eta-1)       * zeta * (zeta-1) / 2.0;
  (xi+1)       * (xi-1)       * eta * (eta-1) * (zeta+1)       * (zeta-1) / 2.0;
  (xi+1) * xi       * (eta+1)       * (eta-1) * (zeta+1)       * (zeta-1) / 2.0;
  (xi+1)       * (xi-1) * (eta+1) * eta       * (zeta+1)       * (zeta-1) / 2.0;
        xi * (xi-1) * (eta+1)       * (eta-1) * (zeta+1)       * (zeta-1) / 2.0;
  (xi+1)       * (xi-1) * (eta+1)       * (eta-1) * (zeta+1) * zeta       / 2.0;

- (xi+1)       * (xi-1) * (eta+1)       * (eta-1) * (zeta+1)       * (zeta-1)];

shape = sortSF27(shape);

naturalDerivatives = [
  (xi-1)  * eta * (eta-1)       * zeta * (zeta-1)     / 8.0 + xi        * eta * (eta-1)       * zeta * (zeta-1)     / 8.0      (xi-1)*xi  * (eta-1)       * zeta * (zeta-1)     / 8.0 + (xi-1)*xi        * eta        * zeta * (zeta-1)     / 8.0     (xi-1)*xi       * eta * (eta-1)       * (zeta-1)     / 8.0 + (xi-1)*xi        * eta * (eta-1)       * zeta      / 8.0;
  xi      * eta * (eta-1)       * zeta * (zeta-1)     / 8.0 + (xi+1)    * eta * (eta-1)       * zeta * (zeta-1)     / 8.0      (xi+1)*xi  * (eta-1)       * zeta * (zeta-1)     / 8.0 + (xi+1)*xi        * eta        * zeta * (zeta-1)     / 8.0     (xi+1)*xi       * eta * (eta-1)       * (zeta-1)     / 8.0 + (xi+1)*xi        * eta * (eta-1)       * zeta      / 8.0;
  xi      * (eta+1) * eta       * zeta * (zeta-1)     / 8.0 + (xi+1)    * (eta+1) * eta       * zeta * (zeta-1)     / 8.0      (xi+1)*xi  * eta           * zeta * (zeta-1)     / 8.0 + (xi+1)*xi        * (eta+1)    * zeta * (zeta-1)     / 8.0     (xi+1)*xi       * (eta+1) * eta       * (zeta-1)     / 8.0 + (xi+1)*xi        * (eta+1) * eta       * zeta      / 8.0;
  (xi-1)  * (eta+1) * eta       * zeta * (zeta-1)     / 8.0 +   xi      * (eta+1) * eta       * zeta * (zeta-1)     / 8.0      (xi-1)*xi  * eta           * zeta * (zeta-1)     / 8.0 + (xi-1)*xi        * (eta+1)    * zeta * (zeta-1)     / 8.0     (xi-1)*xi       * (eta+1) * eta       * (zeta-1)     / 8.0 +   (xi-1)*xi      * (eta+1) * eta       * zeta      / 8.0;
  (xi-1)  * eta * (eta-1)       * (zeta+1) * zeta     / 8.0 +   xi      * eta * (eta-1)       * (zeta+1) * zeta     / 8.0      (xi-1)*xi  * (eta-1)       * (zeta+1) * zeta     / 8.0 + (xi-1)*xi        * eta        * (zeta+1) * zeta     / 8.0     (xi-1)*xi       * eta * (eta-1)       * zeta         / 8.0 +   (xi-1)*xi      * eta * (eta-1)       * (zeta+1)  / 8.0;
  xi      * eta * (eta-1)       * (zeta+1) * zeta     / 8.0 + (xi+1)    * eta * (eta-1)       * (zeta+1) * zeta     / 8.0      xi*(xi+1)  * (eta-1)       * (zeta+1) * zeta     / 8.0 + xi*(xi+1)        * eta        * (zeta+1) * zeta     / 8.0      xi*(xi+1)      * eta * (eta-1)       * zeta         / 8.0 + xi*(xi+1)        * eta * (eta-1)       * (zeta+1)  / 8.0;
  xi      * (eta+1) * eta       * (zeta+1) * zeta     / 8.0 + (xi+1)    * (eta+1) * eta       * (zeta+1) * zeta     / 8.0      xi*(xi+1)  * eta           * (zeta+1) * zeta     / 8.0 + xi*(xi+1)        * (eta+1)    * (zeta+1) * zeta     / 8.0      xi*(xi+1)      * (eta+1) * eta       * zeta         / 8.0 + xi*(xi+1)        * (eta+1) * eta       * (zeta+1)  / 8.0;
  (xi-1)  * (eta+1) * eta       * (zeta+1) * zeta     / 8.0 + xi        * (eta+1) * eta       * (zeta+1) * zeta     / 8.0      (xi-1)*xi  * eta           * (zeta+1) * zeta     / 8.0 + (xi-1)*xi        * (eta+1)    * (zeta+1) * zeta     / 8.0     (xi-1)*xi       * (eta+1) * eta       * zeta         / 8.0 + (xi-1)*xi        * (eta+1) * eta       * (zeta+1)  / 8.0;

(- (xi-1)  * eta * (eta-1)       * zeta * (zeta-1)     / 4.0 - (xi+1)    * eta * (eta-1)       * zeta * (zeta-1)     / 4.0) (- (xi+1)*(xi-1) * (eta-1)       * zeta * (zeta-1)     / 4.0 - (xi+1)*(xi-1)    * eta        * zeta * (zeta-1)     / 4.0)     (- (xi+1)*(xi-1) * eta * (eta-1)       * (zeta-1)     / 4.0 - (xi+1)*(xi-1)    * eta * (eta-1)       * zeta      / 4.0);
(- xi      * (eta+1) * (eta-1)   * zeta * (zeta-1)     / 4.0 - (xi+1)    * (eta+1) * (eta-1)   * zeta * (zeta-1)     / 4.0) (- (xi+1)*xi     * (eta-1)       * zeta * (zeta-1)     / 4.0 - (xi+1)*xi        * (eta+1)    * zeta * (zeta-1)     / 4.0)     (- (xi+1)*xi     * (eta+1) * (eta-1)   * (zeta-1)     / 4.0 - (xi+1)*xi        * (eta+1) * (eta-1)   * zeta      / 4.0);
(- (xi-1)  * (eta+1) * eta       * zeta * (zeta-1)     / 4.0 - (xi+1)    * (eta+1) * eta       * zeta * (zeta-1)     / 4.0) (- (xi+1)*(xi-1) * eta           * zeta * (zeta-1)     / 4.0 - (xi+1)*(xi-1)    * (eta+1)    * zeta * (zeta-1)     / 4.0)     (- (xi+1)*(xi-1) * (eta+1) * eta       * (zeta-1)     / 4.0 - (xi+1)*(xi-1)    * (eta+1) * eta       * zeta      / 4.0);
(- (xi-1)  * (eta+1) * (eta-1)   * zeta * (zeta-1)     / 4.0 -  xi       * (eta+1) * (eta-1)   * zeta * (zeta-1)     / 4.0) (- xi*(xi-1)     * (eta-1)       * zeta * (zeta-1)     / 4.0 -  xi*(xi-1)       * (eta+1)    * zeta * (zeta-1)     / 4.0)     (- xi*(xi-1)     * (eta+1) * (eta-1)   * (zeta-1)     / 4.0 -  xi*(xi-1)       * (eta+1) * (eta-1)   * zeta      / 4.0);
(- (xi-1)  * eta * (eta-1)       * (zeta+1) * (zeta-1) / 4.0 - xi        * eta * (eta-1)       * (zeta+1) * (zeta-1) / 4.0) (- xi*(xi-1)     * (eta-1)       * (zeta+1) * (zeta-1) / 4.0 - xi*(xi-1)        * eta        * (zeta+1) * (zeta-1) / 4.0)     (- xi*(xi-1)     * eta * (eta-1)       * (zeta-1)     / 4.0 - xi*(xi-1)        * eta * (eta-1)       * (zeta+1)  / 4.0);
(- xi      * eta * (eta-1)       * (zeta+1) * (zeta-1) / 4.0 - (xi+1)    * eta * (eta-1)       * (zeta+1) * (zeta-1) / 4.0) (- (xi+1)*xi     * (eta-1)       * (zeta+1) * (zeta-1) / 4.0 - (xi+1)*xi        * eta        * (zeta+1) * (zeta-1) / 4.0)     (- (xi+1)*xi     * eta * (eta-1)       * (zeta-1)     / 4.0 - (xi+1)*xi        * eta * (eta-1)       * (zeta+1)  / 4.0);
(- xi      * (eta+1) * eta       * (zeta+1) * (zeta-1) / 4.0 - (xi+1)    * (eta+1) * eta       * (zeta+1) * (zeta-1) / 4.0) (- (xi+1)*xi     * eta           * (zeta+1) * (zeta-1) / 4.0 - (xi+1)*xi        * (eta+1)    * (zeta+1) * (zeta-1) / 4.0)     (- (xi+1)*xi     * (eta+1) * eta       * (zeta-1)     / 4.0 - (xi+1)*xi        * (eta+1) * eta       * (zeta+1)  / 4.0);
(- (xi-1)  * (eta+1) * eta       * (zeta+1) * (zeta-1) / 4.0 - xi        * (eta+1) * eta       * (zeta+1) * (zeta-1) / 4.0) (- xi*(xi-1)     * eta           * (zeta+1) * (zeta-1) / 4.0 - xi*(xi-1)        * (eta+1)    * (zeta+1) * (zeta-1) / 4.0)     (- xi*(xi-1)     * (eta+1) * eta       * (zeta-1)     / 4.0 - xi*(xi-1)        * (eta+1) * eta       * (zeta+1)  / 4.0);
(- (xi-1)  * eta * (eta-1)       * (zeta+1) * zeta     / 4.0 - (xi+1)    * eta * (eta-1)       * (zeta+1) * zeta     / 4.0) (- (xi+1)*(xi-1) * (eta-1)       * (zeta+1) * zeta     / 4.0 - (xi+1)*(xi-1)    * eta        * (zeta+1) * zeta     / 4.0)     (- (xi+1)*(xi-1) * eta * (eta-1)       * zeta         / 4.0 - (xi+1)*(xi-1)    * eta * (eta-1)       * (zeta+1)  / 4.0);
(- xi      * (eta+1) * (eta-1)   * (zeta+1) * zeta     / 4.0 - (xi+1)    * (eta+1)* (eta-1)    * (zeta+1) * zeta     / 4.0) (- (xi+1)*xi     * (eta-1)       * (zeta+1) * zeta     / 4.0 - (xi+1)*xi        * (eta+1)    * (zeta+1) * zeta     / 4.0)     (- (xi+1)*xi     * (eta+1) * (eta-1)   * zeta         / 4.0 - (xi+1)*xi        * (eta+1)* (eta-1)    * (zeta+1)  / 4.0);
(- (xi-1)  * (eta+1) * eta       * (zeta+1) * zeta     / 4.0 - (xi+1)    * (eta+1) * eta       * (zeta+1) * zeta     / 4.0) (- (xi+1)*(xi-1) * eta           * (zeta+1) * zeta     / 4.0 - (xi+1)*(xi-1)    * (eta+1)    * (zeta+1) * zeta     / 4.0)     (- (xi+1)*(xi-1) * (eta+1) * eta       * zeta         / 4.0 - (xi+1)*(xi-1)    * (eta+1) * eta       * (zeta+1)  / 4.0);
(- (xi-1)  * (eta+1) * (eta-1)   * (zeta+1) * zeta     / 4.0 - xi        * (eta+1) * (eta-1)   * (zeta+1) * zeta     / 4.0) (- xi*(xi-1)     * (eta-1)       * (zeta+1) * zeta     / 4.0 - xi*(xi-1)        * (eta+1)    * (zeta+1) * zeta     / 4.0)     (- xi*(xi-1)     * (eta+1) * (eta-1)   * zeta         / 4.0 - xi*(xi-1)        * (eta+1) * (eta-1)   * (zeta+1)  / 4.0);

  ((xi-1)  * (eta+1)* (eta-1)    * zeta * (zeta-1)     / 2.0 + (xi+1)    * (eta+1)* (eta-1)    * zeta * (zeta-1)     / 2.0)  ((xi+1)*(xi-1)  * (eta-1)       * zeta * (zeta-1)     / 2.0 + (xi+1)*(xi-1)    * (eta+1)    * zeta * (zeta-1)     / 2.0)      ((xi+1)*(xi-1)  * (eta+1)* (eta-1)    * (zeta-1)     / 2.0 + (xi+1)*(xi-1)    * (eta+1)* (eta-1)    * zeta      / 2.0);
  ((xi-1)  * eta * (eta-1)       * (zeta+1)* (zeta-1)  / 2.0 + (xi+1)    * eta * (eta-1)       * (zeta+1)* (zeta-1)  / 2.0)  ((xi+1)*(xi-1)  * (eta-1)       * (zeta+1)* (zeta-1)  / 2.0 + (xi+1)*(xi-1)    * eta        * (zeta+1)* (zeta-1)  / 2.0)      ((xi+1)*(xi-1)  * eta * (eta-1)       * (zeta-1)     / 2.0 + (xi+1)*(xi-1)    * eta * (eta-1)       * (zeta+1)  / 2.0);
  (xi      * (eta+1)* (eta-1)    * (zeta+1)* (zeta-1)  / 2.0 + (xi+1)    * (eta+1) * (eta-1)   * (zeta+1)* (zeta-1)  / 2.0)  ((xi+1)*xi      * (eta-1)       * (zeta+1)* (zeta-1)  / 2.0 + (xi+1)*xi        * (eta+1)    * (zeta+1)* (zeta-1)  / 2.0)      ((xi+1)*xi      * (eta+1)* (eta-1)    * (zeta-1)     / 2.0 + (xi+1)*xi        * (eta+1) * (eta-1)   * (zeta+1)  / 2.0);
  ((xi-1)  * (eta+1) * eta       * (zeta+1)* (zeta-1)  / 2.0 + (xi+1)    * (eta+1) * eta       * (zeta+1)* (zeta-1)  / 2.0)  ((xi+1)*(xi-1)  *  eta          * (zeta+1)* (zeta-1)  / 2.0 + (xi+1)*(xi-1)    * (eta+1)    * (zeta+1)* (zeta-1)  / 2.0)      ((xi+1)*(xi-1)  * (eta+1) * eta       * (zeta-1)     / 2.0 + (xi+1)*(xi-1)    * (eta+1) * eta       * (zeta+1)  / 2.0);
  ((xi-1)  * (eta+1) * (eta-1)   * (zeta+1)* (zeta-1)  / 2.0 + xi        * (eta+1)* (eta-1)    * (zeta+1)* (zeta-1)  / 2.0)      (xi*(xi-1)  * (eta-1)       * (zeta+1)* (zeta-1)  / 2.0 + xi*(xi-1)        * (eta+1)    * (zeta+1)* (zeta-1)  / 2.0)       (xi*(xi-1)     * (eta+1) * (eta-1)   * (zeta-1)     / 2.0 + xi*(xi-1)        * (eta+1)* (eta-1)    * (zeta+1)  / 2.0);
  ((xi-1)  * (eta+1) * (eta-1)   * (zeta+1) * zeta     / 2.0 + (xi+1)    * (eta+1)* (eta-1)    * (zeta+1) * zeta     / 2.0)  ((xi+1)*(xi-1)  * (eta-1)       * (zeta+1) * zeta     / 2.0 + (xi+1)*(xi-1)    * (eta+1)    * (zeta+1) * zeta     / 2.0)      ((xi+1)*(xi-1)  * (eta+1) * (eta-1)   * zeta         / 2.0 + (xi+1)*(xi-1)    * (eta+1)* (eta-1)    * (zeta+1)  / 2.0);

(- (xi-1)  * (eta+1) * (eta-1)   * (zeta+1) * (zeta-1)       - (xi+1)    * (eta+1) * (eta-1)   * (zeta+1) * (zeta-1))      (- (xi+1)*(xi-1)  * (eta-1)       * (zeta+1) * (zeta-1)       - (xi+1)*(xi-1)    * (eta+1)    * (zeta+1) * (zeta-1))          (- (xi+1)*(xi-1)  * (eta+1) * (eta-1)   * (zeta-1)           - (xi+1)*(xi-1)    * (eta+1) * (eta-1)   * (zeta+1))
            ];
        
        naturalDerivatives = sortSF27(naturalDerivatives);
end

end % end function
