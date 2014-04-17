"""
Generic class/interface for codecs
A codec is a way of translating Message to bytes and
vice-versa

@author: francois
"""


def encode(message):
    """Encode message instance before sending it on the network
    Should return bytes to be decoded at the other end
    :param message : Message instance to encode to bytes
    """

    pass


def decode(message):
    """Decode bytes received from remote probe
    Should return Message instance
    :param message : bytes to convert to Message object
    """

    pass

