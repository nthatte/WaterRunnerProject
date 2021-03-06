Linearized Model
================

This folder contains a model with a fully linear plant and controller. It was obtained by linearizing the equations of motion of the robot about the desired position and the expected leg speed at the desired position. In this model, unlike the real water runner, the legs do not have phase relationships. 

simpleSys.m
-----------

This file contains setup parameters and options and should be run before the simulation is started. There are several sections of parameters in this file:

1. Initial and desired conditions and disturbance inputs.
2. Robot Parameters
	1. leg link lengths and frame size
	2. Robot mass is calculated from geometry and density of legs and assumed mass of the body.
3. Water Model Parameters
	1. foot area
	2. foot area folding ratio
	3. drag coefficient
	4. gravity
4. Controller Parameters
	1. Calculates requrired steady state frequncy from desired height. Input dynamics are linearized about this frequncy. 
	2. Computes Taylor series terms to produce linear model for controller. Also, at the end of this section is
	  the coupling gain "Cgain" for the nullspacep projection calculation in the inverse dynamics controller.
	3. PID gains tuned via Ziegler Nichols Method
	4. CPG parameters including phase lags between legs and cpg gain

genForceFunctions.m
-------------------

Uses the symbolic equation for the average force generated by a foot to generate m file functions for the average force and its derivatives with respect to height, y; roll, theta; and control inputs, w1 and w2. The force function and its first derivatives are used to linearize the system. 

findSSinput.m
--------------

Solve force function for steady state leg frequency for a given desired height. Steady state input will create an average force equal to the weight. This function is used by simParam.m to find the steady state input that will achieve the desired height.
