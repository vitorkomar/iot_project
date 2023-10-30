from mqtt_subscriber import *
import numpy as np 
import json
import time
import pprint
import requests

""" Class that as the name says will handle the data gathered by the sensors. 
    It basically is a mqtt subscriber, that is subscribed to ONLY a specific device. 
    A device is the wearable that will keep track of the elderly status, can be seen as the sensors. 
    At each publication on the topic that it is subscribed it will store the new value in its database,
        if the amount of data surpass a threshold it removes the oldest sample and store the new one 
        (we need to define the threshold based on how much data we want to store, one month of data, two weeks...)
    When requested it provides statics of the stored data """

class DataHandler(mqttSubscriber): 
    def __init__(self, catalogURL, deviceID):
        self.catalogURL = catalogURL
        self.deviceID = deviceID
        data = requests.get(self.catalogURL+'/subscriber')
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = 1883 ## hardcoded?
        mqttSubscriber.__init__(self, str(self.deviceID), self.broker, self.port)
        self.topic = data['baseTopic']+'/'+str(self.deviceID[-1])
        self.client.on_message = self.on_message_handler
        self.collected = {'temperature': [],
                          'accelerometer':[],
                          'glucose':[],
                          'systole':[],
                          'diastole':[],
                          'saturation':[]}

    def updateSettings(self):
        """update local data handler settings and store them in a json file"""
        conf = json.load(open("subscriber\settings.json"))
        conf['catalogURL'] = self.catalogURL
        conf['brokerAddress'] = self.broker
        conf['port'] = self.port
        conf['topic'] = self.topic
        conf['id'] = self.deviceID
        with open("subscriber\settings.json", "w") as file:
            json.dump(conf, file, indent = 4)

    def runAnalysys(self):
        """run the data handler"""
        self.client.connect(self.broker, self.port)
        self.subscribe(self.topic)
        self.client.loop_forever()

    def storeValue(self, sensor, value):
        """stores values in local database""" 
        if len(self.collected[sensor]) > 4: #adjust acordingly to how long data is stored (week?, month?)
            self.collected[sensor].pop(0)
        self.collected[sensor].append(value)

    def on_message_handler(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received
            will be called everytime a message is published on the subscribed topic"""
        data = json.loads(msg.payload)
        temp = next((item for item in data["e"] if item["n"] == "temperature"), None)
        acc = next((item for item in data["e"] if item["n"] == "accelerometer"), None)
        glu = next((item for item in data["e"] if item["n"] == "glucose"), None)
        sys = next((item for item in data["e"] if item["n"] == "systole"), None)
        dia = next((item for item in data["e"] if item["n"] == "diastole"), None)
        sat = next((item for item in data["e"] if item["n"] == "saturation"), None)
        time = next((item for item in data["e"] if item["n"] == "time"), None)

        self.storeValue('temperature',temp['v'])
        self.storeValue('accelerometer',acc['v'])
        self.storeValue('glucose',glu['v'])
        self.storeValue('systole',sys['v'])
        self.storeValue('diastole',dia['v'])
        self.storeValue('saturation',sat['v'])

        print('TimeStamp:', time['v'])
        pprint.pprint(self.collected)
        print()

    """ From now on -> Functions that provides statics"""
    def computeMin(self, sensor, timeInterval):
        #fix time interval to be user friendly
        #users are stupid 
        return np.min(self.collected[sensor][-timeInterval:])

    def computeMax(self, sensor, timeInterval):
        #fix time interval to be user friendly
        #users are stupid 
        return np.max(self.collected[sensor][-timeInterval:])

    def computeMean(self, sensor, timeInterval):
        #fix time interval to be user friendly
        #users are stupid 
        return np.mean(self.collected[sensor][-timeInterval:])

    def computeStd(self, sensor, timeInterval):
        #fix time interval to be user friendly
        #users are stupid 
        return np.std(self.collected[sensor][-timeInterval:])
    
    def computeMovingAvg(self):
        pass