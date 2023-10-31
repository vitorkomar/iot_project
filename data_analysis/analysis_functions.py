import pandas as pd

def calculate_mean(device, metric,n_samples):
    '''calculates the mean for the specified device and metric for the number of the last n_samples'''
    df = pd.read_csv('database.csv')
    device = int(device) #just to make sure the device is an integer
    df = df[(df['device_id']==device) & (df['n']==metric)]
    df = df.tail(n_samples)
    return df['v'].mean()

def calculate_max(device, metric,n_samples):
    '''calculates the mean for the specified device and metric for the number of the last n_samples'''
    df = pd.read_csv('database.csv')
    device = int(device) #just to make sure the device is an integer
    df = df[(df['device_id']==device) & (df['n']==metric)]
    df = df.tail(n_samples)
    return df['v'].max()

def calculate_min(device, metric,n_samples):
    '''calculates the mean for the specified device and metric for the number of the last n_samples'''
    df = pd.read_csv('database.csv')
    device = int(device) #just to make sure the device is an integer
    df = df[(df['device_id']==device) & (df['n']==metric)]
    df = df.tail(n_samples)
    return df['v'].min()

def calculate_std(device, metric,n_samples):
    '''calculates the mean for the specified device and metric for the number of the last n_samples'''
    df = pd.read_csv('database.csv')
    device = int(device) #just to make sure the device is an integer
    df = df[(df['device_id']==device) & (df['n']==metric)]
    df = df.tail(n_samples)
    return df['v'].std()