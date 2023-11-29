from mqtt_client import *
import numpy as np 
import json
import time
import requests
from alert import *
import os 

""" Class that as the name says will handle the data gathered by the sensors. 
    It basically is a mqtt subscriber, that is subscribed to ONLY a specific device. 
    A device is the wearable that will keep track of the elderly status, can be seen as the sensors. 
    At each publication on the topic that it is subscribed it will store the new value in its database,
        if the amount of data surpass a threshold it removes the oldest sample and store the new one 
        (we need to define the threshold based on how much data we want to store, one month of data, two weeks...)
    When requested it provides statics of the stored data """

class DataStorer(mqttSubscriber): 
    def __init__(self, catalogURL, clientId):
        self.catalogURL = catalogURL
        self.clientId = clientId
        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = 1883 ## hardcoded for now
        mqttSubscriber.__init__(self, str(self.clientId), self.broker, self.port)
        self.topic = data['baseTopic']+'/#'
        self.client.on_message = self.on_message
        self.collected = {'temperature': [],
                          'accelerometer':[],
                          'glucose':[],
                          'systole':[],
                          'diastole':[],
                          'saturation':[]}

    def updateSettings(self):
        """update local data handler settings and store them in a json file"""
        conf = json.load(open(os.path.join(os.path.curdir, 'settings.json')))
        conf['catalogURL'] = self.catalogURL
        conf['brokerAddress'] = self.broker
        conf['port'] = self.port
        conf['topic'] = self.topic
        with open(os.path.join(os.path.curdir, 'settings.json'), "w") as file:
            json.dump(conf, file, indent = 4)

    def run(self):
        """run the data handler"""
        self.client.connect(self.broker, self.port)
        self.subscribe(self.topic)
        self.client.loop_forever()

    def on_message(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received
            will be called everytime a message is published on the subscribed topic"""
        message_topic = msg.topic
        device_id = message_topic.split('/')[1]
        data = json.loads(msg.payload)
        print(device_id)
        print(data)

        thresholds = {'temperature': (35, 37)}
        samples = {'temperature': 3} ## afects number of alerts  
        alert_url = "http://127.0.0.1:1402"

        databasePath = os.path.join(os.path.curdir, 'database.csv')
        alert = Alert(thresholds, samples, alert_url, databasePath) #apart from the database path, all the other info will come from the catalog

        for item in data['e']:
            n = item['n']
            u = item['u']
            v = item['v']
            with open(os.path.join(os.path.curdir, 'database.csv'), "a") as fd:
                newRow = str(device_id) + ',' + str(n) + ',' + str(u) + ',' + str(v) + '\n'
                fd.write(newRow)
                alert.compute_metric(device_id, n)
