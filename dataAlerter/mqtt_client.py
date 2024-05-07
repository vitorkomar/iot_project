import json
import paho.mqtt.client as PahoMQTT

class mqttPublisher():
    """ Wrapper class that is used to publish data using mqtt
    """
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
        print(f"Published on topic: {topic}")
        self.client.publish(topic, json.dumps(msg), 2)

class mqttSubscriber():
    """ Wrapper class that is used to received data drom subscribed topics using mqtt
    """
    def __init__(self, clientId, broker, port):
        self.broker = broker
        self.port = port
        self.clientId = clientId
        self.topic = ''
        self.totalMessages = 0
        self.client = PahoMQTT.Client(clientId, clean_session=True)
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic):
        self.topic = topic
        self.client.subscribe(self.topic, 2)

    def run(self, topic):
        self.client.connect(self.broker, self.port)
        self.subscribe(topic)
        self.client.loop_forever()
        
    def on_disconnect(self, PahoMQTT, obj, flags, rc):
        print("Disonnected from broker " + self.broker)

    def on_subscribe(self, PahoMQTT, obj, mid, granted_qos):
        print("Subscribed to " + self.topic)
