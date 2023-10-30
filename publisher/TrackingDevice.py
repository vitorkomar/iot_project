from mqtt_client import *
import time
import json
from DataGenerator import *
import random
import requests

""" Class that simulates the sensors that will gather info about patients 
    It basically is a mqtt publisher, that publishes ONLY on a specific topic. 
    It publishes a new message everytime data is acquired, acquiring data depends on the sampling frequency
    At each publication it will publish the new data gathered by a sensor and if a sensor did not record anything 
        on that time instant will simply send the last recorded one
    My idea was that each device has an ID and password issued on frabication, like a router for instance
        that info will be provided to the telegram bot to connect to the device"""

class TrackingDevice():

    def __init__(self, catalogURL):
        self.catalogURL = catalogURL
        conf = json.load(open("publisher\deviceSettings.json"))
        if conf['isNew']:
            self.deviceID = self.generateID()
            self.devicePassword = self.generatePassword()
        else: 
            self.deviceID = conf['id']
            self.devicePassword = conf['password']
        data = requests.get(self.catalogURL+'/publisher')
        data = data.json()
        self.broker = data['brokerAddress']
        self.topic = data['baseTopic']+'/'+str(self.deviceID)
        self.port = 1883 ## hardcoded?

    def generateID(self):
        data = requests.get(self.catalogURL+'/patients')
        data = data.json()
        return len(data)

    def generatePassword(self):
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(random.sample(chars,len(chars)))[:8]

    def updateCatalog(self):
        postData = {}
        postData[self.deviceID] = {"topic": self.topic, "password": self.devicePassword}
        requests.post(self.catalogURL, json=postData)

    def updateSettings(self):
        conf = json.load(open("publisher\deviceSettings.json"))
        conf['isNew'] = False
        conf['catalogURL'] = self.catalogURL
        conf['brokerAddress'] = self.broker
        conf['port'] = self.port
        conf['topic'] = self.topic
        conf['id'] = self.deviceID
        conf['password'] = self.devicePassword
        with open("publisher\deviceSettings.json", "w") as file:
            json.dump(conf, file, indent = 4)

    def run(self): 
        fs = np.array([6,36,3600,3600,3600,3600]) # sampling frequencies of each sensor
        
        #sensor instances
        tempGenerator = DataGenerator(36.6, 0.05, fs[0]) # one sample every 10 min
        accGenerator = DataGenerator(1, 0, fs[1]) # one sample every ? min
        glucGenerator = DataGenerator(99, 0.85, fs[2]) # one sample every 60 min
        systoleGenerator = DataGenerator(124.6, 1.82, fs[3]) # one sample every 60 min
        diastoleGenerator = DataGenerator(77.7, 0.94, fs[4]) # one sample every 60 min
        satGenerator = DataGenerator(97.7, 1.02, fs[5]) # one sample every 60 min 

        #publisher instance
        publisher = mqttPublisher(str(self.deviceID), self.broker, self.port)
        publisher.start()

        timeCounter = 0
        while True:
            if (timeCounter%fs==0).any():
                # Create the SenML data in JSON format
                data = {
                    "bn": "urn:dev:ow:10e2073a01080063",
                    "e": [
                        {
                            "n": "temperature",
                            "u": "celsius",
                            "v": tempGenerator.drawSample(timeCounter)
                        },
                        {
                            "n": "accelerometer",
                            "u": "m/s2",
                            "v": accGenerator.drawSample(timeCounter)
                        },
                        {
                            "n": "glucose",
                            "u": "mg/dl",
                            "v": glucGenerator.drawSample(timeCounter)
                        },
                        {
                            "n": "systole",
                            "u": "mmHg",
                            "v": systoleGenerator.drawSample(timeCounter)
                        },
                        {
                            "n": "diastole",
                            "u": "mmHg",
                            "v": diastoleGenerator.drawSample(timeCounter)
                        },
                        {
                            "n": "saturation",
                            "u": "%",
                            "v": satGenerator.drawSample(timeCounter)
                        },
                        {
                            "n": "time",
                            "u": "s",
                            "v": timeCounter
                        }
                    ]
                }
                publisher.publish_data(self.topic, data)
            
            time.sleep(1)
            timeCounter += 1
            if timeCounter == 3600:
                timeCounter = 0
            
        publisher.disconnect()


    