import numpy as np
import matplotlib.pyplot as plt 

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
        if (timeInstant%self.samplingFrequency) == 0 or self.currSample is None:
            self.currSample = self.avg + self.sigma*np.random.randn()
        return self.currSample

    def generate(self, length, events):
        ''' inputs: length -> length to be generated
                    events -> array in which each row contain information a single event
                              collumn 0 -> event length
                              collumn 1 -> event index
                              collumn 2 -> event avg
                              collumn 3 -> event sigma
                              collumn 4 -> first slope
                              collumn 5 -> peak length
                              collumn 6 -> second slope 
                    if data to be generated should be "clean" events needs to contain only zeros '''
        initialAvg = self.avg
        initialSigma = self.sigma
        dataVec = np.zeros(length)
        if np.all(events==0): #checks if events contains only zeros 
            for i in range(length):
                dataVec[i] = self.drawSample()
        else:
            auxLen = 0
            eventCounter = 0
            while auxLen < length:
                if eventCounter < events.shape[0]:
                    event = events[eventCounter]
                if auxLen == event[1]:
                    eventLength = 0
                    while np.abs(self.avg-event[2]) != 0 and eventLength < event[0]:
                        self.setAvg(self.avg+event[4])
                        dataVec[auxLen] = self.drawSample()
                        auxLen += 1
                        eventLength += 1
                    peakLength = 0
                    while peakLength < event[5] and eventLength < event[0]:
                        dataVec[auxLen] = self.drawSample()
                        auxLen += 1
                        eventLength += 1
                        peakLength += 1
                    while np.abs(self.avg-initialAvg) != 0 and eventLength < event[0]:
                        self.setAvg(self.avg+event[6])
                        dataVec[auxLen] = self.drawSample()
                        auxLen += 1
                        eventLength += 1
                    eventCounter += 1
                else: 
                    dataVec[auxLen] = self.drawSample()
                    auxLen += 1
            self.setAvg(initialAvg)
            self.setSigma(initialSigma)

        return dataVec    

if __name__ == '__main__':

    print('Ola Mundo')
    generator = DataGenerator(36, 0.05)
    events = np.zeros((2,7))
    events[0] = [10800, 6000, 39, 0.05, 0.5, 10000, -0.5]
    events[1] = [10800, 50000, 33, 0.05, -0.5, 10000, 0.5]
    data = generator.generate(60*60*24, events) # one sample per second during a day, 60 seconds, 60 minutes, 24 hours
    plt.plot(data)
    plt.show()