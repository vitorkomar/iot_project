import numpy as np 
import json
import time
import requests
import os 

import cherrypy
import pandas as pd
from influxdb_client_3 import InfluxDBClient3, Point, write_client_options, WriteOptions, InfluxDBError

# Define callbacks for write responses
def success(self, data: str):
    #print(f"Successfully wrote batch: data: {data}")
    pass

def error(self, data: str, exception: InfluxDBError):
    #print(f"Failed writing batch: config: {self}, data: {data}, error: {exception}")
    pass

def retry(self, data: str, exception: InfluxDBError):
    #print(f"Failed retry writing batch: config: {self}, data: {data}, error: {exception}")
    pass

# Instantiate WriteOptions for batching
write_options = WriteOptions(max_retries=5)
wco = write_client_options(success_callback=success,
                            error_callback=error,
                            retry_callback=retry,
                            WriteOptions=write_options)
or,
class InfluxConnector(object):
    """provides an interface between microservices and the influxDB database"""
    exposed = True

    def __init__(self, catalogURL):
        self.catalogURL = catalogURL



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

        token = requests.get(self.catalogURL + '/influxToken').json()
        org = requests.get(self.catalogURL + '/influxOrg').json()
        host = requests.get(self.catalogURL + '/influxHost').json()
        database = requests.get(self.catalogURL + '/influxDatabase').json()

        metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']

        command = uri[0]
        device = int(uri[1])

        if command == "check":
            for metric in metrics:
                #this query is used to get the last recorded value
                query = """SELECT  "value"
                        FROM '""" + str(metric) + """' 
                        WHERE "deviceID" = """ + str(device) + """ORDER BY time DESC
                        LIMIT 1"""

                with InfluxDBClient3(host=host, token=token, org=org, database=database) as client:
                    table = client.query(query=query, language='sql')
                    client.close()
    

                value = table[0][0].as_py()
                metricsDict[metric] = value
            return json.dumps(metricsDict)


        elif command == "statistics":
            timeframe = uri[2]
            for metric in metrics:

                #this query is used to get the mean value
                query = """SELECT MEAN("value")
                FROM '""" + str(metric) + """' 
                WHERE "deviceID" = """ + str(device) + """AND "pubTime" >= now() - interval '1 """ + str(timeframe) + """'"""

                with InfluxDBClient3(host=host, token=token, org=org, database=database) as client:
                    table = client.query(query=query, language='sql')
                    client.close()
    
                mean = table[0][0].as_py()

                #this query is used to get the standard deviation of the value
                query = """SELECT STDDEV("value")
                FROM '""" + str(metric) + """' 
                WHERE "deviceID" = """ + str(device) + """AND "pubTime" >= now() - interval '1 """ + str(timeframe) + """'"""


                with InfluxDBClient3(host=host, token=token, org=org, database=database) as client:
                    table = client.query(query=query, language='sql')
                    client.close()
    
                std = table[0][0].as_py()

                stastsDict = {"mean": mean, "std": std}
                metricsDict[metric] = stastsDict
            return json.dumps(metricsDict)

        elif command == "plot":
            timeframe = uri[2]
            timeframe = uri[3]

            query = """SELECT *
            FROM '""" + str(metric) + """' 
            WHERE "deviceID" = """ + str(device) + """AND "pubTime" >= now() - interval '1 """ + str(timeframe) + """'"""

            with InfluxDBClient3(host=host, token=token, org=org, database=database) as client:
                table = client.query(query=query, language='sql')
                client.close()

            df = table.to_pandas().sort_values(by="pubTime")
            df['pubTime'] = pd.to_datetime(df['pubTime'], format='%Y-%m-%d %H:%M:%S')

            return json.dumps(df.to_json())



    def POST(self, *uri, **params):
        """POST method for the influx connector which is used by the handler service to upload
        data to the influx DB"""



        #TODO
        for key in data:
            metric = data[key]['n']
            point = (
                Point(metric)
                .tag("deviceID", data[key]["deviceID"])
                .field("unit", data[key]["u"])
                .field("value", data[key]["v"])
                .field("pubTime", data[key]["t"])
            )
            with InfluxDBClient3(host=self.influxHost, token=self.influxToken, org=self.influxOrg, database=self.influxDatabase, write_client_options=wco) as client:
                client.write(record=point)
                client.close()



if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }
    webService = Catalog()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 3000})
    cherrypy.engine.start()
    cherrypy.engine.block()