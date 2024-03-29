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
    it will break everything, apparently this is a problem with the library"""

class TelegramBot():

    def __init__(self, token, catalogURL):
        self.catalogURL = catalogURL
        self.bot = telepot.Bot(token)
        self.chatsPath = os.path.join(os.path.curdir, 'chatsInfo.json')
        self.conf = json.load(open(self.chatsPath)) 
        self.medsPath = os.path.join(os.path.curdir, 'medicineInfo.json')
        self.medsConf = json.load(open(self.medsPath)) 
        self.reminders = self.loadReminders() 
        self.commands = ['/help: show information and brief instructions about available commands.', 
                         '/register: connect to a monitoring device, user must provide device ID and password. /register <DeviceID> <Password>',
                         '/associate: associate a device to the patient it is monitoring, user must provide device ID and patient name. /associate <DeviceID> <Name>',
                         '/setReminderOptions: choose to receive medicine reminders or not (default is to receive) for a given patient. /setReminderOptions <PatientName> <False>',
                         '/monitoring: get a list of patients beeing monitored.',
                         '/check: get most recent information about a patient status given its name. /check <PatientName>',
                         '/statistics: get mean and standard deviation of a patient information for a given time period. /statistics <TimePeriod> <PatientName>',
                         '/history: shows a graphical history of a specific sensor, user must provide patient name, metric, time interval. /history <PatientName> <Metric> <TimeInterval>',
                         '/stopMonitoring: stop monitoring the status of a patient given its name and associated device ID. /stopMonitoring <DeviceID> <Name>',
                         '/schedule: schedule a medicine reminder, user must provide patient name, medicine name, period, starting time. /schedule <PatientName> <MedicineName> <Period> <StartTime>',
                         '/unschedule: stop receiving scheduled reminders, user must provide patient name, medicine name. /unschedule <PatientName> <MedicineName>']
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
                    el['devices'].append({'deviceID': deviceID,'allowReminders': True, 'name': 'NO NAME ASSOCIATED'})
                    with open(self.chatsPath, "w") as file:
                        json.dump(self.conf, file, indent = 4)

            self.medsConf.append({'deviceID': deviceID, 'medicines':[]})
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

    def loadReminders(self):
        reminders = []
        for patient in self.medsConf:
            try:
                for medicine in patient['medicines']:
                    data = {'event': {'deviceID':patient['deviceID'], 'medicine':medicine['medicineName'], 'period':medicine['period']}}
                    tNow = datetime.now().timestamp() 
                    correctionTime = medicine['period'] + (tNow - medicine['startTime'])//medicine['period']  
                    reminders.append({
                        'deviceID': data['event']['deviceID'],
                        'medicineName': data['event']['medicine'],
                        'event':self.bot.scheduler.event_at(correctionTime, data)
                        })
            except:
                pass
        return reminders
        
    def bookMedicineSchedule(self, data, startTime):
        newMedicine = {
                "medicineName": data['event']['medicine'],
                "period": data['event']['period'],
                "startTime": startTime
            }
        self.reminders.append({
            'deviceID': data['event']['deviceID'],
            'medicineName': data['event']['medicine'],
            'event':self.bot.scheduler.event_at(startTime, data)
            })
        for patient in self.medsConf:
            if patient['deviceID'] == data['event']['deviceID']:
                patient['medicines'].append(newMedicine)
                with open(self.medsPath, 'w') as file:
                    json.dump(self.medsConf, file, indent=4)

    def cancelMedicineSchedule(self, patientID, medicineName):
        for reminder in self.reminders:
            if reminder['deviceID'] == patientID and reminder['medicineName'] == medicineName:
                self.bot.scheduler.cancel(reminder['event'])
                self.reminders.remove(reminder)

        for patient in self.medsConf:
            if patient['deviceID'] == patientID:
                for medicine in patient['medicines']:
                    if medicine['medicineName'] == medicineName:
                        patient['medicines'].remove(medicine)
                        with open(self.medsPath, 'w') as file:
                            json.dump(self.medsConf, file, indent=4)
                        break
        
    def sendReminder(self, data):
        period = data['event']['period']
        medicineName = data['event']['medicine']
        deviceID = data['event']['deviceID']

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
            if reminder['deviceID'] == data['event']['deviceID'] and reminder['medicineName'] == data['event']['medicine']:
                reminder['event'] = self.bot.scheduler.event_later(data['event']['period'], data)

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
            #for each of the possible commands a different branch is run
            if command == '/help': 
                self.bot.sendMessage(chatId, text='Available commands:')
                for command in self.commands:
                    self.bot.sendMessage(chatId, text=command)

            elif command == '/start':
                self.bot.sendMessage(chatId, text="Hello, thanks for contacting!\nType /help to see available commands.")

            elif command == '/register':
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="Please provide valid credentials.\nFor more information type /help.")
                else:
                    deviceID = text.split()[1]
                    password = text.split()[2]
                    if self.verifyPassword(chatId, deviceID, password):
                        self.registerDevice(chatId, deviceID)
                        self.bot.sendMessage(chatId, text="Succesfully connected to device "+str(deviceID)+".\n Please associate to it the name of the person it is monitoring.")
                    else:
                        self.bot.sendMessage(chatId, text="Incorret credentials.")

            elif command == '/associate': 
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide the device id and the name.\nFor more information type /help.")
                else:
                    deviceID = text.split()[1]
                    patientName = ' '.join(text.split()[2:]) 
                    if self.isConnected(chatId, deviceID):
                        self.associateDevice(chatId, deviceID, patientName)
                        self.bot.sendMessage(chatId, text="Device "+str(deviceID)+' is monitoring patient '+str(patientName)+'.')
                    else:
                        self.bot.sendMessage(chatId, text="Device "+str(deviceID)+' is not connected.')

            elif command == '/setReminderOptions':
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide the name and the preference.\nFor more information type /help.")
                else:
                    patientName = text.split()[1]
                    preference = text.split()[2]
                    deviceID = self.getID(chatId, patientName)
                    if preference == 'False':
                        self.bot.sendMessage(chatId, text='Reminders from patient '+str(patientName)+' will not be received.')
                        self.setReminderOptions(chatId, deviceID, False)
                    elif preference == 'True':
                        self.bot.sendMessage(chatId, text='Reminders from patient '+str(patientName)+' will be received.')
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
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide the patient name.\nFor more information type /help.")
                else:
                    patientName = ' '.join(text.split()[1:])
                    deviceID = self.getID(chatId, patientName)
                    if self.isMonitored(chatId, patientName) == False:
                        self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to check stauts of monitored patients. Please type /monitoring to see patients beeing monitored.')
                    else:
                        statsURL = requests.get(self.catalogURL+"/statsURL").json()
                        url = statsURL+'/check/'+'/'+str(deviceID)
                        stats = requests.get(url).json()
                        message = '```\n'
                        message += 'Metric | Value \n'
                        for metric in ['temperature', 'glucose', 'systole', 'diastole',  'saturation']:
                            value = stats[metric]
                            message += metric + f" | {value:.2f}\n"
                        message += '```'
                        self.bot.sendMessage(chatId, text=message, parse_mode='MarkdownV2')
            
            elif command == '/statistics':
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide the device id and the name.\nFor more information type /help.")
                else:
                    patientName = ' '.join(text.split()[2:])
                    deviceID = self.getID(chatId, patientName)
                    if self.isMonitored(chatId, patientName) == False:
                        self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to check stauts of monitored patients. Please type /monitoring to see patients beeing monitored.')
                    elif text.split()[1] not in ['month', 'week', 'day', 'hour']:
                        self.bot.sendMessage(chatId, text='Chosen time interval is not avaiable. Available time intervals are: month, week, day, hour. Please choose a valid time interval.')
                    else:
                        statsURL = requests.get(self.catalogURL+"/statsURL").json()
                        url = statsURL+'/statistics/'+'/'+str(deviceID)+'/'+text.split()[1]
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
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide the device id and the name.\nFor more information type /help.")
                else:
                    plotterURL = requests.get(self.catalogURL+"/plotterURL").json()
                    
                    patientName = ' '.join(text.split()[3:])
                    deviceID = self.getID(chatId, patientName)

                    if self.isMonitored(chatId, patientName) == False:
                        self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to check history of monitored patients. Please type /monitoring to see patients beeing monitored.')
                    elif text.split()[1] not in ['temperature', 'glucose', 'systole', 'diastole',  'saturation']:
                        self.bot.sendMessage(chatId, text='Chosen metric is not avaiable. Available metrics are: temperature, glucose, systole, diastole, saturation. Please choose a valid metric.')
                    elif text.split()[2] not in ['month', 'week', 'day', 'hour']:
                        self.bot.sendMessage(chatId, text='Chosen time interval is not avaiable. Available time intervals are: month, week, day, hour. Please choose a valid time interval.')
                    else:
                        url = plotterURL+'/'+str(deviceID)+'/'+'/'.join(text.split()[1:3])
                        image = requests.get(url)
                        image = image.content
                        with open('image.jpg', "wb") as f:
                            f.write(image)
                        self.bot.sendPhoto(chatId, open('image.jpg', 'rb'))
                        os.remove('image.jpg')

            elif command == '/stopMonitoring':
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide the device id and the name.\nFor more information type /help.")
                else:
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
                medicineName = text.split()[1]
                period = int(text.split()[2])
                startDate = text.split()[3]
                startHour = text.split()[4]
                patientName = ' '.join(text.split()[5:])
                startTimeSTR = startDate+'/'+str(datetime.now().year)+' '+startHour+' +0100'
                if self.isMonitored(chatId, patientName) == False:
                    self.bot.sendMessage(chatId, text='Patient is not being monitored. It is only possible to schedule reminders for monitored patients. Please type /monitoring to see patients beeing monitored.')
                else:
                    deviceID = self.getID(chatId, patientName)
                    startTime = datetime.strptime(startTimeSTR, '%d/%m/%Y %H:%M %z').timestamp()
                    data = {'event': {'deviceID':deviceID, 'medicine':medicineName, 'period':period}}
                    self.bookMedicineSchedule(data, startTime)
                    self.bot.sendMessage(chatId, text='Reminders scheduled for patient '+str(patientName)+' from '+startTimeSTR[:-6]+', every '+str(period)+'H.')

            elif command == '/unschedule':
                if len(text.split()) <= 1:
                    self.bot.sendMessage(chatId, text="There was an error on the message.\nPlease provide patient and medicine name.\nFor more information type /help.")
                else:
                    patientName = text.split()[1]
                    medicineName = text.split()[2]
                    patientID = self.getID(chatId, patientName)
                    self.cancelMedicineSchedule(patientID, medicineName)
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
    