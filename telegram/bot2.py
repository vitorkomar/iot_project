import telepot
from telepot.loop import MessageLoop
import cherrypy
import json 
import time
import datetime
from datetime import datetime   
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
        self.reminders = [] ## needed to keep track of type telepot.Event() if stored in json or similar will the typing will be lost
        self.commands = ['/help: show information and brief instructions about available commands.', 
                         '/connect: connect to a monitoring device, user must provide device ID and password. /connect <DeviceID> <Password>',
                         '/associate: associate a device to the patient it is monitoring, user must provide device ID and patient name. /associate <DeviceID> <Name>',
                         '/setRemindersOptions: choose to receive medicine reminders or not (default is to receive). /setReminderOptions <False>'
                         '/monitoring: get a list of patients beeing monitored.',
                         '/check: get most recent information about a patient status given its ID. /check <ID>',
                         '/history: shows a graphical history of a specific sensor, user must provide device ID, metric, time interval. /history <DeviceID> <Metric> <TimeInterval>',
                         '/stopMonitoring: stop monitoring the status of a patient given its name and associated device ID. /stopMonitoring <DeviceID> <Name>',
                         '/schedule: schedule a medicine reminder, user must provide patient name, medicine name, starting time, period. /schedule <PatientName> <MedicineName> <StartTime> <Period>',
                         '/unschedule: stop receiving scheduled reminders, user must provide patient name, medicine name. /unschedule <PatientName> <MedicineName>'] ##cancel notifications for everyone, not sure if this the expected behavior but it like this for now.
        ## need to better define check
        MessageLoop(self.bot, {'chat': self.on_chat_message, 'event': self.on_event}).run_as_thread()

    def checkNewChatID(self, chatId):
        '''checks if the chat ID has already connected with the bot, should return true if it is the first time'''
        for el in self.conf:
            if el['chatID'] == chatId:
                return False
        return True

    def hasID(self, deviceID, chatId):
        for el in self.conf:
            for device in el['devices']:
                if device['deviceID'] == deviceID and el['chatID'] == chatId:
                    return True
        return False

    def getID(self, chatId, patientName):
        for chat in self.conf:
            if chat['chatID'] == chatId:
                for device in  chat['devices']:
                    if device['name'] == patientName:
                        return device['deviceID']

    def getName(self, chatID, deviceID): 
        for chat in self.conf:
            if chat['chatID'] == chatID:
                for device in  chat['devices']:
                    if device['deviceID'] == deviceID:
                        return device['name']

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
        if self.hasID(deviceID, chatId):
            pass
        else:            
            for el in self.conf: 
                if el['chatID'] == chatId:
                    el['devices'].append({'deviceID': deviceID, 'allowReminders': True})
                    with open(self.chatsPath, "w") as file:
                        json.dump(self.conf, file, indent = 4)

            self.medsConf.append({'deviceID': deviceID, 'name':'', 'medicines':[]})
            with open(self.medsPath, "w") as file:
                json.dump(self.medsConf, file, indent = 4)

    def associateDevice(self, chatId, deviceID, patientName):
        for el in self.conf:
            if el['chatID'] == chatId:
                for device in el['devices']:
                    if device['deviceID']==deviceID:
                        device['name'] = patientName
                        with open(self.chatsPath, 'w') as file:
                            json.dump(self.conf, file, indent=4)

        for el in self.medsConf:
            if el['deviceID'] == deviceID:
                el['name'] = patientName
                with open(self.medsPath, "w") as file:
                    json.dump(self.medsConf, file, indent = 4)

    def setReminderOptions(self, chatID, deviceID, preference):
        for el in self.conf: 
            if el['chatID'] == chatID:
                for device in el['devices']:
                    if device['deviceID'] == deviceID:
                        device['allowReminders'] = preference
                        with open(self.chatsPath, "w") as file:
                            json.dump(self.conf, file, indent = 4)

    def isMonitored(self, chatId, name):
        '''returns whether or not a certain chat is monitoring a device'''
        for el in self.conf:
            if el['chatID'] == chatId:
                for device in el['devices']:
                    if device['name'] == name:
                        return True
        return False

        
    def bookMedicineSchedule(self, data, startTime):
        newMedicine = {
                "medicineName": data['event']['medicine'],
                "period": data['event']['time'],
                "startTime": startTime
            }
        self.reminders.append({
            'patientName': data['event']['patient'],
            'medicineName': data['event']['medicine'],
            'event':self.bot.scheduler.event_at(startTime, data)
            })
        for patient in self.medsConf:
            if patient['name'] == data['event']['patient']:
                patient['medicines'].append(newMedicine)
                with open(self.medsPath, 'w') as file:
                    json.dump(self.medsConf, file, indent=4)

    def cancelMedicineSchedule(self, patientName, medicineName):
        for reminder in self.reminders:
            if reminder['patientName'] == patientName and reminder['medicineName'] == medicineName:
                self.bot.scheduler.cancel(reminder['event'])
                self.reminders.remove(reminder)

        for patient in self.medsConf:
            if patient['name'] == patientName:
                for medicine in patient['medicines']:
                    if medicine['medicineName'] == medicineName:
                        patient['medicines'].remove(medicine)
                        with open(self.medsPath, 'w') as file:
                            json.dump(self.medsConf, file, indent=4)
                        break
        
    def sendReminder(self, data):
        patientName = data['event']['patient']
        time = data['event']['time']
        chatId = data['event']['chatID']
        medicineName = data['event']['medicine']
        deviceID = self.getID(chatId, patientName)

        chats = []
        names = []
        for chat in self.conf:
            for device in chat['devices']:
                if device['deviceID'] == deviceID and device['allowReminders'] == True:
                    chats.append(chat['chatID'])
                    names.append(device['name'])
        for chatID, name in zip(chats, names):
            reminder = 'Medicine reminder: administrate '+str(medicineName)+' to '+str(name)+'.'
            self.bot.sendMessage(chatID, text=reminder)

    def on_event(self, data):
        self.sendReminder(data)

        for reminder in self.reminders:
            if reminder['patientName'] == data['event']['patient'] and reminder['medicineName'] == data['event']['medicine']:
                reminder['event'] = self.bot.scheduler.event_later(data['event']['time'], data)

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

            elif command == '/setReminderOptions':
                deviceID = text.split()[1]
                preference = text.split()[2]
                if preference == 'False':
                    self.bot.sendMessage(chatId, text='Reminders from device '+str(deviceID)+' will not be received.')
                    self.setReminderOptions(chatId, deviceID, False)
                elif preference == 'True':
                    self.bot.sendMessage(chatId, text='Reminders from device '+str(deviceID)+' will be received.')
                    self.setReminderOptions(chatId, deviceID, True)
                else:
                    self.bot.sendMessage(chatId, text='Invalid preference. To receive reminders select True, otherwise select False')

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
                deviceID = text.split()[1]
                patientName = self.getName(chatId, text.split()[1])
                if self.isMonitored(chatId, patientName) == False:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to check stauts of monitored patients. Please type /monitoring to see patients beeing monitored.')
                else:
                    statsURL = requests.get(self.catalogURL+"/statsURL").json()
                    url = statsURL+'/check/'+'/'.join(text.split()[1:])
                    stats = requests.get(url).json()
                    message = '```\n'
                    message += 'Metric | Value \n'
                    for metric in ['temperature', 'glucose', 'systole', 'diastole',  'saturation']:
                        value = stats[metric]
                        message += metric + f" | {value:.2f}\n"
                    message += '```'
                    self.bot.sendMessage(chatId, text=message, parse_mode='MarkdownV2')
            
            elif command == '/statistics':
                deviceID = text.split()[1]
                patientName = self.getName(chatId, text.split()[1])
                if self.isMonitored(chatId, patientName) == False:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to check stauts of monitored patients. Please type /monitoring to see patients beeing monitored.')
                elif text.split()[2] not in ['month', 'week', 'day', 'hour']:
                    self.bot.sendMessage(chatId, text='Chosen time interval is not avaiable. Available time intervals are: month, week, day, hour. Please choose a valid time interval.')
                else:
                    statsURL = requests.get(self.catalogURL+"/statsURL").json()
                    url = statsURL+'/statistics/'+'/'.join(text.split()[1:])
                    print(url)
                    stats = requests.get(url).json()
                    metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']
                    message = '```\n'
                    message += 'Metric | Mean | Std\n'
                    for metric in metrics:
                        mean = stats[metric]['mean']
                        std = stats[metric]['std']
                        message += metric + f" | {mean:.2f} | {std:.2f} \n"
                    message += '```'
                    self.bot.sendMessage(chatId, text=message, parse_mode='MarkdownV2')
                                
    
            elif command == '/history':
                plotterURL = requests.get(self.catalogURL+"/plotterURL").json()
                
                if self.isMonitored(chatId, self.getName(chatId, text.split()[1])) == False:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to check history of monitored patients. Please type /monitoring to see patients beeing monitored.')
                elif text.split()[2] not in ['temperature', 'glucose', 'systole', 'diastole',  'saturation']:
                    self.bot.sendMessage(chatId, text='Chosen metric is not avaiable. Available metrics are: temperature, glucose, systole, diastole, saturation. Please choose a valid metric.')
                elif text.split()[3] not in ['month', 'week', 'day', 'hour']:
                    self.bot.sendMessage(chatId, text='Chosen time interval is not avaiable. Available time intervals are: month, week, day, hour. Please choose a valid time interval.')
                else:
                    url = plotterURL+'/'+'/'.join(text.split()[1:])
                    image = requests.get(url)
                    image = image.content
                    with open('image.jpg', "wb") as f:
                        f.write(image)
                    self.bot.sendPhoto(chatId, open('image.jpg', 'rb'))
                    os.remove('image.jpg')

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

            elif command == '/schedule':
                patientName = text.split()[1]
                medicineName = text.split()[2]
                time = int(text.split()[3]) 
                startTimeSTR = ' '.join(text.split()[4:])
                if self.isMonitored(chatId, patientName) == False:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to schedule reminders for monitored patients. Please type /monitoring to see patients beeing monitored.')
                else:
                    deviceID = self.getID(chatId, patientName)
                    startTime = datetime.strptime(startTimeSTR, '%d/%m/%y %H:%M').timestamp()
                    data = {'event': {'chatID': chatId, 'patient':patientName, 'deviceID':deviceID, 'medicine':medicineName, 'time':time}}
                    self.bookMedicineSchedule(data, startTime)
                    self.bot.sendMessage(chatId, text='Reminders scheduled for patient '+str(patientName)+' from '+startTimeSTR+', every '+str(time)+'H.')

            elif command == '/unschedule':
                patientName = text.split()[1]
                medicineName = text.split()[2]
                self.cancelMedicineSchedule(patientName, medicineName)
                self.bot.sendMessage(chatId, text=str(medicineName)+' medicine reminder of patient '+str(patientName)+' removed.')
            else:
                self.bot.sendMessage(chatId, text="Inavlid command, type /help to see available commands.")


    def send_high_temp_alert(self, deviceID):
        '''method that sends a message to every chat user 
        that are subscribed to a certatin patient'''
        for user in self.conf:
            for device in user['devices']:
                if device['deviceID'] == deviceID:
                    self.bot.sendMessage(user['chatID'], "High Temperature Alert: Please check patient "+device['name']+"!")


    def send_low_temp_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Low Temperature Alert: Please check patient "+device['name']+"!")


    def send_high_glucose_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "High Glucose Alert: Please check patient "+device['name']+"!")


    def send_low_glucose_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Low Glucose Alert: Please check patient "+device['name']+"!")


    def send_high_pressure_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "High Blood Pressure Alert: Please check patient "+device['name']+"!")


    def send_low_pressure_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Low Blood Pressure Alert: Please check patient "+device['name']+"!")

    def send_high_systole_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "High Sysolte Alert: Please check patient "+device['name']+"!")


    def send_low_systole_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Low Systole Alert: Please check patient "+device['name']+"!")

    def send_high_diastole_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "High Diastole Alert: Please check patient "+device['name']+"!")


    def send_low_diastole_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Low Diastole Alert: Please check patient "+device['name']+"!")


    def send_high_saturation_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "High Saturation Alert: Please check patient "+device['name']+"!")


    def send_low_saturation_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Low Saturation Alert: Please check patient "+device['name']+"!")

    
    def send_fall_alert(self, deviceID):
        for user in self.conf:
            for device in user['devices']:
                if deviceID == device['deviceID']:
                    self.bot.sendMessage(user['chatID'], "Fall Alert: Please check patient "+device['name']+"!")



class Server(object):
    exposed = True
    def __init__(self, bot):
        self.bot = bot

    def PUT(self, *uri, **params):
        '''this will receive the alerts and call the correct bot method to send the message'''

        request_data = cherrypy.request.body.read().decode('utf-8')
        data = json.loads(request_data)

        device = str(data['deviceID'])
        metric = data['metric']
        alertType = data['alertType'] #above or below
        print(metric)

        if metric=='temperature' and alertType=='above':
            print('alert sent')
            self.bot.send_high_temp_alert(device)
        elif metric=='temperature' and alertType=='below':
            print('alert sent')
            self.bot.send_low_temp_alert(device)
        elif metric=='glucose' and alertType=='above':
            print('alert sent')
            self.bot.send_high_glucose_alert(device)
        elif metric=='glucose' and alertType=='below':
            print('alert sent')
            self.bot.send_low_glucose_alert(device)
        elif metric=='systole' and alertType=='above':
            print('alert sent')
            self.bot.send_high_systole_alert(device)
        elif metric=='systole' and alertType=='below':
            print('alert sent')
            self.bot.send_low_systole_alert(device)
        elif metric=='diastole' and alertType=='above':
            print('alert sent')
            self.bot.send_high_diastole_alert(device)
        elif metric=='diastole' and alertType=='below':
            print('alert sent')
            self.bot.send_low_diastole_alert(device)
        elif metric=='saturation' and alertType=='above':
            print('alert sent')
            self.bot.send_high_saturation_alert(device)
        elif metric=='saturation' and alertType=='below':
            print('alert sent')
            self.bot.send_low_saturation_alert(device)
        elif metric=='fall':
            print('alert sent')
            self.bot.send_fall_alert(device)
            

        
if __name__ == '__main__':

    settings = json.load(open("settings.json"))
    token = settings["token"]
    catalogURL = settings["catalogURL"]
    
    bot = TelegramBot(token, catalogURL)
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tool.session.on': True
        }
    }
    webService = Server(bot)
    cherrypy.tree.mount(webService, '/', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 1402})
    cherrypy.engine.start()
    cherrypy.engine.block()
    