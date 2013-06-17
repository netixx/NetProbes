'''
Created on 16 juin 2013

@author: francois
'''
from threading import Thread
import time
import argparse
from commanderMessages import Add
import pickle
from consts import Consts
import urllib
from http.client import HTTPConnection

class Interface(object):

    def __init__(self, ip):
        self.targetIp = ip
#         self.setName("Graphical interface")
#         try :
#             self.connection = HTTPConnection(self.targetIp, Consts.COMMANDER_PORT_NUMBER)
#             self.connection.connect()
#         except:
#             pass
        self.probes = []


    def fetchProbes(self):
        return []

    def doCommand(self, command):
        self.updateStatus("Executing command : " + command)
    #     print(command)
        time.sleep(1)
        cmd = Command(Parser(command), self)
#         cmd.start()
#         cmd.join()
        self.updateStatus("Command done...")

    def updateStatus(self, status):
        pass

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

    def __init__(self, parser, interface):
        Thread.__init__(self)
        self.parser = parser
        self.interface = interface

    # does the command
    def run(self):
        command = self.parser.getCommand()
        message = None
        if (command == "add"):
            message = Add(self.parser.getTarget())

        if (message != None):
            # serialize our message
            serializedMessage = pickle.dumps(message, 3)
            # put it in a dictionnary
            params = {Consts.POST_MESSAGE_KEYWORD : serializedMessage}
            # transform dictionnary into string
            params = urllib.parse.urlencode(params, doseq=True, encoding=Consts.POST_MESSAGE_ENCODING)
            # set the header as header for POST
            headers = {"Content-type": "application/x-www-form-urlencoded;charset=" + Consts.POST_MESSAGE_ENCODING, "Accept": "text/plain"}
#             try :
            self.interface.connection.request("POST", "", params, headers)
