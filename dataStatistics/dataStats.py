import json
import cherrypy
import requests

def any_value_is_none(dictionary):
    for value in dictionary.values():
        if value is None:
            return True
    return False


class dataStats(object):
    """ Statistics class that is responsible for stablishing an interface between telegram bot and InfluxDB
        This service receives get requests from the telegram bot and asks (via REST) the influx connector for the 
            required data in order to provide it for the bot
    """
    exposed = True
    def __init__(self, catalogURL):
        self.catalogURL = catalogURL

    def GET(self, *uri):
        connector = requests.get(self.catalogURL + '/connectorURL').json()

        command = uri[0]
        device = int(uri[1])

        metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']
        metricsDict = {} #will associate each metric to its mean and std
        
        if command == 'statistics':
            
            timeframe = uri[2]

            metricsDict = requests.get(connector+'/'+command+'/'+str(device)+'/'+timeframe).json()

        
        elif command == 'check':
            metricsDict = requests.get(connector+'/'+command+'/'+str(device)).json()

        

        if any_value_is_none(metricsDict):
            return json.dumps("N")
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
        
