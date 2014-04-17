"""
Uses simple Pickle module for python to serialize objects
into strings

@author: francois
"""

import pickle

_ENCODING = 'latin1'


def encode(message):
    """Encode the given message by pickling
    :param message: Message instance to encode
    """
    return pickle.dumps(message, 3)



def decode(message):
    """Decode message received with serialisation
    :param message: bytes to decode
    """
    return pickle.loads(message)



