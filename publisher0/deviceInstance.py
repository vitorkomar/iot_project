from TrackingDevice import *

"""Basically run an instance of the wearable (sensors on the elderly monitor device)
    there shall be one instance for each patient
    my idea is that it will be running on the wearable as soon as it turns on"""

catalogURL = "http://127.0.0.1:8084"

device = TrackingDevice(catalogURL)

device.updateCatalog()
device.updateSettings()
device.run()
