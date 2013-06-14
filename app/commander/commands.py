'''
Created on 13 juin 2013

@author: francois
'''
from threading import Thread
import argparse
from commanderMessages import Add
import pickle
from consts import Consts
import urllib

'''
    Parses a command from user input into
'''
class Parser(object):

    def __init__(self, command):
        self.aCommand = command.split()

    def getCommand(self):
        return self.aCommand[0]
    
    def getTarget(self):
        return self.aCommand[1]
    
    def getParams(self):
        if (len(self.aCommand) > 2):
            return self.aCommand[2:]
        

class Command(Thread):
    
    def __init__(self, parser, cli):
        Thread.__init__(self)
        self.parser = parser
        self.cli = cli
    
    # does the command
    def run(self):
        command = self.parser.getCommand()
        if (command == "add"):
            message = Add(self.parser.getTarget())
            
        if (message != None):
            #serialize our message
            serializedMessage = pickle.dumps( message, 3)
            #put it in a dictionnary
            params = {Consts.POST_MESSAGE_KEYWORD : serializedMessage}
            #transform dictionnary into string
            params = urllib.parse.urlencode(params, doseq = True, encoding=Consts.POST_MESSAGE_ENCODING)
            #set the header as header for POST
            headers = {"Content-type": "application/x-www-form-urlencoded;charset="+ Consts.POST_MESSAGE_ENCODING, "Accept": "text/plain"}
#             try :
            self.cli.connection.request("POST", "", params, headers)
