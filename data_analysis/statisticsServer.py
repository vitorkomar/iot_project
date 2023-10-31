import json
import cherrypy
from analysis_functions import *

class statiticsServer(object):
    '''class for the server that will give statistics for the telegram bot'''
    exposed = True

    def GET(self, *uri):
        operation = uri[0]
        device = uri[1]
        metric = uri[2]
        timeframe = uri[3]

        #this will have to be updated but it is here just to test
        #I based my numbers on a sensor sending data each 10 minutes
        if timeframe == 'month':
            n_samples = 4380
        elif timeframe == 'week':
            n_samples = 1008
        elif timeframe == 'day':
            n_samples = 144
        elif timeframe == 'hour':
            n_samples = 6

        if operation == 'mean':
            res =  calculate_mean(device, metric, n_samples)
            return json.dumps(res)
        elif operation == 'max':
            res =  calculate_max(device, metric, n_samples)
            return json.dumps(res)
        elif operation == 'min':
            res =  calculate_min(device, metric, n_samples)
            return json.dumps(res)
        elif operation == 'std':
            res =  calculate_std(device, metric, n_samples)
            return json.dumps(res)


if __name__ == '__main__':
    conf = {
        '/' : {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }
    webService = statiticsServer()
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_port': 8082})
    cherrypy.engine.start()
    cherrypy.engine.block()
        