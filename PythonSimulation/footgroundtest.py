import numpy as np

class Foot():
	
	def __init__(self,initAngle,initPos,footParams,worldParams,robotMass):
		'''Arguments:
		initAngle: vector containing initial angle, angular speed, angular accel of foot
		initPos:   matrix whos rows are x,y initial position, speed, accel of foot attach pt'''

		self.staticFrictionCoeff = footParams['staticFrictionCoeff']
		self.kinFrictionCoeff = footParams['kinFrictionCoeff']
		
		self.length = footParams['length']
		self.E = footParams['E']*10.**6.
		self.PRBMK = footParams['PRBMK']
		self.gamma = footParams['gamma']
		self.inertia = (footParams['width']*footParams['thickness']**3.)/12.
		self.inertiaEff = .3e-6
		#self.k = (self.gamma*self.PRBMK*self.E*self.inertia/self.length)*180./np.pi
		self.k = footParams['k']
		self.b = footParams['damping']*10.**-5.

		self.gravity = worldParams['gravity']
		self.timeStepFine = worldParams['timeStepFine']
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

		self.speed = np.zeros((3,2), dtype = float)
		self.speed[0,:] = initPos[1,:]
		self.speed[1,:] = initPos[1,:]
		self.speed[2,:] = initPos[1,:]
		
		self.accel = initPos[2,:]

		#initalize forces
		self.loadx = 0.
		self.loady = 0.
		self.moment = 0.
		self.bendingMoment = 0.
		
		self.loadxfine = 0.
		self.loadyfine = 0.
		self.momentfine = 0.
		self.bendingMomentfine = 0.

	def update(self, angle, pos, timeStep):
		'''Updates state of foot by calling methods to calculate joint angular position, speed, and accel, 
		and cartesian posiiton, speed and accels. Updates force/torque on leg.'''
		totalLoadx = 0.
		totalLoady = 0.
		totalMoment = 0.
		self.timeStep = self.timeStepFine
		timeStepRatio = timeStep/self.timeStepFine

		for i in np.arange(timeStepRatio):
			#print i, timeStepRatio
			fineLoadx, fineLoady, fineMoment = self.calcForce()
			totalLoadx += fineLoadx
			totalLoady += fineLoady
			totalMoment += fineMoment
			self.calcAngAccel(angle[2])
			self.calcAngSpeed(angle[1])
			self.calcAngPos(angle[0])
			self.calcPos(pos[0])
			self.calcSpeed(pos[1])
			self.calcAccel(pos[2])
	
		self.loadx = totalLoadx/timeStepRatio
		self.loady = totalLoady/timeStepRatio
		self.moment = totalMoment/timeStepRatio


	def calcAngAccel(self, alpha):
		#update history use euler's for first 4 then adam's bashforth
		self.alphaPRBM3 = self.alphaPRBM2
		self.alphaPRBM2 = self.alphaPRBM1
		self.alphaPRBM1 = self.alphaPRBM
	
		self.alpha = alpha
		self.alphaPRBM = (-1*self.b*self.omegaPRBM - self.k*self.thetaPRBM + self.bendingMomentfine)/self.inertiaEff
		#print 'damp Force: ', -1*self.b*self.omegaPRBM, 'spring force: ', -1*self.k*self.thetaPRBM, 'bending moment: ', self.bendingMoment

	def calcAngSpeed(self, omega):
		self.omega = omega
		
		#update history use euler's for first 4 then adam's bashforth
		self.omegaPRBM3 = self.omegaPRBM2
		self.omegaPRBM2 = self.omegaPRBM1
		self.omegaPRBM1 = self.omegaPRBM

		if self.alphaPRBM3 == None:
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
		self.speed[0,:] = speed
		self.speed[1,:] = self.speed[0,:] - (1 - self.gamma) * self.length * np.array([-1* np.sin(self.theta), np.cos(self.theta)]) * self.omega
		self.speed[2,:] = self.speed[1,:] + self.gamma * self.length *np.array([-1 * np.sin(self.theta + np.pi - self.thetaPRBM), np.cos(self.theta + np.pi - self.thetaPRBM)])*(self.omega - self.omegaPRBM)

	def calcAccel(self, accel):
		self.accel = accel

	def calcForce(self):
		'''Returns Ground Reaction Force and Moment'''
		yp = -1.*self.pos[2,1]
		ypdot = -1.*self.speed[2,1]

		if yp > 0:
			if ypdot > 5:
				ypdot = 5.
			elif ypdot < -2:
				ypdot = -2.
			
			if ypdot >=0:
				self.loadyfine = 0.25e9 * (np.abs(yp)**3.)*(1.- 0.1*ypdot)
			else:
				self.loadyfine = 0.25e9 * (np.abs(yp)**3.)*(1.+ ypdot)
			
			#self.speed = np.zeros((3,2))
			if np.abs(self.robotMass*self.accel[0]) < self.staticFrictionCoeff*self.loadyfine:
				self.loadxfine = -1*self.robotMass*self.accel[0]
			else:
				self.loadxfine = -1*self.kinFrictionCoeff*np.abs(self.loadyfine)*np.sign(self.speed[2,0])
			self.momentfine = -1.*self.loadyfine*(self.pos[2,0]- self.pos[0,0]) + self.loadxfine*(self.pos[2,1] - self.pos[1,1])
			self.bendingMomentfine = self.momentfine - self.loadyfine*(self.pos[0,0]- self.pos[1,0]) + self.loadxfine*(self.pos[0,1] - self.pos[1,1])

		else:
			self.loadyfine = 0.
			self.loadxfine = 0.
			self.momentfine = 0.
			self.bendingMomentfine = 0.
		
		if yp > -0.02 and False:
			print 'alphaPRBM: ', self.alphaPRBM,  'omegaPRBM: ', self.omegaPRBM, 'thetaPRBM: ', self.thetaPRBM
			print 'Fy: ',self.loadyfine, 'Fx: ', self.loadxfine, 'y: ',  self.pos[2,1], 'ydot: ', self.speed[2,1]
			print 'damping: ', -1*self.b*self.omegaPRBM, 'spring: ',  -1* self.k*self.thetaPRBM, 'bending :', self.bendingMoment
			print 'k: ', self.k, 'b: ', self.b, 'I*: ',self.inertiaEff
		return self.loadxfine, self.loadyfine, self.momentfine
