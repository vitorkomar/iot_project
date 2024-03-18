import json
import cherrypy
import base64
import os
from io import BytesIO
from influxdb_client_3 import InfluxDBClient3, Point
import requests
import matplotlib
matplotlib.use('agg')

class dataStats(object):
    '''class for the server that will provide plots for the telegram bot'''
    exposed = True

    def __init__(self, catalogURL):
        self.catalogURL = catalogURL

    def GET(self, *uri):

        token = requests.get(self.catalogURL + '/influxToken').json()
        org = requests.get(self.catalogURL + '/influxOrg').json()
        host = requests.get(self.catalogURL + '/influxHost').json()

        client = InfluxDBClient3(host=host, token=token, org=org)
        command = uri[0]
        device = int(uri[1])
        metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']
        metricsDict = {}
        if command == 'statistics':
            timeframe = uri[2]
            for metric in metrics:
                query = """SELECT MEAN("value")
                FROM '""" + str(metric) + """' 
                WHERE "deviceID" = """ + str(device) + """AND "pubTime" >= now() - interval '1 """ + str(timeframe) + """'"""

                # Execute the query
                database="test"
                table = client.query(query=query, database=database, language='sql')
                mean = table[0][0].as_py()

                query = """SELECT STDDEV("value")
                FROM '""" + str(metric) + """' 
                WHERE "deviceID" = """ + str(device) + """AND "pubTime" >= now() - interval '1 """ + str(timeframe) + """'"""

                # Execute the query
                database="test"
                table = client.query(query=query, database=database, language='sql')
                std = table[0][0].as_py()

                stastsDict = {"mean": mean, "std": std}
                metricsDict[metric] = stastsDict

        
        elif command == 'check':
            for metric in metrics:
                query = """SELECT  "value"
                        FROM '""" + str(metric) + """' 
                        WHERE "deviceID" = """ + str(device) + """ORDER BY time DESC
                        LIMIT 1"""
                database="test"
                table = client.query(query=query, database=database, language='sql')
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
        
