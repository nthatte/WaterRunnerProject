function F_w1 = Force_w1(y,theta,w1,w2,b,k,A,w,alpha)
%FORCE_W1
%    F_W1 = FORCE_W1(Y,THETA,W1,W2,B,K,A,W,ALPHA)

%    This function was generated by the Symbolic Math Toolbox version 5.9.
%    02-May-2013 21:12:11

t2 = sin(theta);
t3 = t2.*w;
t4 = A+t3-y;
t5 = 1.0./pi;
t6 = 1.0./A;
t7 = t4.*t6;
t8 = acos(t7);
t9 = pi-t8;
t10 = t4.*t9;
t11 = t4.^2;
t12 = A.^2;
t13 = -t11+t12;
t14 = sqrt(t13);
t15 = t10+t14;
t16 = w1+w2;
t17 = 1.0./t16;
t18 = t9.*t12;
t19 = t4.*t14;
t20 = t18+t19;
t21 = w1-alpha.*w2;
F_w1 = real(k.*t5.*t15.*1.0./w1.^2.*(w2+alpha.*w1).*(-1.0./2.0)+(alpha.*k.*t5.*t15.*(1.0./2.0))./w1+b.*t5.*t17.*t20.*t21.*w2.*(1.0./2.0)+b.*t5.*t17.*t20.*w1.*w2.*(1.0./2.0)-b.*t5.*1.0./t16.^2.*t20.*t21.*w1.*w2.*(1.0./2.0));
