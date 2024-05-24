import numpy as np 
import json
import requests
from mqtt_client import mqttPublisher, mqttSubscriber
import cherrypy
import pandas as pd
from influxdb_client_3 import InfluxDBClient3, Point, write_client_options, WriteOptions, InfluxDBError
import time

# Define callbacks for write responses
def success(self, data: str):
    print(f"Successfully wrote batch: data: {data}")
    pass

def error(self, data: str, exception: InfluxDBError):
    print(f"Failed writing batch: config: {self}, data: {data}, error: {exception}")
    pass

def retry(self, data: str, exception: InfluxDBError):
    print(f"Failed retry writing batch: config: {self}, data: {data}, error: {exception}")
    pass

# Instantiate WriteOptions for batching
write_options = WriteOptions(max_retries=5)
wco = write_client_options(success_callback=success,
                            error_callback=error,
                            retry_callback=retry,
                            WriteOptions=write_options)

                            
class InfluxConnector(object):
    """provides an interface between microservices and the influxDB database"""
    exposed = True



    def __init__(self, catalogURL, clientId):
        self.catalogURL = catalogURL

        self.clientId = clientId
        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = data['brokerPort']
        self.baseTopic = data['baseTopic']
        self.subTopic = data['baseTopic']+'/+/measurement'

        self.influxToken = requests.get(self.catalogURL + '/influxToken').json()
        self.influxOrg = requests.get(self.catalogURL + '/influxOrg').json()
        self.influxHost = requests.get(self.catalogURL + '/influxHost').json()
        self.influxDatabase = requests.get(self.catalogURL + '/influxDatabase').json()

        self.subscriber = mqttSubscriber("alerterSubscriber", self.broker, self.port)   
        self.subscriber.client.on_message = self.on_message
        self.subscriber.client.on_connect = self.my_on_connect
        self.subscriber.client.connect(self.broker, self.port)
        self.subscriber.client.loop_start()
    

    def my_on_connect(self, PahoMQTT, obj, flags, rc):
        '''The on_connect is redefined here for this mqtt client because if for some reason
        it disconnected from the broker it would not be suscribed to the topic
        This occured in testing when someone used the check, statistics or history commands of the bot'''
        self.subscriber.client.subscribe(self.subTopic)

    def run(self):
        """run the data handler"""
        self.subscriber.client.connect(self.broker, self.port)
        #self.subscriber.client.subscribe(self.subTopic)
        #self.subscriber.client.loop_forever()
        self.subscriber.client.loop_forever()

    def on_message(self, PahoMQTT, obj, msg):
        message_topic = msg.topic
        device_id = message_topic.split('/')[1] #not sure about the index TODO
        dataMSG = json.loads(msg.payload)
        print("Message Received")

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

        for key in data:
            metric = data[key]['n']
            point = (
                Point("measurements")
                .tag("deviceID", data[key]["deviceID"])
                .tag("metric", metric)
                .field("unit", data[key]["u"])
                .field("value", data[key]["v"])
                .field("pubTime", data[key]["t"])
            )
            #self.influxClient.write(database=self.influxDatabase, record=point)
            with InfluxDBClient3(host=self.influxHost, token=self.influxToken, org=self.influxOrg, database=self.influxDatabase, write_client_options=wco) as client:
                client.write(record=point)
                client.close()

            print('uploaded data')
        time.sleep(0.001)

    def GET(self, *uri):
        """GET method for the influx connector, it exposes 3 functionalities

        check: which is used to get the last collected data from a patient
        the check command is used following this structure url/check/deviceID

        statistics: which provide the statistics for a time period for a patient
        the statistics command is used following this structure url/statistics/deviceID/timeframe

        plot: which provides a the data for a given time period and for a given measurement,
        this will then be used by the dataPlotter to plot the data and send the image to the bot
        the plot command is used following this structure url/plot/deviceID/timeframe/metric
        """

        metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']

        command = uri[0]
        device = int(uri[1])

        if command == "check":
            metricsDict = {}

            query = """ SELECT "metric", LAST_VALUE("value")
                    FROM "measurements" 
                    WHERE ("metric" != 'acceleration') AND ("deviceID" = """ + str(device) + """) 
                    GROUP BY "metric" """


            influxToken =  "JS6wfmURh1TfcO9oaGFrDtl2lSa7OxDxm5DJ88BG3jhgMy_WtCglNZUlMQ4qd7c8oIcERwDKzaaoviHACnpQmA=="
            influxOrg =  "Prog4IoT"
            influxHost =  "https://eu-central-1-1.aws.cloud2.influxdata.com"
            influxDatabase = "ElderlyMonitoring"

            with InfluxDBClient3(host=influxHost, token=influxToken, org=influxOrg, database=influxDatabase, write_client_options=wco) as client:
                                table = client.query(query=query, language='sql')
                                client.close()

            metricsDict = {}

            for i, el in enumerate(table[0]):
                metric = el.as_py()
                value = table[1][i].as_py()
                metricsDict[metric] = value

            return json.dumps(metricsDict)


        elif command == "statistics":
            metricsDict = {}
            timeframe = uri[2]
            query = """ SELECT "metric", MEAN("value"), STDDEV("value")
                    FROM "measurements" 
                    WHERE ("metric" != 'acceleration') AND ("deviceID" = """ + str(device) + """) AND ("pubTime" >= now() - interval '1 """ + str(timeframe) +"""') 
                    GROUP BY "metric" """

            influxToken =  "JS6wfmURh1TfcO9oaGFrDtl2lSa7OxDxm5DJ88BG3jhgMy_WtCglNZUlMQ4qd7c8oIcERwDKzaaoviHACnpQmA=="
            influxOrg =  "Prog4IoT"
            influxHost =  "https://eu-central-1-1.aws.cloud2.influxdata.com"
            influxDatabase = "ElderlyMonitoring"

            with InfluxDBClient3(host=influxHost, token=influxToken, org=influxOrg, database=influxDatabase, write_client_options=wco) as client:
                                table = client.query(query=query, language='sql')
                                client.close()

            metricsDict = {}

            for i, el in enumerate(table[0]):
                metric = el.as_py()
                mean = table[1][i].as_py()
                std = table[2][i].as_py()
                metricsDict[metric] = {"mean": mean, "std": std}
            return json.dumps(metricsDict)

        elif command == "plot":
            timeframe = uri[2]
            metric = uri[3]

            query = """SELECT *
                        FROM "measurements"
                        WHERE ("metric" ='""" + str(metric) + """') AND ("deviceID" = """ + str(device) + """) AND ("pubTime" >= now() - interval '1 """ + str(timeframe) +"""') """
            with InfluxDBClient3(host=self.influxHost, token=self.influxToken, org=self.influxOrg, database=self.influxDatabase, write_client_options=wco) as client:
                table = client.query(query=query, language='sql')
                client.close()

            df = table.to_pandas().sort_values(by="pubTime")
            return df.to_json()




if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }
    catalogURL = json.load(open("settings.json"))["catalogURL"]
    webService = InfluxConnector(catalogURL, 10)
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 3000})
    cherrypy.engine.start()
    cherrypy.engine.block()