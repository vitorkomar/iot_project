from mqtt_clientOld import mqttPublisher, mqttSubscriber
import numpy as np 
import json
import time
import os
import requests

#class DataAlerter(mqttClient): 
class DataAlerter():
    def __init__(self, catalogURL, clientId):
        self.catalogURL = catalogURL
        self.clientId = clientId
        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = data['brokerPort']
        self.baseTopic = data['baseTopic']
        self.subTopic = data['baseTopic']+'/+/measurement'

        self.subscriber = mqttSubscriber("alerterSubscriber", self.broker, self.port)
        self.subscriber.client.on_message = self.on_message
        self.subscriber.client.on_connect = self.my_on_connect

        self.publisher = mqttPublisher("alerterPublisher", self.broker, self.port)

        self.collected = {'temperature': [],
                          'accelerometer':[],
                          'glucose':[],
                          'systole':[],
                          'diastole':[],
                          'saturation':[]}

        self.metricsInfo = requests.get(self.catalogURL + '/metrics').json()
        self.thresholds = {}
        for el in self.metricsInfo:
            self.thresholds[el['metric']] = (el['normalMin'], el['normalMax']) 
            #associating each metric to a tuple representing the thresholds


    def my_on_connect(self, PahoMQTT, obj, flags, rc):
        '''The on_connect is redefined here for this mqtt client because if for some reason
        it disconnected from the broker it would not be suscribed to the topic
        This occured in testing when someone used the check, statistics or history commands of the bot'''
        self.subscriber.client.subscribe(self.subTopic)

    def run(self):
        """run the data handler"""
        self.subscriber.client.connect(self.broker, self.port)
        self.subscriber.client.subscribe(self.subTopic)
        self.subscriber.client.loop_forever()

    def on_message(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received
            will be called everytime a message is published on the subscribed topic"""
        message_topic = msg.topic
        device_id = message_topic.split('/')[1] #not sure about the index TODO
        dataMSG = json.loads(msg.payload)
        print("Message Received")
        print(dataMSG)

        #publisher = mqttPublisher(str(self.deviceID), self.broker, self.port)
        self.publisher.start()

        i = 1
        data = {}
        for item in dataMSG['e']:
            n = item['n'] #getting the name of the metric
            u = item['u'] #getting the unit of the metric
            v = item['v'] #gettign the value of the metric
            t = item['t']
            
            pointName = 'point' + str(i)
            data[pointName] = {'n':n, 'u':u, 'v':v, 'deviceID':device_id, 't': t}
            i += 1

            
            if v > self.thresholds[n][1]:
                    if n == 'acceleration':
                        n = 'fall'
                    
                    #self.publish_data(self.baseTopic+'/'+str(device_id)+'/alert/'+str(n)+'/above')
                    dataAlert = {"alert" : "above", "metric": n}
                    publishOnTopic = self.baseTopic+'/'+str(device_id)+'/alert/'+str(n)+'/above'
                    self.publisher.publish_data(publishOnTopic, dataAlert)
            
            elif v < self.thresholds[n][0]:
                    #self.publish_data(self.baseTopic+'/'+str(device_id)+'/alert/'+str(n)+'/below')
                    dataAlert = {"alert" : "below", "metric": n}
                    publishOnTopic = self.baseTopic+'/'+str(device_id)+'/alert/'+str(n)+'/above'
                    self.publisher.publish_data(publishOnTopic, dataAlert)
            
if __name__ == '__main__':

    settings = json.load(open("settings.json"))
    catalogURL = settings["catalogURL"]
    
    alerter = DataAlerter(catalogURL, 1)
    alerter.run()
