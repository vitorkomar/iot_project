import json 
import cherrypy

class Catalog(object):
    '''Class for the catalog server'''
    exposed = True

    def GET(self, *uri):
        database = json.load(open('database.json'))
        data = database
        for el in uri:
            data = data[el]
        return json.dumps(data)


    def POST(self):
        pass

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
    cherrypy.engine.start()
    cherrypy.engine.block()