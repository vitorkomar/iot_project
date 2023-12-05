from mqtt_client import *
import time
import json
from DataGenerator import *
import random
import requests

#conf = json.load(open("settings.json"))
conf = json.load(open("publisher/settings.json"))
topic = conf["baseTopic"]
broker = conf["brokerAddress"]
port = conf["port"]
isNew = conf["isNew"]
Id = conf["id"]
catalogURL = conf['catalogURL']

if isNew:
    print(catalogURL+'/publisher')
    data = requests.get(catalogURL+'/publisher')
    data = data.json()
    broker = data['brokerAddress']
    topic = data['baseTopic']+'/'+str(Id)

    conf.update(data)
    conf['isNew'] = False
    with open("settings.json", "w") as file:
        json.dump(conf, file, indent = 4)

    postData = dict()
    postData[str(str(Id))] = {"topic": topic}
    requests.post(catalogURL, json=postData)

fs = np.array([600,3600,3600,3600,3600,3600])

tempGenerator = DataGenerator(36.6, 0.05, fs[0]) # one sample every 10 min
accGenerator = DataGenerator(1, 0, fs[1]) # one sample every ? min
glucGenerator = DataGenerator(99, 0.85, fs[2]) # one sample every 60 min
systoleGenerator = DataGenerator(124.6, 1.82, fs[3]) # one sample every 60 min
diastoleGenerator = DataGenerator(77.7, 0.94, fs[4]) # one sample every 60 min
satGenerator = DataGenerator(97.7, 1.02, fs[5]) # one sample every 60 min 

publisher = mqttPublisher(str(Id), broker, port)
publisher.start()

timeCounter = 0
while True:
    if (timeCounter%fs==0).any():
        # Create the SenML data in JSON format
        data = {
            "bn": "urn:dev:ow:10e2073a01080063",
            "e": [
                {
                    "n": "temperature",
                    "u": "celsius",
                    "v": tempGenerator.drawSample(timeCounter)
                },
                {
                    "n": "accelerometer",
                    "u": "m/s2",
                    "v": accGenerator.drawSample(timeCounter)
                },
                {
                    "n": "glucose",
                    "u": "mg/dl",
                    "v": glucGenerator.drawSample(timeCounter)
                },
                {
                    "n": "systole",
                    "u": "mmHg",
                    "v": systoleGenerator.drawSample(timeCounter)
                },
                {
                    "n": "diastole",
                    "u": "mmHg",
                    "v": diastoleGenerator.drawSample(timeCounter)
                },
                {
                    "n": "saturation",
                    "u": "%",
                    "v": satGenerator.drawSample(timeCounter)
                }
            ]
        }
        print(timeCounter)
        publisher.publish_data(topic, data)
    
    time.sleep(1)
    timeCounter += 1
    if timeCounter == 3600:
        timeCounter = 0
    
publisher.disconnect()
    
