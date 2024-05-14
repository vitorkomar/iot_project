import numpy as np 
import json
import time
import os
import requests

from mqtt_client import mqttPublisher, mqttSubscriber

class DataAlerter():
    """ Alerter class that is responsible to send alert messages to the telegram bot when needed
        Alert messages can be either disconnection or sick data
        It cointains one mqtt subscriber and one mqtt publisher:
             The subscriber is subscribed to ElderlyMonitoring/+/measurement (receives from all devices; + wildcard)
             The publisher can publish an alert in the topic ElderlyMonitoring/{deviceID}/alert/{sensorName}/{condition}
    """
    def __init__(self, catalogURL, clientId):
        self.catalogURL = catalogURL
        self.clientId = clientId
        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = data['brokerPort']
        self.baseTopic = data['baseTopic']
        self.subTopic = data['baseTopic']+'/+/measurement'

        self.subscriber = mqttSubscriber("alerterSubscriberEM", self.broker, self.port)
        self.subscriber.client.on_message = self.my_on_message
        self.subscriber.client.on_connect = self.my_on_connect

        self.publisher = mqttPublisher("alerterPublisherEM", self.broker, self.port)
        self.publisher.start()
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
        """ Customized version of standard mqtt on_connect
            During development we faced issues with the maintaining connection with the broker
                everytime we lost connection we were not subscribed anymore
                to solve this issue we implemented this customized on_connect
            Every time it connects to the broker it subscribe to correct topic 
        """
        print("Connected to broker " + self.broker)
        self.subscriber.topic = self.subTopic
        self.subscriber.client.subscribe(self.subTopic, 2)

    def run(self):
        """ Runs the data alerter
        """
        self.subscriber.client.connect(self.broker, self.port)
        self.subscriber.client.loop_forever()

    def my_on_message(self, PahoMQTT, obj, msg):
        """ Everytime a message is received from the broker this customized on_message will be executed
            It checks if the received data is within a threshold and if not sends an alert to the bot 
            The alert specifies which device ID is out of range, which sensor the out of range data comes from 
                and if it is above or below the range
            The alert is sent using an mqtt publisher that publishes
            Example of topic (fever condition): ElderlyMonitoring/0/alert/temperature/above 
        """
        message_topic = msg.topic
        device_id = message_topic.split('/')[1] 
        dataMSG = json.loads(msg.payload)
        print(f"Message received from topic {message_topic}")


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
                    
                    dataAlert = {"alert" : "above", "metric": n}
                    publishOnTopic = self.baseTopic+'/'+str(device_id)+'/alert/'+str(n)+'/above'
                    self.publisher.publish_data(publishOnTopic, dataAlert)
            
            elif v < self.thresholds[n][0]:
                    dataAlert = {"alert" : "below", "metric": n}
                    publishOnTopic = self.baseTopic+'/'+str(device_id)+'/alert/'+str(n)+'/below'
                    self.publisher.publish_data(publishOnTopic, dataAlert)
            
if __name__ == '__main__':

    settings = json.load(open("settings.json"))
    catalogURL = settings["catalogURL"]
    
    alerter = DataAlerter(catalogURL, 1)
    alerter.run()
