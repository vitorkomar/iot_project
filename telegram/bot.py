import telepot
from telepot.loop import MessageLoop
import cherrypy
import json 

class TelegramBot():

    def __init__(self, token):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.chat_id = None
        self.conf = json.load(open('bot_settings.json'))
        self.new = self.conf['new']
        if self.new == False:
            self.chat_id = self.conf['chat_id']
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()


    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if self.new:
            self.chat_id = chat_id
            self.conf['chat_id'] = chat_id
            self.conf['new'] = False
            json.dump(self.conf, open('bot_settings.json', 'w'))
        self.bot.sendMessage(self.chat_id, text="Hello, thanks for registering")
    
            
    def fever_alert(self):
        print('function called')
        self.bot.sendMessage(self.chat_id, "Fever Alert: Please check on the patient!")
    
    def fall_alert(self):
        self.bot.sendMessage(self.chat_id, "Fall Alert: Please check on the patient!")
    
    


class Server:
    def __init__(self, bot):
        self.bot = bot

    @cherrypy.expose
    def fever(self):
        self.bot.fever_alert()

    @cherrypy.expose
    def fall(self):
        self.bot.fever_alert()



if __name__ == '__main__':
    bot = TelegramBot("5837844672:AAGPkiYHwtHVQQ71ErsnVvA2u7PBIahxw_E")
    cherrypy.quickstart(Server(bot))
