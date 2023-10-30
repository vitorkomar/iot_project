from DataHandler import *
import requests
import numpy as np 
import json
import time

"""Basically run an instance of the data handler 
    there shall be one instance for each patient
    my idea is that it will be running on the wearable as soon as it turns on"""

catalogURL = "http://127.0.0.1:8083"

handler = DataHandler(catalogURL, 'client-'+str(7))
handler.updateSettings()
handler.runAnalysys()

