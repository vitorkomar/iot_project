import telepot
from telepot.loop import MessageLoop
import cherrypy
import json 
import time



def registerNewPatient(chatId, patientId):
    data = json.load(open('bot_settings.json'))
    data[chatId]['patients'].append(patientId)
    with open("bot_settings.json", "w") as file:
        json.dump(data, file, indent = 4)

class TelegramBot():

    def __init__(self, token):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.conf = json.load(open('bot_settings.json'))
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()


    def on_chat_message(self, msg):
        content_type, chat_type, chatId = telepot.glance(msg)
        chatId = str(chatId)
        text = msg['text']
        
        if chatId not in self.conf:
            self.conf.update({chatId: {'patients': []}})
            with open("bot_settings.json", "w") as file:
                json.dump(self.conf, file, indent = 4)
            self.bot.sendMessage(chatId, text="Hello, thanks for registering \n Use the following commands to interact with the bot:\n register patient_id \n check patient")
        
        else:
            if 'register' in text:
                patientId = text.split()[1]
                registerNewPatient(chatId, patientId)
                self.bot.sendMessage(chatId, text="New patient registered sucessfully")
            

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
    bot = TelegramBot("5837844672:AAGPkiYHwtHVQQ71ErsnVvA2u7PBIahxw_E")
    cherrypy.config.update({'server.socket_port': 8099})
    cherrypy.quickstart(Server(bot))
    