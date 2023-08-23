from mqtt_client import *
import time
import json
from DataGenerator import *
import random
import requests

conf = json.load(open("settings.json"))
topic = conf["baseTopic"]
broker = conf["broker"]
port = conf["port"]
isNew = conf["isNew"]
Id = conf["id"]

if isNew:
    data = requests.get("http://localhost:8080/publisher")
    data = data.json()
    broker = data['brokerAddress']
    topic = data['baseTopic']+'/'+str(Id)

    conf.update(data)
    conf['isNew'] = False
    with open("settings.json", "w") as file:
        json.dump(conf, file, indent = 4)


publisher = mqttPublisher(Id, broker, port)
publisher.start()

tempGenerator = DataGenerator(36.6, 0.05)
accGenerator = DataGenerator(1, 0)
glucGenerator = DataGenerator(99, 0.85)
systoleGenerator = DataGenerator(124.6, 1.82)
diastoleGenerator = DataGenerator(77.7, 0.94)
satGenerator = DataGenerator(97.7, 1.02)

    
    

while True:
    time.sleep(1)

    # Create the SenML data in JSON format
    data = {
        "bn": "urn:dev:ow:10e2073a01080063",
        "e": [
            {
                "n": "temperature",
                "u": "celsius",
                "v": tempGenerator.drawSample()
            },
            {
                "n": "accelerometer",
                "u": "m/s2",
                "v": accGenerator.drawSample()
            },
            {
                "n": "glucose",
                "u": "mg/dl",
                "v": glucGenerator.drawSample()
            },
            {
                "n": "systole",
                "u": "mmHg",
                "v": systoleGenerator.drawSample()
            },
            {
                "n": "diastole",
                "u": "mmHg",
                "v": diastoleGenerator.drawSample()
            },
            {
                "n": "saturation",
                "u": "%",
                "v": satGenerator.drawSample()
            }
        ]
    }

    publisher.publish_data(topic, data)
    
publisher.disconnect()
    