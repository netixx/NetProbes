'''
Created on 15 avr. 2014

@author: francois
'''
import pickle
import zlib

_ENCODING = 'latin1'
_LEVEL = 6

'''Encode message to send on the network by serialization'''


def encode(message):
    o = pickle.dumps(message, 3)
    r = zlib.compress(o, _LEVEL)
    return r


'''Decode message received with serialisation'''


def decode(message):
    return pickle.loads(zlib.decompress(message))
