import numpy as np

class DataGenerator():
    """Class that simulates a sensors 
    """
    def __init__(self, average, sigma, samplingFrequency, n, u):
        self.avg = average
        self.sigma = sigma
        self.samplingFrequency = samplingFrequency
        self.n = n
        self.u = u
        self.currSample = None

    def drawSample(self):
        """ Draw a sample from a normal distribution with mean self.avg and std self.sigma
        """
        self.currSample = self.avg + self.sigma*np.random.randn()
        return self.currSample

class AccDataGenerator(DataGenerator):
    """ Class that simulates an accelerometer sensor
    """
    def __init__(self, average, sigma, samplingFrequency, n, u):
        super().__init__(average, sigma, samplingFrequency, n, u)

    def drawSample(self):
        """ Draw a sample from a Bernoulli distribution with succes rate 0.05
        """
        self.currSample = 10.0*np.random.binomial(1, 0.05)
        return self.currSample
