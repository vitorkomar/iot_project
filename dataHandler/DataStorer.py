from mqtt_client import mqttSubscriber
import numpy as np 
import json
import time
import requests
import os 
from influxdb_client_3 import InfluxDBClient3, Point, write_client_options, WriteOptions, InfluxDBError

# Define callbacks for write responses
def success(self, data: str):
    print(f"Successfully wrote batch: data: {data}")

def error(self, data: str, exception: InfluxDBError):
    print(f"Failed writing batch: config: {self}, data: {data}, error: {exception}")

def retry(self, data: str, exception: InfluxDBError):
    print(f"Failed retry writing batch: config: {self}, data: {data}, error: {exception}")

# Instantiate WriteOptions for batching
write_options = WriteOptions(max_retries=5)
wco = write_client_options(success_callback=success,
                            error_callback=error,
                            retry_callback=retry,
                            WriteOptions=write_options)



class DataStorer(mqttSubscriber): 
    """ Class that as the name says will handle the data gathered by the sensors. 
    It basically is a mqtt subscriber, that is subscribed to ONLY a specific device. 
    A device is the wearable that will keep track of the elderly status, can be seen as the sensors. 
    At each publication on the topic that it is subscribed it will store the new value in its database """


    def __init__(self, catalogURL, clientId):
        self.catalogURL = catalogURL
        self.clientId = clientId
        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = data['brokerPort']
        mqttSubscriber.__init__(self, str(self.clientId), self.broker, self.port)
        self.topic = data['baseTopic']+'/#'
        self.client.on_message = self.on_message
        self.client.on_connect = self.my_on_connect
        self.collected = {'temperature': [],
                          'accelerometer':[],
                          'glucose':[],
                          'systole':[],
                          'diastole':[],
                          'saturation':[]}

        self.alert_url = requests.get(self.catalogURL + '/alert_url').json()
        self.metricsInfo = requests.get(self.catalogURL + '/metrics').json()
        self.thresholds = {}
        for el in self.metricsInfo:
            self.thresholds[el['metric']] = (el['normalMin'], el['normalMax']) 
            #associating each metric to a tuple representing the thresholds

        self.influxToken = requests.get(self.catalogURL + '/influxToken').json()
        self.influxOrg = requests.get(self.catalogURL + '/influxOrg').json()
        self.influxHost = requests.get(self.catalogURL + '/influxHost').json()
        self.influxDatabase = requests.get(self.catalogURL + '/influxDatabase').json()
        #self.influxClient =  InfluxDBClient3(host=self.influxHost, token=self.influxToken, org=self.influxOrg, write_client_options=wco)

    def my_on_connect(self, PahoMQTT, obj, flags, rc):
        #print("*********************Connected to broker \n\n\n\n\n\n\n\n\ ///////////////////////////////////// \n\n\n\n\n ////////////////////******************")
        self.client.subscribe(self.topic)

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
        dataMSG = json.loads(msg.payload)

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
                print(n)

                if n == 'accelerometer':
                    n = 'fall'
                package = {'deviceID':device_id, 'metric':n, 'alertType':'above'}
        
                try:
                    requests.put(self.alert_url, json=package) #sending alert to telegram bot
                    print('Alert sent')
                    print(package)
                except:
                    print("Couldn't send alert")
        
        elif v < self.thresholds[n][0]:
                package = {'deviceID':device_id, 'metric':n, 'alertType':'below'}
                try:
                    requests.put(self.alert_url, json=package) #sending alert to telegram bot
                    print('Alert sent')
                    print(package)
                except:
                    print("Couldn't send alert")
        
        #uploading the data to influx db
        for key in data:
            metric = data[key]['n']
            point = (
                Point(metric)
                .tag("deviceID", data[key]["deviceID"])
                .field("unit", data[key]["u"])
                .field("value", data[key]["v"])
                .field("pubTime", data[key]["t"])
            )
            #self.influxClient.write(database=self.influxDatabase, record=point)
            with InfluxDBClient3(host=self.influxHost, token=self.influxToken, org=self.influxOrg, database=self.influxDatabase, write_client_options=wco) as client:
                client.write(record=point)
                client.close()

            print('uploaded data')
            
