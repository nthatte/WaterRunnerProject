function F_th = Force_th(y,theta,phi,w1,w2,b,k,A,l,w,alpha)
%FORCE_TH
%    F_TH = FORCE_TH(Y,THETA,PHI,W1,W2,B,K,A,L,W,ALPHA)

%    This function was generated by the Symbolic Math Toolbox version 5.9.
%    02-May-2013 13:49:20

t2 = cos(theta);
t3 = sin(phi);
t4 = sin(theta);
t5 = t4.*w;
t7 = l.*t3;
t6 = A+t5-t7-y;
t8 = 1.0./A;
t9 = t6.^2;
t10 = 1.0./pi;
t11 = A.^2;
t12 = -t9+t11;
t13 = 1.0./A.^2;
t14 = -t9.*t13+1.0;
t15 = 1.0./sqrt(t14);
t16 = 1.0./sqrt(t12);
F_th = (k.*t10.*(w2+alpha.*w1).*(t2.*w.*(pi-acos(t6.*t8))-t2.*t6.*t16.*w+t2.*t6.*t8.*t15.*w).*(1.0./2.0))./w1+(b.*t10.*w1.*w2.*(w1-alpha.*w2).*(t2.*sqrt(t12).*w-t2.*t9.*t16.*w+A.*t2.*t15.*w).*(1.0./2.0))./(w1+w2);
