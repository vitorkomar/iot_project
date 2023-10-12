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
        self.conf = json.load(open("telegram\Bot_settings.json"))
        self.commands = ['/help: show information and brief instructions about available commands.', 
                         '/track: register a new patient to keep track, user must provide patient name. /track <name>',
                         '/tracking: get a list of patients beeing tracked.',
                         '/check: get information about a patient status given its ID. /check <ID>'] 
        ## need to better define tracking
        ## need to better define check
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def generateID(self):
        data = json.load(open('telegram\Bot_settings.json'))
        universalID = 0
        for chatID in data.keys():
            universalID += len(data[chatID]['patients']['ID'])
        return universalID

    def registerNewPatient(self, chatId, patientName):
        """Register a new patient to keep track"""
        ## need to better define the name of the function and how it is stored maybe tuple instead of two lists
        ## universily identify?????
        ## data or self.conf?? Diferent chats should be able to track same patient 
            ## apparently it is done but needs further testing
        data = json.load(open('telegram\Bot_settings.json'))
        data[chatId]['patients']['name'].append(patientName)
        data[chatId]['patients']['ID'].append(self.generateID())
        with open("telegram\Bot_settings.json", "w") as file:
            json.dump(data, file, indent = 4)
        self.conf = json.load(open("telegram\Bot_settings.json"))

    def on_chat_message(self, msg):
        content_type, chat_type, chatId = telepot.glance(msg)
        chatId = str(chatId)
        text = msg['text']
        command = text.split()[0]
        if chatId not in self.conf:
            self.conf.update({chatId: {'patients': {'name':[], 'ID':[]}}})
            with open("telegram\Bot_settings.json", "w") as file:
                json.dump(self.conf, file, indent = 4)
            self.bot.sendMessage(chatId, text="Hello, thanks for contacting!\nType /help to see available commands.")
        else:
            if command == '/help': 
                self.bot.sendMessage(chatId, text='Available commands:')
                for command in self.commands:
                    self.bot.sendMessage(chatId, text=command)
            elif command == '/track':
                patientName = text.split()[1]
                self.registerNewPatient(chatId, patientName)
                self.bot.sendMessage(chatId, text="Tracking patient "+str(patientName))
            elif command == '/tracking':
                numberOfPatients = len(self.conf[chatId]['patients']['ID'])
                patientsList = '```\n'
                patientsList += 'Name : ID\n'
                for i in range(numberOfPatients):
                    patientName = self.conf[chatId]['patients']['name'][i]
                    patientID = self.conf[chatId]['patients']['ID'][i]
                    patientsList += str(patientName)+' : '+str(patientID)+'\n'
                patientsList += '```'
                self.bot.sendMessage(chatId, text=patientsList, parse_mode='MarkdownV2')

                #tried to make a table but did not work 
                #patientsList = '<pre>\n'
                #patientsList += '|    Name    |   ID  |\n'
                #patientsList += '|:---------|:-----:|\n'
                #for i in range(numberOfPatients):
                #    patientName = self.conf[chatId]['patients']['name'][i]
                #    patientID = self.conf[chatId]['patients']['ID'][i]
                #    patientsList += '|'+str(patientName)+'|'+str(patientID)+'|\n'
                #patientsList += '</pre>'
            elif command == '\check':
                #need to better understand this method
                pass
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
    cherrypy.config.update({'server.socket_port': 8099})
    cherrypy.quickstart(Server(bot))
    