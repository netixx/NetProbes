'''
Codec = Encoder + decoder
Translate python Message instances into a String/bytes
to be send accross the network by the protocols.* modules

@author: francois
'''

import pickle
_ENCODING = 'latin1'

'''Encode message to send on the network by serialization'''
def encode(message):
    return pickle.dumps(message, 3)


'''Decode message received with serialisation'''
def decode(message):
    return pickle.loads(message)



