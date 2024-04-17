import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import cherrypy
import json 
import time
#import datetime
from datetime import datetime   
import random 
import requests
import os
from mqtt_client import mqttSubscriber
"""Telegram bot that will allow interaction with wearable device 
    my opnion is that to understand the bot is better to run it and use it alongside with reading the code
    VERY IMPORTANT: DO NOT BLOCK THE BOT!!!!!
    it will break everything, apparently this is a problem with the library"""

class TelegramBot():

    def __init__(self, token, catalogURL):
        self.catalogURL = catalogURL

        data = requests.get(self.catalogURL)
        data = data.json()
        self.broker = data['brokerAddress']
        self.port = data['brokerPort']
        self.botSubscriber = mqttSubscriber("botSubscriber", self.broker, self.port)
        self.topic = data['baseTopic']+'/+/alert/#'
        self.botSubscriber.client.on_message = self.on_alert
        self.botSubscriber.client.on_connect = self.my_on_connect
    
        self.bot = telepot.Bot(token)
        self.reminders = self.loadReminders() 
        self.mode = "Listening"
        self.buffer = [None] ### helper buffer of user inputs 
        self.inline_keyboard_message = None
        self.commands = ['Help: show information and brief instructions about available commands.', 
                         'Register: connect to a monitoring device, user must provide device ID and password.',
                         'Associate: associate a device to the patient it is monitoring, user must provide device ID and patient name.',
                         'Reminder Options: choose to receive medicine reminders or not (default is to receive) for a given patient.',
                         'Monitoring: get a list of patients beeing monitored.',
                         'Check: get most recent information about a patient status given its name.',
                         'Statistics: get mean and standard deviation of a patient information for a given time period.',
                         'History: shows a graphical history of a specific sensor, user must provide patient name, metric, time interval.',
                         'Stop Monitoring: stop monitoring the status of a patient given its name and associated device ID.',
                         'Schedule: schedule a medicine reminder, user must provide patient name, medicine name, period, starting time.',
                         'Unschedule: stop receiving scheduled reminders, user must provide patient name, medicine name.']
        self.initial_Keyboard_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Help', callback_data="Help"),             InlineKeyboardButton(text='Register', callback_data="Register")],
            [InlineKeyboardButton(text='Edit Name', callback_data="Associate"),   InlineKeyboardButton(text='Reminder Options', callback_data="Reminders")],
            [InlineKeyboardButton(text='Monitoring', callback_data="Monitoring"), InlineKeyboardButton(text='Check', callback_data="Check")],
            [InlineKeyboardButton(text='Statistics', callback_data="Stats"),      InlineKeyboardButton(text='History', callback_data="History")],
            [InlineKeyboardButton(text='Stop Monitoring', callback_data="StopM"), InlineKeyboardButton(text='Schedule', callback_data="Schedule")],
            [InlineKeyboardButton(text='Unschedule', callback_data="Unschedule"), InlineKeyboardButton(text='Hide', callback_data="Hide")]
                        ])
        MessageLoop(self.bot, {'chat': self.on_chat_message, 'callback_query': self.on_callback, 'event': self.on_event}).run_as_thread()

    def checkNewChatID(self, chatId):
        '''checks if the chat ID has already connected with the bot, should return true if it is the first time'''
        
        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json()
        
        for el in chatsLists:
            if el['chatID'] == chatId:
                return False
        return True

    def hasID(self, deviceID, chatId):

        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json()

        for el in chatsLists:
            for device in el['monitoringDevices']:
                if device['deviceID'] == deviceID and el['chatID'] == chatId:
                    return True
        return False

    def getID(self, chatId, patientName):

        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json()

        for chat in chatsLists:
            if chat['chatID'] == chatId:
                for device in  chat['monitoringDevices']:
                    if device['name'] == patientName:
                        return device['deviceID']

    def getName(self, chatID, deviceID): 

        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json() 

        for chat in chatsLists:
            if chat['chatID'] == chatID:
                for device in chat['monitoringDevices']:
                    if device['deviceID'] == deviceID:
                        return device['name']

    def getDevicesList(self, chatID):
        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json()
        for el in chatsLists:
            if el['chatID'] == str(chatID):
                devicesList = el['monitoringDevices']
        return devicesList

    def buildPatientsKeyboard(self, devicesList, query):
        patientsButtons = []
        for device in devicesList:
            button = InlineKeyboardButton(text=device['name'], callback_data=query + " " + device["deviceID"] + " " +device['name'])
            patientsButtons.append(button) 
        markup = InlineKeyboardMarkup(inline_keyboard=[patientsButtons])
        return markup

    def isConnected(self, chatID, deviceID):

        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json() 

        for el in chatsLists:
            if el['chatID'] == chatID:
                for device in el['monitoringDevices']:
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
            chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json() 
            for el in chatsLists: 
                if el['chatID'] == chatId:
                    uri =  '/telegramBotChats/'+str(chatId)
                    postData = {'deviceID': deviceID, 'allowReminders': True, 'name': 'device: ' +str(deviceID)+' (NO NAME ASSOCIATED)'}
                    requests.post(self.catalogURL + uri, json=postData)

    def associateDevice(self, chatId, deviceID, patientName): 

        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json() 
        for el in chatsLists:
            if el['chatID'] == chatId:
                for device in el['monitoringDevices']:
                    if device['deviceID']==deviceID:
                        putData = {"chatID":chatId, "deviceID":deviceID, "name":patientName}
                        requests.put(self.catalogURL + '/telegramBotChats', json=putData)
 
    def setReminderOptions(self, chatID, deviceID, preference):
        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json()
        for el in chatsLists: 
            if el['chatID'] == chatID:
                for device in el['monitoringDevices']:
                    if device['deviceID'] == deviceID:
                        putData = {"chatID":chatID, "deviceID":deviceID, "allowReminders":preference}
                        requests.put(self.catalogURL + '/telegramBotChats', json=putData)

    def isMonitored(self, chatId, name):
        '''returns whether or not a certain chat is monitoring a device'''
        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json()
        for el in chatsLists:
            if el['chatID'] == chatId:
                for device in el['monitoringDevices']:
                    if device['name'] == name:
                        return True
        return False

    def loadReminders(self): 
        medsLists = requests.get(self.catalogURL + '/medicineReminders').json()
        reminders = []
        for patient in medsLists:
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
        
    def bookMedicineSchedule(self, data, startTime, deviceID): 
        newMedicine = {
                "medicineName": data['event']['medicine'],
                "period": data['event']['period'],
                "startTime": startTime
            }
        uri = '/medicineReminders/'+str(deviceID)
        requests.post(self.catalogURL + uri, json=newMedicine)
        self.reminders = self.loadReminders() 

    def cancelMedicineSchedule(self, deviceID, medicineName): 
        for reminder in self.reminders:
            if reminder['deviceID'] == deviceID and reminder['medicineName'] == medicineName:
                self.bot.scheduler.cancel(reminder['event'])
                self.reminders.remove(reminder)

        uri = '/medicineReminders/'+str(deviceID)+'/'+str(medicineName)
        requests.delete(self.catalogURL + uri)
        
    def sendReminder(self, data):
        period = data['event']['period']
        medicineName = data['event']['medicine']
        deviceID = data['event']['deviceID']

        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json() 

        chats = []
        names = []
        for chat in chatsLists:
            for device in chat['monitoringDevices']:
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
        
        if self.checkNewChatID(chatId):
            uri = '/telegramBotChats'
            postData = {"chatID": chatId, "monitoringDevices": []}
            requests.post(self.catalogURL + uri, json=postData)
            self.bot.sendMessage(chatId, text="Hello, thanks for contacting!\nPress Help to see available commands.")
            self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
        else:
            #for each of the possible commands a different branch is run
            if self.mode == "Listening":
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
            elif self.mode == 'Register ID':
                try:
                    deviceID = int(text)
                    if self.hasID(text, chatId):
                        self.bot.sendMessage(chatId, text="Device "+text+" is already connected.")
                        self.mode = "Listening"
                        self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
                    else:
                        self.buffer[0] = text
                        self.bot.sendMessage(chatId, text="Please provide the password of device "+text+".")
                        self.mode = "Register Password"
                except ValueError:
                    self.bot.sendMessage(chatId, text="Device ID must be a number.")
                    self.mode = "Listening"
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
            elif self.mode == "Register Password":
                password = text
                if self.verifyPassword(chatId, self.buffer[0], password):
                    self.registerDevice(chatId, self.buffer[0])
                    self.bot.sendMessage(chatId, text="Succesfully connected to device "+str(self.buffer[0])+".\n Please associate to it the name of the person it is monitoring.\n What is their name?")
                    self.mode = "Register Name"
                else:
                    self.bot.sendMessage(chatId, text="Incorret credentials.")
                    self.mode = "Listening"
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
            elif self.mode == "Register Name":
                self.buffer.append(text) 
                self.associateDevice(chatId, self.buffer[0], self.buffer[1])
                self.bot.sendMessage(chatId, text="Device "+str(self.buffer[0])+' is monitoring patient '+str(self.buffer[1])+'.')
                markup = InlineKeyboardMarkup(inline_keyboard=[
                                                [InlineKeyboardButton(text='Yes', callback_data="AllowReminders" + " " + self.buffer[0] + " " + self.buffer[1]), 
                                                InlineKeyboardButton(text='No', callback_data="BlockReminders" + " " + self.buffer[0] + " " + self.buffer[1])]])
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Do you wish to receive notifiactions about '+str(self.buffer[0])+'?', reply_markup=markup)
                self.mode = "Waiting Inline" 

            elif self.mode == "Associate Name":
                self.buffer.append(text) 
                self.associateDevice(chatId, self.buffer[0], self.buffer[1])
                self.bot.sendMessage(chatId, text="Device "+str(self.buffer[0])+' is monitoring patient '+str(self.buffer[1])+'.')
                self.mode = "Listening"
                self.buffer = [None]
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
                            
            elif self.mode == "Schedule Medicine Name":
                self.buffer.append(text)
                self.bot.sendMessage(chatId, text="Please provide the periodicity of the reminder (in hours).")
                self.mode = "Schedule Medicine Period"

            elif self.mode == "Schedule Medicine Period":
                try:
                    period = int(text)
                    self.buffer.append(period)
                    self.bot.sendMessage(chatId, text="Please provide the first time the patient is supposed to take the medicine.\nFormat: (dd/mm HH:MM)")
                    self.mode = "Schedule Medicine Initial"
                except ValueError:
                    self.bot.sendMessage(chatId, text="The medicine period must be a number in hours.")
                    self.buffer = [None]
                    self.mode = "Listening"
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

            elif self.mode == "Schedule Medicine Initial":
                try:
                    startDate = text.split()[0]
                    startHour = text.split()[1]
                    startTimeSTR = startDate+'/'+str(datetime.now().year)+' '+startHour
                    startTime = datetime.strptime(startTimeSTR, '%d/%m/%Y %H:%M').timestamp()
                    data = {'event': {'deviceID':self.buffer[0], 'medicine':self.buffer[2], 'period':self.buffer[-1]}}
                    self.bookMedicineSchedule(data, startTime, self.buffer[0])
                    self.bot.sendMessage(chatId, text='Reminders scheduled for patient '+str(self.buffer[1])+' from '+startTimeSTR+', every '+str(self.buffer[-1])+'H.')
                except ValueError:
                    self.bot.sendMessage(chatId, text="The time must follow the format: (dd/mm HH:MM).")
                self.buffer = [None]
                self.mode = "Listening"
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

            elif self.mode == 'Unschedule Medicine Name':
                self.buffer.append(text)
                self.cancelMedicineSchedule(self.buffer[0], self.buffer[-1])
                self.bot.sendMessage(chatId, text=str(self.buffer[-1])+' medicine reminder of patient '+str(self.buffer[1])+' removed.')
                self.buffer = [None]
                self.mode = "Listening"
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
            else:
                self.bot.sendMessage(chatId, text="Inavlid command, press Help to see available commands.")
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

    def on_callback(self, msg):
        query_id, chatId, query_data = telepot.glance(msg, flavor='callback_query')
        
        query_data = query_data.split()
        command = query_data[0]
        self.bot.editMessageReplyMarkup((chatId, msg['message']['message_id']), reply_markup=None) #clear inline_keyboard
        if command == 'Help':
            self.mode = "Listening"
            self.bot.sendMessage(chatId, text='Available commands:')
            for command in self.commands:
                self.bot.sendMessage(chatId, text=command)
            self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == 'Register':
            self.bot.sendMessage(chatId, text="Please provide the device ID of the device that you want to register.")
            self.mode = "Register ID"
        
        elif command == 'AllowReminders':
            self.bot.sendMessage(chatId, text='Reminders from patient '+str(" ".join(query_data[2:]))+' will be received.')
            self.setReminderOptions(str(chatId), str(query_data[1]), True)
            self.mode = "Listening"
            self.buffer = [None]
            self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)
        
        elif command == 'BlockReminders':
            self.bot.sendMessage(chatId, text='Reminders from patient '+str(" ".join(query_data[2:]))+' will not be received.')
            self.setReminderOptions(str(chatId), str(query_data[1]), False)
            self.mode = "Listening"
            self.buffer = [None]
            self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == "Associate":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient to edit the name:', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            else:
                self.bot.sendMessage(chatId, text='What is the new name?')
                self.buffer[0] = query_data[1]
                self.mode = "Associate Name"

        elif command == "Reminders":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient:', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            else:
                patientName = " ".join(query_data[2:])
                markup = InlineKeyboardMarkup(inline_keyboard=[
                                        [InlineKeyboardButton(text='Yes', callback_data="AllowReminders " + str(query_data[1]) + " " + patientName), 
                                         InlineKeyboardButton(text='No', callback_data="BlockReminders "+ str(query_data[1]) + " " + patientName)]
                                         ])
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Do you wish to receive notifiactions about '+patientName+'?', reply_markup=markup)
                self.mode = "Waiting Inline"

        elif command == "Monitoring":
            devicesList = self.getDevicesList(chatId)
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
            self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == "Check":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            else:
                deviceID = query_data[1]
                chosen = " ".join(query_data[2:])
                statsURL = requests.get(self.catalogURL+"/statsURL").json()
                url = statsURL+'/check/'+str(deviceID)
                stats = requests.get(url).json()
                message = "Patient "+" ".join(query_data[2:])+" status:\n"
                message += '```\n'
                message += 'Metric | Value \n'
                for metric in ['temperature', 'glucose', 'systole', 'diastole',  'saturation']:
                    value = stats[metric]
                    message += metric + f" | {value:.2f}\n"
                message += '```'
                self.bot.sendMessage(chatId, text=message, parse_mode='MarkdownV2')
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == "Stats":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            elif len(query_data) > 1 and query_data[-1] not in ['month', 'week', 'day', 'hour']:
                deviceID = query_data[1]
                chosen = " ".join(query_data[2:])
                time_frame_Keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Hour', callback_data="Stats " + " " +  deviceID + " " + chosen + " hour"), 
                    InlineKeyboardButton(text='Day', callback_data="Stats " + " " +  deviceID + " " + chosen + " day")],
                    [InlineKeyboardButton(text='Week', callback_data="Stats " + " " +  deviceID + " " + chosen + " week"), 
                    InlineKeyboardButton(text='Month', callback_data="Stats " + " " +  deviceID + " " + chosen + " month")]
                        ])
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a time window:', reply_markup=time_frame_Keyboard)
            else:
                statsURL = requests.get(self.catalogURL+"/statsURL").json()
                url = statsURL+'/statistics/'+'/'+str(query_data[1])+'/'+query_data[-1]
                stats = requests.get(url).json()
                metrics = ['temperature', 'glucose', 'diastole', 'systole', 'saturation']
                message = "Patient "+" ".join(query_data[2:-1])+" statistics:\n"
                message += '```\n'
                message += 'Metric | Mean | Std\n'
                for metric in metrics:
                    mean = stats[metric]['mean']
                    std = stats[metric]['std']
                    if mean is None or std is None:
                        message += metric + f" : No data for this time period    \n"
                    else:
                        message += metric + f" | {mean:.2f} | {std:.2f} \n"
                message += '```'
                self.bot.sendMessage(chatId, text=message, parse_mode='MarkdownV2')
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == "History":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            elif len(query_data) > 1 and (query_data[-1] not in ['temperature', 'glucose', 'systole', 'diastole',  'saturation'] and query_data[-1] not in ['month', 'week', 'day', 'hour']):
                deviceID = query_data[1]
                chosen = " ".join(query_data[2:])
                time_frame_Keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Temperature', callback_data="History " + " " +  deviceID + " " + chosen + " temperature")], 
                    [InlineKeyboardButton(text='Glucose', callback_data="History " + " " +  deviceID + " " + chosen + " glucose")],
                    [InlineKeyboardButton(text='Systole', callback_data="History " + " " +  deviceID + " " + chosen + " systole")], 
                    [InlineKeyboardButton(text='Diastole', callback_data="History " + " " +  deviceID + " " + chosen + " diastole")],
                    [InlineKeyboardButton(text='Saturation', callback_data="History " + " " +  deviceID + " " + chosen + " saturation")] 
                        ])
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a metric:', reply_markup=time_frame_Keyboard)
            elif len(query_data) > 1 and query_data[-1] not in ['month', 'week', 'day', 'hour']:
                deviceID = query_data[1]
                chosen = " ".join(query_data[2:])
                metric = query_data[-1]
                time_frame_Keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Hour', callback_data="History " + " " +  deviceID + " " + chosen +  " " + metric + " hour"), 
                    InlineKeyboardButton(text='Day', callback_data="History " + " " +  deviceID + " " + chosen + " " + metric + " day")],
                    [InlineKeyboardButton(text='Week', callback_data="History " + " " +  deviceID + " " + chosen + " " + metric + " week"), 
                    InlineKeyboardButton(text='Month', callback_data="History " + " " +  deviceID + " " + chosen + " " + metric + " month")]
                        ])
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a time window:', reply_markup=time_frame_Keyboard)
            else:
                plotterURL = requests.get(self.catalogURL+"/plotterURL").json()
                url = plotterURL+'/'+str(query_data[1])+'/'+str(query_data[-2])+'/'+str(query_data[-1])
                image = requests.get(url)

                if image.json() == "No data available for this time period":
                    self.bot.sendMessage(chatId, 'No data available for this time period')

                else:
                    image = image.content
                    with open('image.jpg', "wb") as f:
                        f.write(image)
                    self.bot.sendPhoto(chatId, open('image.jpg', 'rb'))
                    os.remove('image.jpg')
                self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == "StopM":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            else:
                    deviceID = query_data[1]
                    patientName = ' '.join(query_data[2:])
                    uri = '/telegramBotChats/'+str(chatId)+'/'+str(deviceID)
                    requests.delete(self.catalogURL + uri)
                    self.bot.sendMessage(chatId, text="Patient "+str(patientName)+' is no longer being monitored.')
                    self.bot.sendMessage(chatId, text="Device "+str(deviceID)+" is no longer connected.")
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'How can I help you?', reply_markup=self.initial_Keyboard_markup)

        elif command == "Schedule":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            elif len(query_data) > 1 and self.buffer[0] == None:
                self.buffer[0] = query_data[1]
                self.buffer.append(" ".join(query_data[2:]))
                self.bot.sendMessage(chatId, text='Please provide the medicine name.')
                self.mode = "Schedule Medicine Name"               
        
        elif command == "Unschedule":
            if len(query_data) == 1:
                devicesList = self.getDevicesList(chatId)
                if len(devicesList) > 0:
                    markup = self.buildPatientsKeyboard(devicesList, query_data[0])
                    self.message_with_inline_keyboard = self.bot.sendMessage(chatId, 'Please choose a patient', reply_markup=markup)
                else: 
                    self.bot.sendMessage(chatId, text='No patient is beeing monitored at the moment.')
            elif len(query_data) > 1 and self.buffer[0] == None:
                self.buffer[0] = query_data[1]
                self.buffer.append(" ".join(query_data[2:]))
                self.bot.sendMessage(chatId, text='Please provide the medicine name.')
                self.mode = "Unschedule Medicine Name"  

        elif command == "Hide":
            self.bot.sendMessage(chatId, text="Hiding options. To open it again simply type something. I am very happy to help.")
            self.mode = "Listening"
   
    def my_on_connect(self, PahoMQTT, obj, flags, rc):
        '''The on_connect is redefined here for this mqtt client because if for some reason
        it disconnected from the broker it would not be suscribed to the topic
        This occured in testing when someone used the check, statistics or history commands of the bot'''
        self.botSubscriber.client.subscribe(self.topic)

    def on_alert(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received
            will be called everytime a message is published on the subscribed topic"""
        message_topic = msg.topic
        deviceID = message_topic.split('/')[1]
        dataMSG = json.loads(msg.payload)
        print(message_topic)
        #print("message recieved from "+deviceID)
        print(dataMSG)
        chatsLists = requests.get(self.catalogURL + '/telegramBotChats').json() 
        chats = []
        names = []
        for chat in chatsLists:
            for device in chat['monitoringDevices']:
                #print(device, deviceID)
                if device['deviceID'] == deviceID and device['allowReminders'] == True:
                    chats.append(chat['chatID'])
                    names.append(device['name'])
        for chatID, name in zip(chats, names):
            if 'disconnection' in message_topic:
                alert = "Disconnection alert: Please check if the device of patient "+name+" is working!"
            else:
                alert = dataMSG['metric'].upper()+" alert: Please check patient "+name+"!"
            self.bot.sendMessage(chatID, text=alert)
        
    def run(self):
        self.botSubscriber.client.connect(self.broker, self.port)
        #self.subscriber.client.subscribe(self.subTopic)
        self.botSubscriber.client.loop_forever()
        #self.botSubscriber.run(self.topic)

if __name__ == '__main__':

    settings = json.load(open("settings.json"))
    token = settings["token"]
    catalogURL = settings["catalogURL"]
    
    bot = TelegramBot(token, catalogURL)
    bot.run()