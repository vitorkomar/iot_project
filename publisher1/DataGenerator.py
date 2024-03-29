import numpy as np
import matplotlib.pyplot as plt 

"""Class that simulates the sensors 
    for now ignore generate method 
    consider only methods up drawSample"""

class DataGenerator():

    def __init__(self, average, sigma, samplingFrequency, n, u):
        self.avg = average
        self.sigma = sigma
        self.samplingFrequency = samplingFrequency
        self.n = n
        self.u = u
        self.currSample = None
    
    def setAvg(self, average):
        self.avg = average

    def getAvg(self):
        return self.avg

    def setSigma(self, sigma):
        self.sigma = sigma

    def getSigma(self):
        return self.sigma

    def drawSample(self, timeInstant):
        """ draw a sample every timeInstant 
            timeInstant can be seen as sampling frequency
            samples are drawn from a normal distribution with mean self.avg and std self.sigma"""
        #if (timeInstant%self.samplingFrequency) == 0 or self.currSample is None:
            #self.currSample = self.avg + self.sigma*np.random.randn()
        self.currSample = self.avg + self.sigma*np.random.randn()
        return self.currSample

class AccDataGenerator(DataGenerator):

    def __init__(self, average, sigma, samplingFrequency, n, u):
        super().__init__(average, sigma, samplingFrequency, n, u)

    def drawSample(self, timeInstant):
        self.currSample = 10.0*np.random.binomial(1, 0.5)
        return self.currSample