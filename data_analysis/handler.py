from data_handler import *
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

handler = DataHandler("client-"+str(Id), broker, port)
handler.run(topic)

