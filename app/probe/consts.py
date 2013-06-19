'''
Created on 7 juin 2013

@author: francois
'''

class Consts:
    '''
    classdocs
    '''

    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000


class Params:
    DEBUG = True
    COMMANDER = True

class Identification:
    PROBE_ID = "1122334455667788"


def debug(message):
    if (Params.DEBUG):
        print(message)
