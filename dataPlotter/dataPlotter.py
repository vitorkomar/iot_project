import json
import cherrypy
import base64
import matplotlib.pyplot as plt
import os
from io import BytesIO
from influxdb_client_3 import InfluxDBClient3, Point
import matplotlib.dates as mdates
import requests
import matplotlib
matplotlib.use('agg')

class dataPlotter(object):
    '''class for the server that will provide plots for the telegram bot'''
    exposed = True

    def __init__(self, catalogURL):
        self.catalogURL = catalogURL

    def GET(self, *uri):

        token = requests.get(self.catalogURL + '/influxToken').json()
        org = requests.get(self.catalogURL + '/influxOrg').json()
        host = requests.get(self.catalogURL + '/influxHost').json()

        client = InfluxDBClient3(host=host, token=token, org=org)
        device = int(uri[0])
        metric = uri[1]
        timeframe = uri[2]


        query = """SELECT *
        FROM '""" + str(metric) + """' 
        WHERE "deviceID" = """ + str(device) + """AND "pubTime" >= now() - interval '1 """ + str(timeframe) + """'"""

        # Execute the query
        database="test"
        table = client.query(query=query, database=database, language='sql')

        # Convert to dataframe
        #df['pubTime'] = pd.to_datetime(df['pubTime'], format='%Y-%m-%d %H:%M:%S')
        df = table.to_pandas().sort_values(by="pubTime")
        df['pubTime'] = pd.to_datetime(df['pubTime'], format='%Y-%m-%d %H:%M:%S')
        unitDict = {
            'temperature': '°C',
            'glucose': 'mg/dl',
            'diastole': 'mmHg',
            'systole': 'mmHg', 
            'saturation': '%',
            'acceleration': 'm/s2'
        }



        fig = plt.figure()
        plt.plot(df['pubTime'], df['value'])
        plt.title('Last '+ timeframe+' '+metric+' measurements')
        plt.xlabel('time')

        plt.ylabel(unitDict[metric])
        plt.grid()


        if timeframe == 'month':
            formatter = '%d/%m'
        elif timeframe == 'week':
            formatter = '%d-%Hh'
        elif timeframe == 'day':
            formatter = '%H:%M'

        xformatter = mdates.DateFormatter(formatter)
        plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)
        plt.xticks(df['pubTime'], rotation=45)
        plt.locator_params(axis='x', nbins=10)
        plt.tight_layout()

        img_buf = BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        plt.close()

        cherrypy.response.headers['Content-Type'] = 'image/png'

        return img_buf.read()
    
if __name__ == '__main__':
    conf = {
        '/' : {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }


    catalogURL = json.load(open("settings.json"))["catalogURL"]

    webService = dataPlotter(catalogURL)
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 1400})
    cherrypy.engine.start()
    cherrypy.engine.block()
        
