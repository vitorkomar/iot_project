import json 
import cherrypy
import os

class Catalog(object):
    '''Class for the catalog server'''
    exposed = True

    def GET(self, *uri):
        database = json.load(open(os.path.join(os.path.curdir, 'database.json')))
        data = database
        for el in uri:
            data = data[el]
        return json.dumps(data)

    def POST(self, *uri, **params):
        request_data = cherrypy.request.body.read().decode('utf-8')
        new_data = json.loads(request_data)

        with open(os.path.join(os.path.curdir, 'database.json'),'r+') as file:
            file_data = json.load(file)
    
        file_data["patients"].update(new_data)

        with open(os.path.join(os.path.curdir, 'database.json'), "w") as file:
            json.dump(file_data, file, indent = 4)

    def PUT(self):
        pass


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }
    webService = Catalog()
    cherrypy.tree.mount(webService, '/', conf)
    #cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 8083})
    cherrypy.engine.start()
    cherrypy.engine.block()