"""
Basic serialize codec
Uses the pickle python module to transform objects into bytes

@author: francois
"""

import pickle

_ENCODING = 'latin1'


def encode(message):
    """Pickle the Message instance and returns it
    :param message : Message to pickle
    """
    return pickle.dumps(message, 3)


def decode(message):
    """Unpickle the bytes
    :param message : bytes to unpickle
    """
    return pickle.loads(message)
