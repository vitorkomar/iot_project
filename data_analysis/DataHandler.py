from mqtt_subscriber import *
import numpy as np 
import json
import time
import pprint
import requests

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
        conf = json.load(open("subscriber\settings.json"))
        conf['catalogURL'] = self.catalogURL
        conf['brokerAddress'] = self.broker
        conf['port'] = self.port
        conf['topic'] = self.topic
        conf['id'] = self.deviceID
        with open("subscriber\settings.json", "w") as file:
            json.dump(conf, file, indent = 4)

    def runAnalysys(self):
        self.client.connect(self.broker, self.port)
        self.subscribe(self.topic)
        self.client.loop_forever()

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

        print('TimeStamp:', time['v'])
        pprint.pprint(self.collected)
        print()

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