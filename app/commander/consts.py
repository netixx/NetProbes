'''
Created on 7 juin 2013

@author: francois
'''

class Consts:

    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000

class Params:
    DEBUG = True

def debug(message):
    if (Params.DEBUG):
        print(message)
