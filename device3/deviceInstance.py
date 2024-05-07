from TrackingDevice import TrackingDevice
import json

""" Run an instance of the wearable device there shall be one instance for each patient
    The wearable device contains the mqtt publisher and all simulated sensors 
"""

catalogURL = json.load(open("deviceSettings.json"))["catalogURL"]

device = TrackingDevice(catalogURL)

device.updateCatalog()
device.updateSettings()
device.run()
device.removeFromCatalog()