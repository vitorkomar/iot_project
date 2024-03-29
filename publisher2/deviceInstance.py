from TrackingDevice import *
import time

"""Basically run an instance of the wearable (sensors on the elderly monitor device)
    there shall be one instance for each patient
    my idea is that it will be running on the wearable as soon as it turns on"""

time.sleep(60*2)

catalogURL = json.load(open("deviceSettings.json"))["catalogURL"]

device = TrackingDevice(catalogURL)

device.updateCatalog()
device.updateSettings()
device.run()
