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
            
    

if __name__ == '__main__':
    bot = TelegramBot("5837844672:AAGPkiYHwtHVQQ71ErsnVvA2u7PBIahxw_E")
    while True:
        time.sleep(3)
