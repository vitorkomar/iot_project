import json
import paho.mqtt.client as PahoMQTT

class mqttPublisher():
    """ Wrapper class that is used to publish simulated data using mqtt
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
        self.client.publish(topic, json.dumps(msg), 2)
