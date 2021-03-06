import numpy as np

class Leg:

	def __init__(self,initAngle,initPos,legParams,worldParams,Foot):
		'''Arguments:
		initAngle: vector containing initial angle, angular speed, angular accel of leg input shaft
		initPos:   matrix whos rows are x,y initial position, speed, accel of leg input shaft
		legParams: dict containing link lengths vector and plus/minus 1 const for kinematics solution
		Foot: this legs foot'''

		self.L = legParams['linkLengths']
		self.pm = legParams['pm']

		#Vectors that hold joint angles, ang speeds, and ang accel
		self.theta = np.zeros(4)
		self.theta = self.calcAngles(0., initAngle[0])
		self.omega = np.zeros(4)
		self.omega = self.calcAngSpeeds(0, initAngle[1])
		self.alpha = np.zeros(4)
		self.alpha = self.calcAngAccels(0, initAngle[2])
		
		#Matricies that hold x, y position, speed, accel of joints. Rows are O, A, B, C, F respectively.
		self.initPos = initPos
		self.jointPos = np.zeros((5,2))
		self.jointPos = self.calcPos(initPos[0,:])
		self.jointSpeed = np.zeros((5,2))
		self.jointSpeed = self.calcSpeed(initPos[1,:])
		self.jointAccel = np.zeros((5,2))
		self.jointAccel = self.calcAccel(initPos[2,:])
		
		#Vector that holds all joint loads and vector that holds loads transmitted to robot
		self.jointLoad = np.zeros(9)
		self.robotLoad = np.zeros(5) #[Fx0, Fy0, Fx3, Fy3, T]
		self.Foot = Foot

	def update(self, angle0, angle1, pos, timestep):
		'''Updates state of leg by calling methods to calculate joint angular position, speed, and accel, 
		and cartesian posiiton, speed and accels. Updates force/torque on leg.'''
		
		#update angular state
		self.calcAngles(angle0[0], angle1[0])
		self.calcAngSpeeds(angle0[1], angle1[1])
		self.calcAngAccels(angle0[2], angle1[2])

		#update cartesian state
		self.calcPos(pos[0,:])
		self.calcSpeed(pos[1,:])
		self.calcAccel(pos[2,:])
		
		#update Foot
		self.Foot.update([self.theta[2], self.omega[2], self.alpha[2]],[self.jointPos[4,:], self.jointSpeed[4,:], self.jointAccel[4,:]], timestep)
		
		#update Force/Torque
		self.calcForceTorque()

	def calcAngles(self, theta0, theta1):
		'''Takes input link angle, performs 4 bar kinematics calcs and returns angles of all links'''
		
		self.theta[0] = theta0
		self.theta[1] = theta1

		Alpha = 2.*self.L[0]*self.L[3] * np.cos(self.theta[0]) - 2.*self.L[1]*self.L[3]*np.cos(self.theta[1])
		Beta  = 2.*self.L[0]*self.L[3] * np.sin(self.theta[0]) - 2.*self.L[1]*self.L[3]*np.sin(self.theta[1])
		Gamma = (self.L[0]**2 + self.L[1]**2 + self.L[3]**2 - self.L[2]**2 - 2.*self.L[0]*self.L[1]*np.cos(self.theta[0]) * np.cos(self.theta[1])
																		   - 2.*self.L[0]*self.L[1]*np.sin(self.theta[0]) * np.sin(self.theta[1]))
		Delta = np.arctan2(Beta,Alpha)

		self.theta[3] = Delta + self.pm*np.arccos(-1*Gamma/np.sqrt(Alpha**2 + Beta**2))
		self.theta[2] = (np.arctan2(self.L[0]*np.sin(self.theta[0]) + self.L[3]*np.sin(self.theta[3]) - self.L[1]*np.sin(self.theta[1]),
							self.L[0]*np.cos(self.theta[0]) + self.L[3]*np.cos(self.theta[3]) - self.L[1]*np.cos(self.theta[1])))
		return self.theta

	def calcAngSpeeds(self, omega0, omega1):
		'''Solves system of equations and returns angular speeds given input link speed omega1'''
		self.omega[1] = omega1
		self.omega[0] = omega0

		A = np.array([[-1*self.L[3]*np.sin(self.theta[3]),    self.L[2]*np.sin(self.theta[2])],
					     [self.L[3]*np.cos(self.theta[3]), -1*self.L[2]*np.cos(self.theta[2])]])
		b = ( np.array([[-1*self.L[1]*np.sin(self.theta[1])],
						   [self.L[1]*np.cos(self.theta[1])]]) * omega1
			+ np.array([[-1*self.L[0]*np.sin(self.theta[0])],
						   [self.L[0]*np.cos(self.theta[0])]]) * omega0)
		omega32 = np.linalg.solve(A,b)
		self.omega[3] = omega32[0]
		self.omega[2] = omega32[1]

		return self.omega
	
	def calcAngAccels(self, alpha0, alpha1):
		'''Solves system of equations and returns angular accels given input link accel alpha1'''

		A  = np.array([[-1*self.L[3]*np.sin(self.theta[3]),    self.L[2]*np.sin(self.theta[2])],
					      [self.L[3]*np.cos(self.theta[3]), -1*self.L[2]*np.cos(self.theta[2])]])
		
		b0 = np.array([[   self.L[0]*np.sin(self.theta[0])],
					   [-1*self.L[0]*np.cos(self.theta[0])]])
		b1 = np.array([[-1*self.L[1]*np.sin(self.theta[1])],
					   [   self.L[1]*np.cos(self.theta[1])]])
		b2 = np.array([[-1*self.L[1]*np.cos(self.theta[1])],
					   [-1*self.L[1]*np.sin(self.theta[1])]])
		b3 = np.array([[-1*self.L[2]*np.cos(self.theta[2])],
					   [-1*self.L[2]*np.sin(self.theta[2])]])
		b4 = np.array([[   self.L[3]*np.cos(self.theta[3])],
					   [   self.L[3]*np.sin(self.theta[3])]])
		b5 = np.array([[   self.L[0]*np.cos(self.theta[0])],
					   [   self.L[0]*np.sin(self.theta[0])]])
		b = b0*alpha0 + b1*alpha1 + b2*self.omega[1]**2 + b3*self.omega[2]**2 + b4*self.omega[3]**2 + b5*self.omega[0]**2

		alpha32 = np.linalg.solve(A,b)
		self.alpha[3] = alpha32[0]
		self.alpha[2] = alpha32[1]
		self.alpha[1] = alpha1
		self.alpha[0] = alpha0
		return self.alpha
	
	def calcPos(self, Opos):
		'''Returns x,y coordinates of Joints O,A,B,C and Foot Connection of four bar given position of point O'''
		self.jointPos[0,:] =  Opos
		self.jointPos[1,:] =  Opos + np.array([self.L[1]*np.cos(self.theta[1]), self.L[1]*np.sin(self.theta[1])]) #A
		self.jointPos[2,:] = (Opos + np.array([self.L[0]*np.cos(self.theta[0]), self.L[0]*np.sin(self.theta[0])]) 
							 	   + np.array([self.L[3]*np.cos(self.theta[3]), self.L[3]*np.sin(self.theta[3])])) #B
		self.jointPos[3,:] =  Opos + np.array([self.L[0]*np.cos(self.theta[0]), self.L[0]*np.sin(self.theta[0])]) #C
		self.jointPos[4,:] = (Opos + np.array([self.L[1]*np.cos(self.theta[1]), self.L[1]*np.sin(self.theta[1])])
						           + np.array([self.L[4]*np.cos(self.theta[2] + np.pi), self.L[4]*np.sin(self.theta[2] + np.pi)]))   #F
		return self.jointPos
	
	def calcSpeed(self, Ospeed):
		'''Returns x,y speeds of Joints O,A,B,C and Foot Connection of four bar given speed of point O'''
		self.jointSpeed[0,:] = Ospeed
		self.jointSpeed[1,:] = Ospeed + np.array([-1*self.L[1] * np.sin(self.theta[1]), self.L[1] * np.cos(self.theta[1])])*self.omega[1] #A
		self.jointSpeed[2,:] = Ospeed + np.array([-1*self.L[0] * np.sin(self.theta[0]), self.L[0] * np.cos(self.theta[0])])*self.omega[0]+ np.array([-1*self.L[3] * np.sin(self.theta[3]), self.L[3] * np.cos(self.theta[3])])*self.omega[3] #B
		self.jointSpeed[3,:] = Ospeed + np.array([-1*self.L[0] * np.sin(self.theta[0]), self.L[0] * np.cos(self.theta[0])])*self.omega[0]#C
		self.jointSpeed[4,:] = Ospeed + (np.array([-1*self.L[1]*np.sin(self.theta[1]),  self.L[1]*np.cos(self.theta[1])		  ])*self.omega[1]
									  +  np.array([-1*self.L[4]*np.sin(self.theta[2] + np.pi), self.L[4]*np.cos(self.theta[2] + np.pi)])*self.omega[2]) #F
		return self.jointSpeed

	def calcAccel(self, Oaccel):
		'''Returns x,y accel of Joints O,A,B,C and Foot Connection of four bar given accel of point O'''
		self.jointAccel[0,:] = Oaccel
		self.jointAccel[1,:] = Oaccel + (np.array([-1*self.L[1]*np.cos(self.theta[1]), -1*self.L[1]*np.sin(self.theta[1])])*self.omega[1]**2
									  +  np.array([-1*self.L[1]*np.sin(self.theta[1]),    self.L[1]*np.cos(self.theta[1])])*self.alpha[1])   #A
		self.jointAccel[2,:] = Oaccel + (np.array([-1*self.L[0]*np.cos(self.theta[0]), -1*self.L[0]*np.sin(self.theta[0])])*self.omega[0]**2
									  +  np.array([-1*self.L[0]*np.sin(self.theta[0]),    self.L[0]*np.cos(self.theta[0])])*self.alpha[0]
							          +  np.array([-1*self.L[3]*np.cos(self.theta[3]), -1*self.L[3]*np.sin(self.theta[3])])*self.omega[3]**2
									  +  np.array([-1*self.L[3]*np.sin(self.theta[3]),    self.L[3]*np.cos(self.theta[3])])*self.alpha[3])	 #B
		self.jointAccel[3,:] = Oaccel + (np.array([-1*self.L[0]*np.cos(self.theta[0]), -1*self.L[0]*np.sin(self.theta[0])])*self.omega[0]**2
									  +  np.array([-1*self.L[0]*np.sin(self.theta[0]),    self.L[0]*np.cos(self.theta[0])])*self.alpha[0]) #C
		self.jointAccel[4,:] = Oaccel + (self.jointAccel[1,:] 
									  + np.array([-1*self.L[4]*np.cos(self.theta[2] + np.pi), -1*self.L[4]*np.sin(self.theta[2] + np.pi)])*self.omega[2]**2
									  + np.array([-1*self.L[4]*np.sin(self.theta[2] + np.pi),    self.L[4]*np.cos(self.theta[2] + np.pi)])*self.alpha[2]) #F
		return self.jointAccel

	def calcForceTorque(self):
		'''Solves system of equations, and returns vector containing joint load
		and motor shaft torque using ground reaction force force, and moment
		x = [Fr1x Fr1y Fr3x Fr3y F1x F1y F3x F3y T]'''

		A = np.array([[0, 0, 0, 0,  1,								   0,							       1,												0,				                              0],
					  [0, 0, 0, 0,  0,								   1,							       0,												1,											  0],		
					  [0, 0, 0, 0, -1*self.L[4]*np.sin(self.theta[2]), self.L[4]*np.cos(self.theta[2]),   -1*(self.L[2] + self.L[4])*np.sin(self.theta[2]), (self.L[2]+ self.L[4])*np.cos(self.theta[2]), 0],
					  [1, 0, 0, 0, -1,								   0,							       0,									            0,											  0],
					  [0, 1, 0, 0,  0,								   -1,							       0,												0,											  0],
					  [0, 0, 0, 0,  self.L[1]*np.sin(self.theta[1]),  -1.*self.L[1]*np.cos(self.theta[1]), 0,												0,											  1],
					  [0, 0, 1, 0,  0,								   0,							      -1,											    0,				                              0],
					  [0, 0, 0, 1,  0,								   0,						 	       0,											   -1,				                              0],
					  [0, 0, 0, 0,  0,								   0,						 	       self.L[3]*np.sin(self.theta[3]),				   -1*self.L[3]*np.cos(self.theta[3]),            0]]
					  , dtype = float)
		
		b = np.array([[-1*self.Foot.loadx],
					  [-1*self.Foot.loady],
					  [-1*self.Foot.moment], 
					  [0.], [0.], [0.], [0.], [0.], [0.]])
		self.jointLoad = np.linalg.solve(A,b).reshape((1,9))
		'''
		self.robotLoad[0] = -1.*self.jointLoad[0,0] - self.jointLoad[0,2]
		self.robotLoad[1] = -1.*self.jointLoad[0,1] - self.jointLoad[0,3]
		self.robotLoad[2] = -1.*self.jointLoad[0,8]
		'''
		self.robotLoad[0] = -1.*self.jointLoad[0,0]
		self.robotLoad[1] = -1.*self.jointLoad[0,1] 
		self.robotLoad[2] = -1.*self.jointLoad[0,2]
		self.robotLoad[3] = -1.*self.jointLoad[0,3]
		self.robotLoad[4] = -1.*self.jointLoad[0,8]
		return self.jointLoad
