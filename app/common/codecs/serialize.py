'''
Created on 9 avr. 2014

@author: francois
'''

import pickle

_ENCODING = 'latin1'


def encode(message):
    return pickle.dumps(message, 3)


def decode(message):
    return pickle.loads(message)
