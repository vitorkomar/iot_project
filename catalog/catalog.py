import json 
import cherrypy
import os

def addMonitoringDevice(curr_data, uri, new_data):

    #uri0 -> users; #uri1 -> chat; 
    for el in curr_data[uri[0]]:
        if el["userID"] == uri[1]:
            el["monitoringDevices"].append(new_data)

def addMedicine(curr_data, uri, new_data):
    
    #uri0 -> medicineReminders; #uri1 -> deviceID; 
    for el in curr_data[uri[0]]:
        if el["deviceID"] == uri[1]:
            el["medicine"].append(new_data) #change to string to medicines might be better

def updateBotChat(curr_data, uri, new_data):

    keysList = list(new_data.keys()) #key0 -> userID; #key1 -> deviceID; #key2 -> newData (name or allowReminders)
    for el in curr_data[uri[0]]:
        if el[keysList[0]] == new_data[keysList[0]]:
            for device in el["monitoringDevices"]: 
                if device[keysList[1]] == new_data[keysList[1]]:
                    device[keysList[2]] = new_data[keysList[2]]

def removeDevice(curr_data, uri):

    for el in curr_data['devices']:
        if el["deviceID"] == uri[1]:
            curr_data['devices'].remove(el)
    
    for chat in curr_data["users"]:
        for device in chat["monitoringDevices"]:
            if device["deviceID"] == uri[1]:
                chat["monitoringDevices"].remove(device)
                
    for device in curr_data["medicineReminders"]:
        if device["deviceID"] == uri[1]:
            curr_data["medicineReminders"].remove(device)

def removeReminder(curr_data, uri):

    for device in curr_data["medicineReminders"]:
        if device["deviceID"] == uri[1]:
            for medicine in device["medicines"]:
                if medicine["medicineName"] == uri[2]:
                    device["medicines"].remove(medicine)

def removeFromChat(curr_data, uri):

    for chat in curr_data["users"]:
        if chat["userID"] == uri[1]:
            for device in chat["monitoringDevices"]:
                chat["monitoringDevices"].remove(device)

class Catalog(object):   
    '''Class for the catalog server'''
    exposed = True

    def GET(self, *uri):
        database = json.load(open(os.path.join(os.path.curdir, 'catalogSettings.json')))
        data = database
        for el in uri:
            data = data[el]
        return json.dumps(data)

    def POST(self, *uri, **params):
        request_data = cherrypy.request.body.read().decode('utf-8')
        new_data = json.loads(request_data)
    
        with open(os.path.join(os.path.curdir, 'catalogSettings.json'),'r+') as file:
            file_data = json.load(file)
       
        if len(uri) == 1 and (uri[0] == "devices" or uri[0] == "users"):
            if uri[0]=="devices":
                file_data["medicineReminders"].append({"deviceID": new_data["deviceID"], "medicine": []})
            file_data[uri[0]].append(new_data)
        elif len(uri) == 2 and uri[0] == "users":
            try:
                addMonitoringDevice(file_data, uri, new_data)
            except:
                raise cherrypy.HTTPError(400,"Bad Request. Request must contain valid chat device ID.")
        elif len(uri) == 2 and uri[0] == "medicineReminders":
            try:
                addMedicine(file_data, uri, new_data)
            except:
                raise cherrypy.HTTPError(400,"Bad Request. Request must contain valid device ID.")
        else:
            raise cherrypy.HTTPError(404, "Error: It is only possible to add a new device, new chat or a new medicine reminder.")

        with open(os.path.join(os.path.curdir, 'catalogSettings.json'), "w") as file:
            json.dump(file_data, file, indent = 4)

    def PUT(self, *uri, **params):
        request_data = cherrypy.request.body.read().decode('utf-8')
        new_data = json.loads(request_data)
        
        with open(os.path.join(os.path.curdir, 'catalogSettings.json'),'r+') as file:
            file_data = json.load(file)

        if len(uri) == 1 and uri[0] == "users":
            updateBotChat(file_data, uri, new_data)
        else: 
            raise cherrypy.HTTPError(404, "Error: It is only possible to update users.")

        with open(os.path.join(os.path.curdir, 'catalogSettings.json'), "w") as file:
            json.dump(file_data, file, indent = 4)

    def DELETE(self, *uri, **params): 

        with open(os.path.join(os.path.curdir, 'catalogSettings.json'),'r+') as file:
            file_data = json.load(file)
    
        if len(uri) == 2 and uri[0] == "devices":
            try:
                removeDevice(file_data, uri)
            except:
                raise cherrypy.HTTPError(400,"Bad Request. Request must contain valid device ID.")        
        elif len(uri) == 3 and uri[0] == "medicineReminders":
            try:
                removeReminder(file_data, uri)
            except:
                raise cherrypy.HTTPError(400,"Bad Request. Request must contain valid medicine and device ID.")
        elif len(uri) == 3 and uri[0] == "users":
            try:
                removeFromChat(file_data, uri)
            except:
                raise cherrypy.HTTPError(400,"Bad Request. Request must contain valid chat and device ID.")
        else:
            raise cherrypy.HTTPError(404, "Error: It is only possible to add a new device, new chat or a new medicine reminder.")
        
        with open(os.path.join(os.path.curdir, 'catalogSettings.json'), "w") as file:
            json.dump(file_data, file, indent = 4)

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
    cherrypy.config.update({'server.socket_port': 8084})
    cherrypy.engine.start()
    cherrypy.engine.block()