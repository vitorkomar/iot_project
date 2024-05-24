import time
import json
import random
import requests
import os 
import numpy as np
from time import strftime, localtime

from DataGenerator import DataGenerator, AccDataGenerator
from mqtt_client import mqttPublisher

class TrackingDevice():
    """ Class that aggregates the sensors that will gather info about patients 
    It contains a mqtt publisher, that publishes on two specific topic. 
        Topics are: 
            (i) ElderlyMonitoring/{deviceID}/measurement
            (ii) ElderlyMonitoring/{deviceID}/alert/disconnection
        (i) is used when new data needs to be published
        (ii) is used when a disconnection alert needs to be published, for intance, when the device is turned off
    Acquiring data depends on the sampling frequency of each simulated sensor
    At each publication it will publish only the new data gathered by a sensor
    Each device has an ID and password issued on frabication, like a router for instance and
        that info will be provided to the telegram bot to connect to the device        
    """
    def __init__(self, catalogURL):
        self.catalogURL = catalogURL
        conf = json.load(open(os.path.join(os.path.curdir, 'deviceSettings.json')))
        if conf['isNew']:
            self.deviceID = self.generateID()
            self.devicePassword = self.generatePassword()
        else: 
            self.deviceID = conf['id']
            self.devicePassword = conf['password']
        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.topic = data['baseTopic']+'/'+str(self.deviceID)+'/measurement'
        self.port = data['brokerPort']
        self.disconnectTopic = data['baseTopic']+'/'+str(self.deviceID)+'/alert/disconnection'
        self.publisher = mqttPublisher(str(self.deviceID), self.broker, self.port)

    def generateID(self):
        """ Simulates the ID that would be issued on fabrication
            For developing/testing/demonstration reasons it was decided to keep it as the amount of already existing devices
        """
        data = requests.get(self.catalogURL+'/devices')
        data = data.json()
        return len(data)

    def generatePassword(self):
        """ Simulates the Password that would be issued on fabrication
            For developing/testing/demonstration reasons it was decided to keep it as a fixed password, 123 in our case
        """
        #Example of possible simple randomized password
        #chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        #return ''.join(random.sample(chars,len(chars)))[:8]
        return '123'

    def updateCatalog(self):
        """ Updates the catalog information using a post request
        """
        data = requests.get(self.catalogURL)
        data = data.json()
        needsUpdate = True
        for device in data['devices']:
            if self.deviceID == int(device['deviceID']):
                needsUpdate = False
        if needsUpdate:
            postData = {"deviceID":str(self.deviceID), "topic": self.topic, "password": self.devicePassword}
            requests.post(self.catalogURL+'/devices', json=postData)

    def updateSettings(self):
        """ Updates local device settings
        """
        conf = json.load(open(os.path.join(os.path.curdir, 'deviceSettings.json')))
        conf['isNew'] = False
        conf['catalogURL'] = self.catalogURL
        conf['topic'] = self.topic
        conf['id'] = self.deviceID
        conf['password'] = self.devicePassword
        with open(os.path.join(os.path.curdir, 'deviceSettings.json'), "w") as file:
            json.dump(conf, file, indent = 4)

    def removeFromCatalog(self):
        """ Removes the catalog information using a delete request
        """
        disconnectAlert = {"alert" : "disconnection"}
        self.publisher.publish_data(self.disconnectTopic, disconnectAlert)
        self.publisher.stop()
        print("Published "+ self.disconnectTopic)
        print(f"Disconnecting device {self.deviceID}")
        uri = '/devices/'+str(self.deviceID)
        requests.delete(self.catalogURL + uri)
            
    def run(self):
        """ Simulates the behavior of all sensors inside the device while also publishing messages
        """
        fs = np.array([30, 30, 30, 30, 30, 30])

        tempGenerator = DataGenerator(36.6, 0.16, fs[0], 'temperature', 'celsius') 
        accGenerator = AccDataGenerator(0, 0, fs[1], 'acceleration', 'm/s2') 
        glucGenerator = DataGenerator(80, 2, fs[2], 'glucose', 'mg/dl') 
        systoleGenerator = DataGenerator(124.6, 1, fs[3], 'systole', 'mmHg') 
        diastoleGenerator = DataGenerator(77.7, 1, fs[4], 'diastole', 'mmHg')
        satGenerator = DataGenerator(85, 1.42, fs[5], 'saturation', '%')

        healthyGenerators = np.array([tempGenerator, accGenerator, glucGenerator, systoleGenerator, diastoleGenerator, satGenerator])

        tempGenerator2 = DataGenerator(36.7, 0.16, fs[0], 'temperature', 'celsius') 
        accGenerator2 = AccDataGenerator(0, 0, fs[1], 'acceleration', 'm/s2') 
        glucGenerator2 = DataGenerator(250, 1, fs[2], 'glucose', 'mg/dl') 
        systoleGenerator2 = DataGenerator(124.6, 1, fs[3], 'systole', 'mmHg') 
        diastoleGenerator2 = DataGenerator(77.7, 1, fs[4], 'diastole', 'mmHg') 
        satGenerator2 = DataGenerator(85, 1.42, fs[5], 'saturation', '%') 

        sickGenerators = np.array([tempGenerator2, accGenerator2, glucGenerator2, systoleGenerator2, diastoleGenerator2, satGenerator2])

        self.publisher.start()

        timeCounter = 0
        
        generators = healthyGenerators
        healthy = True
        while True:
            if (timeCounter%fs==0).any():
                data = { "bn": "urn:dev:ow:10e2073a01080063", "e":[]}
                for g in generators[timeCounter%fs==0]:
                    data["e"].append({
                            "n": g.n,
                            "u": g.u,
                            "v": g.drawSample(),
                            "t": strftime('%Y-%m-%d %H:%M:%S', localtime(time.time()))
                        })
                self.publisher.publish_data(self.topic, data)
                print("Published " + str(timeCounter) + " "+ self.topic)
            time.sleep(1)
            timeCounter += 1

            if timeCounter%30==0:
                if healthy:
                    healthy = False
                    generators = sickGenerators
                else:
                    healthy = True
                    generators = healthyGenerators

            if timeCounter == 3600: #avoids possible overflow (loop forever)
                timeCounter = 0
            
    
