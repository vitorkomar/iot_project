from TrackingDevice import *

catalogURL = "http://127.0.0.1:8083"

device = TrackingDevice(catalogURL)

device.updateCatalog()
device.updateSettings()
device.run()