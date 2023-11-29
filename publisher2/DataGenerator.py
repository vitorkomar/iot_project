import numpy as np
import matplotlib.pyplot as plt 

"""Class that simulates the sensors 
    for now ignore generate method 
    consider only methods up drawSample"""

class DataGenerator():

    def __init__(self, average, sigma, samplingFrequency):
        self.avg = average
        self.sigma = sigma
        self.samplingFrequency = samplingFrequency
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
        if (timeInstant%self.samplingFrequency) == 0 or self.currSample is None:
            self.currSample = self.avg + self.sigma*np.random.randn()
        return self.currSample
