import telepot
from telepot.loop import MessageLoop
import cherrypy
import json 
import time
import random 

class TelegramBot():

    def __init__(self, token):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.conf = json.load(open("telegram\settingsUpdated.json"))
        self.commands = ['/help: show information and brief instructions about available commands.', 
                         '/track: register a new patient to keep track, user must provide patient name. /track <Surname> <Name>',
                         '/tracking: get a list of patients beeing tracked.',
                         '/check: get information about a patient status given its ID. /check <ID>',
                         '/stopTracking: stop tracking the status of a patient given its ID.'] 
        ## need to better define tracking
        ## need to better define check
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def getName(self, chatID, ID):
        for key in self.conf[chatID]['patients'].keys():
            if key == ID:
                return self.conf[chatID]['patients'][key]
        return None

    def generateID(self):
        #data = json.load(open('telegram\settingsUpdated.json'))
        universalID = 0
        for chatID in self.conf.keys():
            universalID += len(self.conf[chatID]['patients'])
        return universalID

    def existingID(self, chatID, ID):
        for key in self.conf[chatID]['patients'].keys():
            if key == ID:
                return True
        return False

    def hasID(self, patientName):
        for chatID in self.conf.keys():
            for key, value in self.conf[chatID]['patients'].items():
                if value == patientName:
                    return True
        return False

    def registerNewPatient(self, chatId, patientName):
        """Register a new patient to keep track"""
        ## need to better define the name of the function and how it is stored maybe tuple instead of two lists
        ## universily identify?????
        ## data or self.conf?? 
        ## Diferent chats should be able to track same patient 
            ## apparently it is done but needs further testing
        #data = json.load(open('telegram\settingsUpdated.json'))
        #data[chatId]['patients'][self.generateID()] = patientName
        if self.hasID(patientName):
            for chatID in self.conf.keys():
                for key, value in self.conf[chatID]['patients'].items():
                    if value == patientName:
                        newID = key
        else:
            newID = str(self.generateID())
            while self.existingID(chatId, newID):
                newID = int(newID)
                newID += 1
                newID = str(newID)
        self.conf[chatId]['patients'][newID] = patientName
        with open("telegram\settingsUpdated.json", "w") as file:
            json.dump(self.conf, file, indent = 4)
        self.conf = json.load(open("telegram\settingsUpdated.json")) #update bot configs

        return newID

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
            elif command == '/track':
                patientName = ' '.join(text.split()[1:]) 
                newID = self.registerNewPatient(chatId, patientName)
                self.bot.sendMessage(chatId, text="Tracking patient "+str(patientName)+'. Patient ID is '+str(newID)+'.')
            elif command == '/tracking':
                if len(self.conf[chatId]['patients']) > 0:
                    self.bot.sendMessage(chatId, text='No patient is beeing tracked at the moment.')
                else: 
                    patientsList = '```\n'
                    patientsList += 'ID : Name\n'
                    for key, value in self.conf[chatId]['patients'].items():
                        patientID = key
                        patientName = value 
                        patientsList += str(patientID)+' : '+str(patientName)+'\n'
                    patientsList += '```'
                    self.bot.sendMessage(chatId, text=patientsList, parse_mode='MarkdownV2')
            elif command == '/check':
                #need to better understand this method
                pass
            elif command == '/stopTracking':
                patientID = text.split()[1]
                if self.getName(chatId, patientID) is None:
                    self.bot.sendMessage(chatId, text='Patient is not being tracked. Please type /tracking to see patients beeing tracked.')
                else: 
                    patientName = self.getName(chatId, patientID)
                    self.conf[chatId]['patients'].pop(patientID)
                    with open("telegram\settingsUpdated.json", "w") as file:
                        json.dump(self.conf, file, indent = 4)
                    self.bot.sendMessage(chatId, text="Patient "+str(patientName)+' with ID '+str(patientID)+' is no longer being tracked.')
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
    token = "6459586229:AAGLeU1eA4q-noi6Uob2El3R69jwfTHHwLI"

    bot = TelegramBot(token)
    cherrypy.config.update({'server.socket_port': 8083})
    cherrypy.quickstart(Server(bot))
    