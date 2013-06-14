'''
Created on 13 juin 2013

@author: francois
'''
from threading import Thread
import argparse


'''
    Parses a command from user input into
'''
class Parser(object):

    def __init__(self, command):
        pass


class Command(Thread):
    
    def __init__(self, parser):
        Thread.__init__(self)
        self.parser = parser
    
    # does the command
    def run(self):
        pass
