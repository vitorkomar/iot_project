from mqtt_subscriber import *
import numpy as np 
import json
import time
import pprint

class DataHandler(mqttSubscriber): 
    def __init__(self, clientId, broker, port):
        mqttSubscriber.__init__(self, clientId, broker, port)
        self.client.on_message = self.on_message_handler
        self.collected = {'temperature': [],
                          'accelerometer':[],
                          'glucose':[],
                          'systole':[],
                          'diastole':[],
                          'saturation':[]}

    def storeValue(self, sensor, value): 
        if len(self.collected[sensor]) > 4: #adjust acordingly to how long data is stored (week?, month?)
            self.collected[sensor].pop(0)
        self.collected[sensor].append(value)

    def on_message_handler(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received"""
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

        #print('TimeStamp:', time['v'])
        #pprint.pprint(self.collected)
        #print()

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
    