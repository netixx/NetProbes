'''
Created on 11 avr. 2014

@author: francois
'''
from threading import Thread

def createConnection(probe):
    pass

def connect(connection):
    pass

def disconnect(connection):
    pass

class Listener(Thread):

    def __init__(self, helper):
        pass


class Sender(object):

    def send(self, connection, message):
        pass

    def requestProbes(self, connection):
        pass

    def requestResults(self, connection):
        pass
