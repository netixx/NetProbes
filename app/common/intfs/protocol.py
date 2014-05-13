"""Protocol interface
A protocol is in charge of sending data across the network
It uses the codec to transform objects into bytes and interacts with
the server through the helper instance given by the server

@author: francois
"""
from threading import Thread


def createConnection(probe):
    """Create a connection object for this probe
    :param probe : the probe to create the connection for
    """
    pass


def connect(connection):
    """Connection this connection
    :param connection : connection to connect
    """
    pass


def disconnect(connection):
    """Close this connection
    :param connection : connection to close
    """
    pass


def getRemoteId(ip):
    """Get the id of the probe with ip
    :param ip : ip of the probe to query
    """
    pass


class Listener(Thread):
    """Listen for incoming connections
    Uses the helper to access probe specific services
    """

    def __init__(self, helper):
        pass

    def close(self):
        pass


class Sender(object):
    """Object to send data across the network"""

    @staticmethod
    def send(cls, connection, message):
        """Method to send data
        :param connection: connection to use
        :param message: message to send"""
        pass

    @staticmethod
    def requestProbes(cls, connection):
        """Method to request the list of probes
        :param connection : connection to request the probe on
        """
        pass

    @staticmethod
    def requestResults(cls, connection):
        """Method to request results of a test
        :param connection : connection to request the results on
        """
        pass
