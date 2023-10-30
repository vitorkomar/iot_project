import json
import paho.mqtt.client as PahoMQTT

class mqttSubscriber():
    '''wrapper class that is used to subscribe data from the raspberrry pi using mqtt'''
    """Superclass of the data handler (subscriber)
        maybe it would be better to unify both subscriber and publisher into a client class
        but for now I think it is better to make everything work and then deal with this burocracy"""
    def __init__(self, clientId, broker, port):
        self.broker = broker
        self.port = port
        self.clientId = clientId
        self.topic = ''
        self.totalMessages = 0
        self.client = PahoMQTT.Client(clientId, clean_session=True)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic):
        #self.client.connect(self.broker, self.port)
        self.topic = topic
        self.client.subscribe(self.topic, 2)

    def run(self, topic):
        self.client.connect(self.broker, self.port)
        self.subscribe(topic)
        self.client.loop_forever()
        
    def on_connect(self, PahoMQTT, obj, flags, rc):
        print("Connected to broker " + self.broker)

    def on_connect_fail(self, PahoMQTT, obj):
        print("Connect failed")

    def on_message(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received"""
        data = json.loads(msg.payload)
        temp = next((item for item in data["e"] if item["n"] == "temperature"), None)
        acc = next((item for item in data["e"] if item["n"] == "accelerometer"), None)
        glu = next((item for item in data["e"] if item["n"] == "glucose"), None)
        sys = next((item for item in data["e"] if item["n"] == "systole"), None)
        dia = next((item for item in data["e"] if item["n"] == "diastole"), None)
        sat = next((item for item in data["e"] if item["n"] == "saturation"), None)
        time = next((item for item in data["e"] if item["n"] == "time"), None)

        print('TimeStamp:', time['v'])
        print('Temp:', temp['v'])
        print('Acc:', acc['v'])
        print('Glu:', glu['v'])
        print('Systole:', sys['v'])
        print('Diastole:', dia['v'])
        print('Sat:', sat['v'])
        print()

    def on_subscribe(self, PahoMQTT, obj, mid, granted_qos):
        #print("Subscribed: "+str(mid)+" "+str(granted_qos))
        print("subscribed to " + self.topic)