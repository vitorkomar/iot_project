import telepot
from telepot.loop import MessageLoop
import cherrypy
import json 
import time
import random 
import requests
import os

"""Telegram bot that will allow interaction with wearable device 
    my opnion is that to understand the bot is better to run it and use it alongside with reading the code
    VERY IMPORTANT: DO NOT BLOCK THE BOT!!!!!
    it will break everything, still need to find a way to fix this behaviour"""

class TelegramBot():

    def __init__(self, token, catalogURL):
        self.catalogURL = catalogURL
        self.bot = telepot.Bot(token)
        self.chatsPath = os.path.join(os.path.curdir, 'chatsInfo.json')
        self.conf = json.load(open(self.chatsPath)) 
        self.medsPath = os.path.join(os.path.curdir, 'medicineInfo.json')
        self.medsConf = json.load(open(self.medsPath)) 
        self.commands = ['/help: show information and brief instructions about available commands.', 
                         '/connect: connect to a monitoring device, user must provide device ID and password. /connect <DeviceID> <Password>',
                         '/associate: associate a device to the patient it is monitoring, user must provide device ID and patient name. /associate <DeviceID> <Name>',
                         '/monitoring: get a list of patients beeing monitored.',
                         '/check: get information about a patient status given its ID. /check <ID>',
                         '/stopMonitoring: stop monitoring the status of a patient given its name and associated device ID. /stopMonitoring <DeviceID> <Name>'] 
        ## need to better define check
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def checkNewChatID(self, chatId):
        '''checks if the chat ID has already connected with the bot, should return true if it is the first time'''
        for el in self.conf:
            if el['chatID'] == chatId:
                return False
        return True

    def hasID(self, deviceID):
        for el in self.conf:
            for device in el['devices']:
                if device['deviceID'] == deviceID:
                    return True
        return False

    def isConnected(self, chatID, deviceID):
        for el in self.conf:
            if el['chatID'] == chatID:
                for device in el['devices']:
                    if device['deviceID'] == deviceID:
                        return True
        return False
    
    def verifyPassword(self, chatId, deviceID, givenPassword):
        data = requests.get(self.catalogURL+'/devices')
        data = data.json()
        for device in data:
            if deviceID == str(device['deviceID']) and givenPassword == device['password']:
                return True
        return False 
    
    def registerDevice(self, chatId, deviceID):
        if self.hasID(deviceID):
            pass
        else:            
            for el in self.conf: 
                if el['chatID'] == chatId:
                    el['devices'].append({'deviceID': deviceID})
                    with open(self.chatsPath, "w") as file:
                        json.dump(self.conf, file, indent = 4)

    def associateDevice(self, chatId, deviceID, patientName):
        for el in self.conf:
            if el['chatID'] == chatId:
                for device in el['devices']:
                    if device['deviceID']==deviceID:
                        device['name'] = patientName
                        with open(self.chatsPath, 'w') as file:
                            json.dump(self.conf, file, indent=4)
                
    def isMonitored(self, chatId, name):
        '''returns whether or not a certain chat is monitoring a device'''
        for el in self.conf:
            if el['chatID'] == chatId:
                for device in el['devices']:
                    if device['name'] == name:
                        return True
        return False

    def checkPatient(self, metric, patientName):
        '''method that send a get request to the data analysis rest server to get data'''
        #still not implemented
        pass

    def updateMedicineSchedule(self, patientName, medicineName, period, firstTaken):
        newMedicine = {
                "medicineName": medicineName,
                "period": period,
                "firstTaken": firstTaken
            }
        for patient in self.medsConf:
            if patient['name'] == patientName:
                patient['medicines'].append(newMedicine)

    def on_chat_message(self, msg):
        content_type, chat_type, chatId = telepot.glance(msg)
        chatId = str(chatId)
        text = msg['text']
        command = text.split()[0]

        if self.checkNewChatID(chatId):
            self.conf.append({"chatID": chatId, "devices": []})
            with open(self.chatsPath, "w") as file:
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
                if self.verifyPassword(chatId, deviceID, password):
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
                for el in self.conf:
                    if el['chatID'] == chatId:
                        devicesList = el['devices']
                if len(devicesList) > 0:
                    patientsList = '```\n'
                    patientsList += 'ID : Name\n'
                    for device in devicesList:
                        patientID = device['deviceID']
                        patientName = device['name'] 
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
                if self.isMonitored(chatId, patientName) == False:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. Please type /monitoring to see patients beeing monitored.')
                else:
                    for el in self.conf:
                        if el['chatID'] == chatId:
                            devices = el['devices']
                            for device in devices:
                                if device['name'] == patientName:
                                        devices.remove(device)
                    
                    with open(self.chatsPath, "w") as file:
                        json.dump(self.conf, file, indent = 4)
                    self.bot.sendMessage(chatId, text="Patient "+str(patientName)+' is no longer being monitored.')
                    self.bot.sendMessage(chatId, text="Device "+str(deviceID)+" is no longer connected.")

            else:
                self.bot.sendMessage(chatId, text="Inavlid command, type /help to see available commands.")

    """We need to finish data analysis in order to properly implement the following methods and check functionality"""
    def send_fever_message(self, deviceID):
        '''method that sends a message to every chat user 
        that are subscribed to a certatin patient'''
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Fever Alert: Please check patient "+device['name']+"!")


class Server():

    def __init__(self, bot):
        self.bot = bot

    @cherrypy.expose
    def alert(self, *uri):
        '''this method will be used to receive every method, it will also get the metric and call the
        right method of the bot'''
        device = str(uri[0])
        metric = str(uri[1])
        print(uri)
        #for now every alert will be fever so, just to test it
        #the specific method for each alert will have to be specified 
        self.bot.send_fever_message(device)
        
        '''
        if metric == 'temperature':
            self.bot.send_fever_alert(device)
        elif metric == 'glucose':
            self.bot.send_glucose_alert(device)'''
        
    
if __name__ == '__main__':

    token = "6577470521:AAFTej1Dn-sOG6jE6xrYhvr9BHqudhI-SQg"
    catalogURL = "http://127.0.0.1:8084"
    #catalogURL = "http://192.168.11.43:8083"
    
    bot = TelegramBot(token, catalogURL)
    cherrypy.config.update({'server.socket_port': 1402})
    cherrypy.quickstart(Server(bot))
    