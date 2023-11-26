import json
import paho.mqtt.client as PahoMQTT

class mqttPublisher():
    '''wrapper class that is used to publish data from the raspberrry pi using mqtt'''
    """ maybe it would be better to unify both subscriber and publisher into a client class
        but for now I think it is better to make everything work and then deal with this burocracy"""
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
        print('Published on topic:', topic)
        self.client.publish(topic, json.dumps(msg), 2)


class mqttSubscriber():
    '''wrapper class that is used to subscribe data from the raspberrry pi using mqtt'''
    """Different subscriber then the one used on the data handler but a first try put both classes together """
    def __init__(self, clientId, broker, port):
        self.broker = broker
        self.port = port
        self.clientId = clientId
        self.topic = ''
        self.client = PahoMQTT.Client(clientId, clean_session=True)
        self.client.on_message = self.on_message

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic):
        self.client.connect(self.broker, self.port)
        self.topic = topic
        self.client.subscribe(self.topic, 2)

    def on_message(self, client, userdata, msg):
        pass