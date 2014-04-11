'''
Created on 7 juin 2013

@author: francois
'''
__all__ = ['Consts', 'Params']

class Params(object):
    DEBUG = True

def debug(message):
    if (Params.DEBUG):
        print(message)
