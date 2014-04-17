"""
Codec that uses pickle combined with zlib deflate algorithm
to send data across

@author: francois
"""
import pickle
import zlib

_ENCODING = 'latin1'
_LEVEL = 6

'''Encode message to send on the network by serialization'''


def encode(message):
    """Encode the given message with pickle and zlib
    :type message: Message instance to encode
    :param message: the message to send"""
    o = pickle.dumps(message, 3)
    r = zlib.compress(o, _LEVEL)
    return r


'''Decode message received with serialisation'''


def decode(message):
    """Decode message string into Message Object
    :param message: the message bytes to decode"""
    return pickle.loads(zlib.decompress(message))
