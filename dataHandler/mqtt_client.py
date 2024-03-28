import json
import paho.mqtt.client as PahoMQTT

class mqttPublisher():
    '''wrapper class that is used to publish data from the raspberrry pi using mqtt'''

    def __init__(self, clientId, broker, port):
        self.broker = broker
        self.port = port
        self.clientId = clientId
        self.topic = ''
        self.client = PahoMQTT.Client(clientId, clean_session=True)

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def publish_data(self, topic, msg):
        self.client.publish(topic, json.dumps(msg), 2)




class mqttSubscriber():
    '''wrapper class that is used to subscribe data from the raspberrry pi using mqtt'''
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

    def on_disconnect(self, PahoMQTT, obj, flags, rc):
        print("Disonnected from broker " + self.broker)

    def on_connect_fail(self, PahoMQTT, obj):
        print("Connect failed")

    def on_message(self, PahoMQTT, obj, msg):
        """ Test function to check messages being received"""
        pass #behavior will be defined by each use

    def on_subscribe(self, PahoMQTT, obj, mid, granted_qos):
        #print("Subscribed: "+str(mid)+" "+str(granted_qos))
        print("subscribed to " + self.topic)
