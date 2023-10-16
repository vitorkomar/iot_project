from DataHandler import *
import requests
import numpy as np 
import json
import time


catalogURL = "http://127.0.0.1:8083"

handler = DataHandler(catalogURL, 'client-'+str(7))
handler.updateSettings()
handler.runAnalysys()

