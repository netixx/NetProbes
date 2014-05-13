"""Generic protocol class (auto-completion mainly)
A protocol is a set of method to send and receive data and create connection
between probes

@author: francois
"""
from threading import Thread


def createConnection(probe):
    """Create connection object to remote probe given Probe Object
    :param probe: Probe to create the connection for"""
    pass


def connect(connection):
    """Connect to remote host given connection (created by createConnection)
    :param connection : Connection to connect
    """
    pass


def disconnect(connection):
    """Close connection to remote probe
    :param connection : connection to close

    """
    pass


def getRemoteId(probeIp):
    """Get the remote ID of the probe with probeIp
    :param probeIp : the Ip of the probe to query"""
    pass


class Sender(object):
    """Class to send data across network"""

    def send(self, message):
        """Send a message across
        :param message : message to send across
        """
        pass


class Listener(Thread):
    """Class to listen for data on the network"""
    pass
