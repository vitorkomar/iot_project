from DataStorer import *
import json

"""Basically run an instance of the data storer 
    there shall be one instance for each patient
    my idea is that it will be running on the wearable as soon as it turns on"""

catalogURL = "http://127.0.0.1:8084"
#catalogURL = "http://192.168.11.238:8083"

storer = DataStorer(catalogURL, 10)
storer.updateSettings()
storer.run()

