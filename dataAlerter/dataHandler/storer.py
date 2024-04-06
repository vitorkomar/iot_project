from DataStorer import DataStorer
import json
import requests

"""Basically run an instance of the data storer 
    there shall be one instance for each patient
    my idea is that it will be running on the wearable as soon as it turns on"""

catalogURL = json.load(open("settings.json"))["catalogURL"]

storer = DataStorer(catalogURL, 10)
storer.run()

