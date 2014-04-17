"""
Codec = Coder + Decoder

The interface is very simple, two methods are required : encode and decode
encode transforms a CommanderMessage object into bytes
decode transforms bytes into CommanderMessage object

@author: francois
"""


def encode(message):
    """Transform CommanderMessage object to bytes
    :param message : CommanderMessage to transform
    """
    pass


def decode(message):
    """Transform bytes into Commander message instance
    :param message : bytes to decode
    """
    pass
