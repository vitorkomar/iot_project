import json
import cherrypy
import base64
import os
from influxdb_client_3 import InfluxDBClient3, Point
import requests

class dataStats(object):
    '''class for the server that will provide plots for the telegram bot'''
    exposed = True

    def __init__(self, catalogURL):
        self.catalogURL = catalogURL

    def GET(self, *uri):

        token = requests.get(self.catalogURL + '/influxToken').json()
        org = requests.get(self.catalogURL + '/influxOrg').json()
        host = requests.get(self.catalogURL + '/influxHost').json()
        database = requests.get(self.catalogURL + '/influxDatabase').json()

        command = uri[0]
        device = int(uri[1])

        metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']
        metricsDict = {} #will associate each metric to its mean and std
        
        if command == 'statistics':
            #if the user requested the statistics, this will re
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

        
        elif command == 'check':
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




    
if __name__ == '__main__':
    conf = {
        '/' : {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }


    catalogURL = json.load(open("settings.json"))["catalogURL"]

    webService = dataStats(catalogURL)
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 8050})
    cherrypy.engine.start()
    cherrypy.engine.block()
        
