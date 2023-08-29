from mqtt_client import *
import requests
import numpy as np 
import json
import time

def send_fever_alert(patientId):
    requests.get("http://localhost:8099/fever_alert/"+str(patientId))

def send_fever_alert(patientId):
    requests.get("http://localhost:8099/fall_alert/"+str(patientId))
