import json
import cherrypy
import matplotlib.pyplot as plt
from io import BytesIO
import matplotlib.dates as mdates
import requests
import matplotlib
import pandas as pd
import numpy as np ###added to make sample plots must remove later

from matplotlib.dates import DateFormatter, DayLocator, HourLocator, MinuteLocator
matplotlib.use('agg')

class dataPlotter(object):
    '''class for the server that will provide plots for the telegram bot'''
    exposed = True

    def __init__(self, catalogURL):
        self.catalogURL = catalogURL

    def GET(self, *uri):

        connector = requests.get(self.catalogURL + '/connectorURL').json()
        device = int(uri[0])
        metric = uri[1]
        timeframe = uri[2]

        unitDict = {
            'temperature': '°C',
            'glucose': 'mg/dl',
            'diastole': 'mmHg',
            'systole': 'mmHg', 
            'saturation': '%',
            'acceleration': 'm/s2'
        }


        connector = requests.get(self.catalogURL + '/connectorURL').json()

        data = requests.get(connector+'/plot/'+str(device)+'/'+timeframe+'/'+metric).json()

        df = pd.read_json(json.dumps(data))
        df['pubTime'] = pd.to_datetime(df['pubTime'], format='%Y-%m-%d %H:%M:%S')

        print(df)

        if df.empty:
            return json.dumps("No data available for this time period")


        fig = plt.figure()
        plt.plot(df['pubTime'], df['value'])
        plt.title('Last '+ timeframe+' '+metric+' measurements')
        plt.xlabel('time')

        plt.ylabel(unitDict[metric])
        plt.grid()


        if timeframe == 'month':
            formatter = '%d/%m'
            locator = DayLocator()
        elif timeframe == 'week':
            formatter = '%d-%Hh'
            locator = DayLocator()
        elif timeframe == 'day':
            formatter = '%H:%M'
            locator = HourLocator()
        elif timeframe == 'hour':
            formatter = '%H:%M'
            locator = MinuteLocator()

        xformatter = mdates.DateFormatter(formatter)
        plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)

        plt.gca().xaxis.set_major_locator(locator)

        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability

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
        
