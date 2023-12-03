import json
import cherrypy
import base64
import matplotlib.pyplot as plt
import os
from io import BytesIO
from analysis_functions import *

import matplotlib
matplotlib.use('agg')

class dataPlotter(object):
    '''class for the server that will provide plots for the telegram bot'''
    exposed = True

    def GET(self, *uri):
        device = int(uri[0])
        metric = uri[1]
        timeframe = uri[2]

        if timeframe == 'month':
            n_samples = 4380
        elif timeframe == 'week':
            n_samples = 1008
        elif timeframe == 'day':
            n_samples = 144
        elif timeframe == 'hour':
            n_samples = 6

        databasePath = os.path.join(os.path.curdir, 'database.csv')
        df = pd.read_csv(databasePath)
        df = df[(df['device_id']==device) & (df['n']==metric)]
        df = df.tail(n_samples)

        fig = plt.figure()
        plt.plot(range(df.shape[0]), df['v'])
        plt.title('Last '+timeframe+' '+metric+' measurements')
        plt.xlabel('time')
        plt.ylabel('°C')
        plt.grid()

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
    webService = dataPlotter()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 1400})
    cherrypy.engine.start()
    cherrypy.engine.block()
        