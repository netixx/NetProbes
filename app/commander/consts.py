'''
Created on 7 juin 2013

@author: francois
'''
__all__ = ['Consts', 'Params']

class Consts(object):

    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000

class Params(object):
    DEBUG = True

def debug(message):
    if (Params.DEBUG):
        print(message)
