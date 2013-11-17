'''
Module gathering the constants of the probe

@author: francois
'''

class Consts(object):
    '''
    The 'real' consts
    '''

    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000
    PROPAGATION_RATE = 5

class Params(object):
    '''
    Parameters for the runtime
    '''
    DEBUG = False
    COMMANDER = False


class Identification(object):
    '''
    Identification elements of the probe
    '''
    PROBE_ID = "1122334455667788"
