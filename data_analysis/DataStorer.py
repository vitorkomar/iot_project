from mqtt_client import *
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

class DataStorer(mqttSubscriber): 
    def __init__(self, catalogURL, clientId):
        self.catalogURL = catalogURL
        self.clientId = clientId
        data = requests.get(self.catalogURL+'/subscriber')
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
        conf = json.load(open("./settings.json"))
        conf['catalogURL'] = self.catalogURL
        conf['brokerAddress'] = self.broker
        conf['port'] = self.port
        conf['topic'] = self.topic
        conf['id'] = self.clientId
        with open("./settings.json", "w") as file:
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
        print(data)
        for item in data['e']:
            n = item['n']
            u = item['u']
            v = item['v']
            with open('./database.csv','a') as fd:
                newRow = device_id + ',' + str(n) + ',' + str(u) + ',' + str(v) + '\n'
                fd.write(newRow)
