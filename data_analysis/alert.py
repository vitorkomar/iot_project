import json 
import requests
import numpy as np
import pandas as pd


class Alert():
    '''class that will manage the alerts sent to the telegram bot
    the alerts are sent based on a moving average, i.e., if the mean of the 
    last n_samples is larger or smaller than a thresold, than an alert will be sent'''

    def __init__(self, thresholds, samples, alert_url, database_path):
        self.thresholds = thresholds #a dictionary of thresholds, where each thereshold is a tuple with the min and max values for that metric
        self.samples = samples #cotains how many samples to use per metric type
        self.alert_url = alert_url #base url for the rest server that will receive the requests
        self.database_path = database_path

    def compute_metric(self, device, metric):
        if metric == 'temperature':

            threshold = self.thresholds[metric]
            n_samples = self.samples[metric]
            df = pd.read_csv(self.database_path)
            device = int(device)
            df = df[(df['device_id']==device) & (df['n']==metric)]
            df = df.tail(n_samples)
            values = df['v']
            mean = np.mean(values)

            if mean < threshold[0] or mean > threshold[1]:
                self.send_alert(device, metric)
                print('alert sent')
            else:
                pass

    def send_alert(self, device, metric):

        url = self.alert_url + '/alert/' + str(device) + '/' + metric
        requests.get(url) #sending alert to telegram bot