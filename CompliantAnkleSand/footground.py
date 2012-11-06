import numpy as np

class Foot():
	
	def __init__(self,initAngle,initPos,footParams,worldParams,robotMass):
		'''Arguments:
		initAngle: vector containing initial angle, angular speed, angular accel of foot
		initPos:   matrix whos rows are x,y initial position, speed, accel of foot attach pt'''

		self.staticFrictionCoeff = footParams['staticFrictionCoeff']
		self.kinFrictionCoeff = footParams['kinFrictionCoeff']
		
		self.length = footParams['length']
		self.E = footParams['E']*10**6
		self.PRBMK = footParams['PRBMK']
		self.gamma = footParams['gamma']
		self.inertia = (footParams['width']*footParams['height']**3)/12.
		self.inertiaEff = 0.2708*self.inertia
		self.k = (self.gamma*self.PRBMK*self.E*self.inertia/self.length)*np.pi/180
		self.b = footParams['damping']
		
		self.gravity = worldParams['gravity']
		self.timeStep = worldParams['timeStep']
		self.robotMass = robotMass

		#initialize angle position, speed, accel of foot
		self.theta = initAngle[0]
		self.omega = initAngle[1]
		self.alpha = initAngle[2]
		self.thetaPRBM = 0.
		self.omegaPRBM = 0.
		self.alphaPRBM = 0.

		#history for adam's bashforth
		self.alphaPRBM1 = None
		self.alphaPRBM2 = None
		self.alphaPRBM3 = None
		self.omegaPRBM1 = None
		self.omegaPRBM2 = None
		self.omegaPRBM3 = None

		#initialize cartesian position, speed, accel of foot
		self.pos = np.zeros((3,2), dtype = float) #attatch point, psuedo-torsion spring loc, bottom
		self.pos[0,:] = initPos[0,:] 
		self.pos[1,:] = self.pos[0,:] - (1. - self.gamma)*self.length*np.array([np.cos(self.theta), np.sin(self.theta)])
		self.pos[2,:] = self.pos[1,:] - self.gamma*self.length*np.array([np.cos(self.theta), np.sin(self.theta)])
		self.speed = initPos[1,:]
		self.accel = initPos[2,:]

		#initalize forces
		self.loadx = 0.
		self.loady = 0.
		self.moment = 0.
		self.bendingMoment = 0.

	def update(self, angle, pos):
		'''Updates state of foot by calling methods to calculate joint angular position, speed, and accel, 
		and cartesian posiiton, speed and accels. Updates force/torque on leg.'''

		self.calcAngAccel(angle[2])
		self.calcAngSpeed(angle[1])
		self.calcAngPos(angle[0])
		self.calcPos(pos[0])
		self.calcSpeed(pos[1])
		self.calcAccel(pos[2])
		self.calcForce()

	def calcAngAccel(self, alpha):
		#update history use euler's for first 4 then adam's bashforth
		self.alphaPRBM3 = self.alphaPRBM2
		self.alphaPRBM2 = self.alphaPRBM1
		self.alphaPRBM1 = self.alphaPRBM

		self.alpha = alpha
		self.alphaPRBM = (-1*self.b*self.omegaPRBM - self.k*self.thetaPRBM + self.bendingMoment)/self.inertiaEff

	def calcAngSpeed(self, omega):
		self.omega = omega
		
		#update history use euler's for first 4 then adam's bashforth
		self.omegaPRBM3 = self.omegaPRBM2
		self.omegaPRBM2 = self.omegaPRBM1
		self.omegaPRBM1 = self.omegaPRBM

		if self.omegaPRBM3 == None:
			self.omegaPRBM += self.alphaPRBM*self.timeStep
		else:
			self.omegaPRBM += (self.timeStep/24.) * (55.*self.alphaPRBM - 59.*self.alphaPRBM1 + 37.*self.alphaPRBM2 - 9.*self.alphaPRBM3)	
	
	def calcAngPos(self, theta):
		self.theta = theta
		if self.omegaPRBM3 == None:
			self.thetaPRBM += self.omegaPRBM*self.timeStep + 0.5*self.alphaPRBM*self.timeStep**2
		else:
			self.thetaPRBM += (self.timeStep/24.) * (55.*self.omegaPRBM - 59.*self.omegaPRBM1 + 37.*self.omegaPRBM2 - 9.*self.omegaPRBM3)
	
	def calcPos(self, pos):
		self.pos[0,:] = pos
		self.pos[1,:] = self.pos[0,:] - (1. - self.gamma) * self.length * np.array([np.cos(self.theta), np.sin(self.theta)]) 
		self.pos[2,:] = self.pos[1,:] - self.gamma * self.length * np.array([np.cos(self.theta - self.thetaPRBM), np.sin(self.theta - self.thetaPRBM)])

	def calcSpeed(self, speed):
		self.speed = speed

	def calcAccel(self, accel):
		self.accel = accel

	def calcForce(self):
		'''Returns Ground Reaction Force and Moment'''
		yp = -1.*self.pos[2,1]
		ypdot = -1.*self.speed[1]
		if yp > 0:
			self.loady = 0.25e9 * (np.abs(yp)**3.)*(1.- ypdot)
			if np.abs(self.robotMass*self.accel[0]) < self.staticFrictionCoeff*self.loady:
				self.loadx = self.robotMass*self.accel[0]
			else:
				self.loadx = -1*self.kinFrictionCoeff*np.abs(self.loady)*np.sign(self.speed[0])
			self.moment = (self.loady*(self.pos[2,0]- self.pos[0,0])) - self.loadx*(self.pos[2,1] - self.pos[1,1])
			self.bendingMoment =  (-1*self.loady*(self.pos[2,0]- self.pos[1,0]) + self.loadx*(self.pos[2,1] - self.pos[1,1]) 
							        + self.loady*(self.pos[0,0]- self.pos[1,0]) - self.loadx*(self.pos[0,1] - self.pos[1,1]))
			print 'alphaPRBM: ', self.alphaPRBM,  'omegaPRBM: ', self.omegaPRBM, 'thetaPRBM: ', self.thetaPRBM
			print 'bendingMoment: ', self.bendingMoment, 'Fy: ',self.loady, 'Fx: ', self.loadx, 'yp: ', yp, 'ypdot: ', ypdot
			print 'k: ', self.k, 'b: ', self.b, 'I*: ',self.inertiaEff
		else:
			self.loady = 0.
			self.loadx = 0.
			self.moment = 0.
			self.bendingMoment = 0.

		


