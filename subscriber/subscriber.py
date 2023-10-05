from mqtt_subscriber import *
import requests
import numpy as np 
import json
import time

conf = json.load(open("subscriber\settings.json"))
topic = conf["baseTopic"]
broker = conf["brokerAddress"]
port = conf["port"]
isNew = conf["isNew"]
Id = conf["id"]
catalogURL = conf['catalogURL']

subscriber = mqttSubscriber("client-"+str(Id), broker, port)
subscriber.run(topic)

