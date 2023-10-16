import telepot
from telepot.loop import MessageLoop
import cherrypy
import json 
import time
import random 
import requests

class TelegramBot():

    def __init__(self, token, catalogURL):
        self.catalogURL = catalogURL
        self.bot = telepot.Bot(token)
        self.conf = json.load(open("telegram\settingsUpdated.json"))
        self.commands = ['/help: show information and brief instructions about available commands.', 
                         '/connect: connect to a monitoring device, user must provide device ID and password. /connect <DeviceID> <Password>',
                         '/associate: associate a device to the patient it is monitoring, user must provide device ID and patient name. /associate <DeviceID> <Name>',
                         '/monitoring: get a list of patients beeing monitored.',
                         '/check: get information about a patient status given its ID. /check <ID>',
                         '/stopMonitoring: stop monitoring the status of a patient given its name and associated device ID. /stopMonitoring <DeviceID> <Name>'] 
        ## need to better define tracking
        ## need to better define check
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def hasID(self, deviceID):
        for chatID in self.conf.keys():
            for key in self.conf[chatID]['patients'].keys():
                if key == deviceID:
                    return True
        return False

    def isConnected(self, chatID, deviceID):
        for key in self.conf[chatID]['patients'].keys():
            if key == deviceID:
                return True
        return False
    
    def verifyPassword(self, chatId, deviceID, givenPassword):
        data = requests.get(self.catalogURL+'/patients')
        data = data.json()
        if givenPassword == data[deviceID]['password']:
            return True
        else: 
            return False 
    
    def registerDevice(self, chatId, deviceID):
        if self.hasID(deviceID):
            pass
        else:
            self.conf[chatId]['patients'][deviceID] = ''
            with open("telegram\settingsUpdated.json", "w") as file:
                json.dump(self.conf, file, indent = 4)
            self.conf = json.load(open("telegram\settingsUpdated.json")) #update bot configs

    def associateDevice(self, chatId, deviceID, patientName):
        self.conf[chatId]['patients'][deviceID] = patientName
        with open("telegram\settingsUpdated.json", "w") as file:
            json.dump(self.conf, file, indent = 4)
        self.conf = json.load(open("telegram\settingsUpdated.json")) #update bot configs

    def on_chat_message(self, msg):
        content_type, chat_type, chatId = telepot.glance(msg)
        chatId = str(chatId)
        text = msg['text']
        command = text.split()[0]
        if chatId not in self.conf:
            self.conf.update({chatId: {'patients': {}}})
            with open("telegram\settingsUpdated.json", "w") as file:
                json.dump(self.conf, file, indent = 4)
            self.bot.sendMessage(chatId, text="Hello, thanks for contacting!\nType /help to see available commands.")
        else:
            if command == '/help': 
                self.bot.sendMessage(chatId, text='Available commands:')
                for command in self.commands:
                    self.bot.sendMessage(chatId, text=command)
            elif command == '/start':
                self.bot.sendMessage(chatId, text="Hello, thanks for contacting!\nType /help to see available commands.")
            elif command == '/connect':
                deviceID = text.split()[1]
                password = text.split()[2]
                if self.hasID(deviceID) and self.verifyPassword(chatId, deviceID, password):
                    self.registerDevice(chatId, deviceID)
                    self.bot.sendMessage(chatId, text="Succesfully connected to device "+str(deviceID)+".")
                else:
                    self.bot.sendMessage(chatId, text="Incorret credentials.")
            elif command == '/associate': 
                deviceID = text.split()[1]
                patientName = ' '.join(text.split()[2:]) 
                if self.isConnected(chatId, deviceID):
                    self.associateDevice(chatId, deviceID, patientName)
                    self.bot.sendMessage(chatId, text="Device "+str(deviceID)+' is monitoring patient '+str(patientName)+'.')
                else:
                    self.bot.sendMessage(chatId, text="Device "+str(deviceID)+' is not connected.')
            elif command == '/monitoring':
                if len(self.conf[chatId]['patients']) > 0:
                    patientsList = '```\n'
                    patientsList += 'ID : Name\n'
                    for key, value in self.conf[chatId]['patients'].items():
                        patientID = key
                        patientName = value 
                        patientsList += str(patientID)+' : '+str(patientName)+'\n'
                    patientsList += '```'
                    self.bot.sendMessage(chatId, text=patientsList, parse_mode='MarkdownV2')
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            elif command == '/check':
                #need to better understand this method
                pass
            elif command == '/stopMonitoring':
                deviceID = text.split()[1]
                patientName = ' '.join(text.split()[2:])
                if self.getName(chatId, patientID) is None:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. Please type /monitoring to see patients beeing monitored.')
                else: 
                    self.conf[chatId]['patients'].pop(deviceID)
                    with open("telegram\settingsUpdated.json", "w") as file:
                        json.dump(self.conf, file, indent = 4)
                    self.bot.sendMessage(chatId, text="Patient "+str(patientName)+' is no longer being monitored.')
                    self.bot.sendMessage(chatId, text="Device "+str(deviceID)+" is no longer connected.")
            else:
                self.bot.sendMessage(chatId, text="Inavlid command, type /help to see available commands.")
            
    def send_fever_message(self, patient):
        '''method that sends a message to every chat user 
        that are subscribed to a certatin patient'''
        for chatId in self.conf:
            if patient in self.conf[chatId]['patients']:
                self.bot.sendMessage(chatId, "Fever Alert: Please check on the patient!")

    def send_fall_message(self, patient):
        '''method that sends a message to every chat user 
        that are subscribed to a certatin patient'''
        for chatId in self.conf:
            if patient in self.conf[chatId]['patients']:
                self.bot.sendMessage(chatId, "Fall Alert: Please check on the patient!")

class Server():

    def __init__(self, bot):
        self.bot = bot

    @cherrypy.expose
    def fever_alert(self, *uri):
        patient = str(uri[0])
        self.bot.send_fever_message(patient)
        
    @cherrypy.expose
    def fall_alert(self, *uri):
        patient = str(uri[0])
        self.bot.send_fever_message(patient)

if __name__ == '__main__':

    token = "6577470521:AAFTej1Dn-sOG6jE6xrYhvr9BHqudhI-SQg"
    catalogURL = "http://127.0.0.1:8083"

    bot = TelegramBot(token, catalogURL)
    cherrypy.config.update({'server.socket_port': 1402})
    cherrypy.quickstart(Server(bot))
    