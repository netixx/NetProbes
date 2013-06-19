'''
Created on 16 juin 2013

@author: francois
'''
from threading import Thread
import time
import shlex
from commanderMessages import Add, Do
import pickle
from consts import Consts
import urllib
from http.client import HTTPConnection
from probedisp import Probe
from exceptions import NoSuchCommand
import argparse

class Interface(object):
    targetIp = "127.0.0.1"
    
    def __init__(self, ip):
        self.targetIp = ip
#         self.setName("Graphical interface")
        try :
            self.connection = HTTPConnection(self.targetIp, Consts.COMMANDER_PORT_NUMBER)
            self.connection.connect()
        except:
            pass

    def fetchProbes(self):
        self.connection.request("GET", "probes", "", {})
        response = self.connection.getresponse()
        pi = response.read(int(response.getheader('content-length')))
        return pickle.loads(pi)
#         return [Probe("id", "10.0.0.2"), Probe("id 2", "10.0.0.2")]

    def doCommand(self, command):
        self.updateStatus("Executing command : " + command)
        time.sleep(1)
        try:
            cmd = Command(Parser(command), self)
            cmd.start()
            cmd.join()
            self.updateStatus("Command done...")
        except (ValueError, NoSuchCommand):
            self.updateStatus("Command is false or unkown")


    def updateStatus(self, status):
        pass

'''
    Parses a command from user input into
'''
    # todo : refactor
class Parser(object):

    def __init__(self, command):
        self.command = None
        args = argparse.ArgumentParser(description="Parses the user command")
        args.add_argument('-t', '--target-probe', metavar='target-ip', help="Ip of the target", default=Interface.targetIp)
        subp = args.add_subparsers()
        subp1 = subp.add_parser('add')
        subp1.add_argument('ip', metavar='ip',
                    help='The ip you want to add')
        subp1.set_defaults(func=self.setAdd)

        subp2 = subp.add_parser('do')
        subp2.add_argument('test', metavar='test',
                    help='The message you want to send to the probe')
        subp2.set_defaults(func=self.setDo)
        self.aCommand = args.parse_args(shlex.split(command))
        self.errors = args.format_usage()
#         if (len(self.aCommand) < 2):
#             raise ValueError("The argument supplied must at least have 2 words")

    def getCommand(self):
        return self.command

    def getTarget(self):
        return self.aCommand.target_probe

    def getParams(self):
        return self.aCommand

    def getErrors(self):
        return self.errors

    def setAdd(self):
        self.command = "add"

    def setDo(self):
        self.command = "do"

class Command(Thread):

    def __init__(self, parser, interface):
        Thread.__init__(self)
        self.parser = parser
        self.interface = interface

    # does the command
    def run(self):
        command = self.parser.getCommand()
        message = None
        # todo : refactor
        if (command == "add"):
            message = Add(self.parser.getTarget())
        
        if (command == "do"):
            message = Do(self.parser.getTarget(), self.parser.getParams().test)

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
            self.interface.connection.getResponse()
        else:
            raise NoSuchCommand()
