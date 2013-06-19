'''
Created on 16 juin 2013

@author: francois
'''
from threading import Thread
import time
import shlex
from commanderMessages import Add, Do, Delete
import pickle
from consts import Consts
import urllib
from http.client import HTTPConnection
from probedisp import Probe
from exceptions import NoSuchCommand
import argparse
from threading import Event

class Interface(object):
    targetIp = "127.0.0.1"
    PROBE_REFRESH_TIME = 10
    def __init__(self, ip):
        self.targetIp = ip
        self.isRunning = True
        self.fetchTrigger = Event()
#         self.setName("Graphical interface")
        try :
            self.connection = HTTPConnection(self.targetIp, Consts.COMMANDER_PORT_NUMBER)
            self.connection.connect()
        except:
            pass

    def fetchProbes(self):
        self.connection.request("GET", "/probes", "", {})
        response = self.connection.getresponse()
        pi = response.read(int(response.getheader('content-length')))
        return pickle.loads(pi)
#         return [Probe("id", "10.0.0.2"), Probe("id 2", "10.0.0.2")]

    def doCommand(self, command):
        self.updateStatus("Executing command : " + command)
        time.sleep(0.5)
        try:
            cmd = Command(Parser(command), self)
            cmd.start()
            cmd.join()
            self.updateStatus("Command done...")
        except (ValueError, NoSuchCommand):
            self.updateStatus("Command is false or unkown")


    def triggerUpdater(self):
        while(self.isRunning):
            self.fetchTrigger.set()
            time.sleep(self.PROBE_REFRESH_TIME)

    def triggerFetch(self):
        self.fetchTrigger.set()

    def updateStatus(self, status):
        pass

'''
    Parses a command from user input into
'''
class Parser(object):

    def __init__(self, command):
        self.command = None
        args = argparse.ArgumentParser(description="Parses the user command")
        args.add_argument('-t', '--target-probe', metavar='target-ip', help="Ip of the target", default=Interface.targetIp)
        subp = args.add_subparsers(dest='subparser_name')
        subp1 = subp.add_parser('add')
        subp1.add_argument('ip', metavar='ip',
                    help='The ip you want to add')
        subp1.set_defaults(func=self.setAdd)

        subp2 = subp.add_parser('do')
        subp2.add_argument('test', metavar='test',
                    help='The message you want to send to the probe')
        subp2.set_defaults(func=self.setDo)

        subp3 = subp.add_parser('remove')
        subp3.add_argument('id', metavar='id',
                    help='The id of the probe you wish to remove')
        subp3.set_defaults(func=self.setRemove)
        self.aCommand = args.parse_args(shlex.split(command))
        self.aCommand.func()
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

    def setRemove(self):
        self.command = "remove"


class Command(Thread):

    def __init__(self, parser, interface):
        Thread.__init__(self)
        self.parser = parser
        self.interface = interface
        self.setName('Command')

    # does the command
    def run(self):
        command = self.parser.getCommand()
        message = None
        if (command == "add"):
            message = Add(self.parser.aCommand.ip)
        
        if (command == "do"):
            message = Do(self.parser.getTarget(), self.parser.getParams().test)
        
        if (command == "remove"):
            message = Delete(self.parser.getParams().id)

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
            self.interface.connection.getresponse()
        else:
            raise NoSuchCommand()
