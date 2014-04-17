'''
Generic protocol class (autocompletion mainly)
A protocol is a set of method to send and receive data and create connection
between probes

@author: francois
'''
from threading import Thread


def createConnection(probe):
    '''Create connection object to remote probe given probe Object'''
    pass


def connect(connection):
    '''Connect to remote host given connection (created by createConnection)
    @see: createConnection

    '''
    pass


def disconnect(connection):
    '''Close connection to remote probe
    @see: createConnection

    '''
    pass


def getRemoteId(probeIp):
    '''Get the remote ID of the probe with probeIp'''
    pass


class Sender(object):
    '''Class to send data across network'''

    def send(self, message):
        pass


class Listener(Thread):
    '''Class to listend for data on the network'''
    pass
