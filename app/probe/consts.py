'''
Module gathering the constants of the probe

@author: francois
'''

class Consts:
    '''
    The 'real' consts
    '''

    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000


class Params:
    '''
    Parameters for the runtime
    '''
    DEBUG = True
    COMMANDER = True

class Identification:
    '''
    Identification elements of the probe
    '''
    PROBE_ID = "1122334455667788"


def debug(message):
    if (Params.DEBUG):
        print(message)
