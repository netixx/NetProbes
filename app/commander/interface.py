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
from http.client import CannotSendRequest

class Interface(object):
    targetIp = "127.0.0.1"
    PROBE_REFRESH_TIME = 10
    RESULTS_REFRESH_TIME = 10

    def __init__(self, ip):
        self.targetIp = ip
        self.isRunning = True
        self.doFetchProbes = Event()
        self.doFetchResults = Event()
#         self.setName("Graphical interface")
        try :
            self.connection = HTTPConnection(self.targetIp, Consts.COMMANDER_PORT_NUMBER)
            self.connection.connect()
        except:
            self.updateStatus("Connection to probe impossible, commands cannot be executed")
            raise

        try:
            self.connectionProbes = HTTPConnection(self.targetIp, Consts.COMMANDER_PORT_NUMBER)
            self.connectionProbes.connect()
        except:
            raise

        try :
            self.connectionResults = HTTPConnection(self.targetIp, Consts.COMMANDER_PORT_NUMBER)
            self.connectionResults.connect()
        except:
            self.addResult("Connection to the probe impossible, results cannot be fetched")
            raise

    def doCommand(self, command):
        self.updateStatus("Executing command : " + command)
        time.sleep(0.3)
        try:
            cmd = Command(Parser(command), self)
            cmd.start()
            cmd.join()
            time.sleep(0.3)
            self.triggerFetchProbes()
            self.updateStatus("Command done...")
        except (ValueError, NoSuchCommand):
            pass
#       self.updateStatus("Command is false or unkown")

    def updateProbes(self):
        pass

    def updateResults(self):
        pass

    def probeFetcherScheduler(self):
        while(self.isRunning):
            self.triggerFetchProbes()
            time.sleep(self.PROBE_REFRESH_TIME)

    def triggerFetchProbes(self):
        self.doFetchProbes.set()

    def resultFetcherScheduler(self):
        while(self.isRunning):
            self.triggerFetchResult()
            time.sleep(self.RESULTS_REFRESH_TIME)

    def triggerFetchResult(self):
        self.doFetchResults.set()

    def fetchProbes(self):
        self.doFetchProbes.clear()
        self.connectionProbes.request("GET", "/probes", "", {})
        response = self.connectionProbes.getresponse()
        pi = response.read(int(response.getheader('content-length')))
        return pickle.loads(pi)
#         return [Probe("id", "10.0.0.2"), Probe("id 2", "10.0.0.2")]

    def fetchResults(self):
        self.doFetchResults.clear()
        self.connectionResults.request("GET", "/results", "", {})
        response = self.connectionResults.getresponse()
        return response.read(int(response.getheader('content-length'))).decode()


    def updateStatus(self, status):
        pass
    
    def addResult(self, result):
        pass

    def quit(self):
        self.connection.close()
        self.connectionProbes.close()
        self.connectionResults.close()

'''
    Parses a command from user input into a commanderMessage
'''
class Parser(object):

    def __init__(self, command):
        self.message = None
        self.errors = None
        args = argparse.ArgumentParser(description="Parses the user command")
        args.add_argument('-t', '--target-probe', metavar='target-ip', help="Ip of the target", default=Interface.targetIp)
        subp = args.add_subparsers(dest='subparser_name')

        # parser for the add command
        subp1 = subp.add_parser('add')
        subp1.add_argument('ip', metavar='ip',
                    help='The ip you want to add')
        subp1.set_defaults(func=self.setAdd)

        # parser for the do command
        subp2 = subp.add_parser('do')
        subp2.add_argument('test', metavar='test',
                    help='The message you want to send to the probe')
        subp2.add_argument('options', nargs=argparse.REMAINDER)
        subp2.set_defaults(func=self.setDo)

        # parse for the remove command
        subp3 = subp.add_parser('remove')
        subp3.add_argument('id', metavar='id',
                    help='The id of the probe you wish to remove')
        subp3.set_defaults(func=self.setRemove)
        

        try:
            self.command = args.parse_args(shlex.split(command))
            self.command.func()
        except (argparse.ArgumentError, SystemExit):
            self.errors = args.format_usage()
#         if (len(self.aCommand) < 2):
#             raise ValueError("The argument supplied must at least have 2 words")

    def getParams(self):
        return self.command

    def getErrors(self):
        return self.errors

    def setAdd(self):
        self.message = Add(self.command.ip)

    def setDo(self):
        self.message = Do(self.command.target_probe, self.command.test, self.command.options)

    def setRemove(self):
        self.message = Delete(self.command.id)

    def getMessage(self):
        return self.message

'''
    Runs the command of the user (in a new Thread)
'''
class Command(Thread):

    def __init__(self, parser, interface):
        Thread.__init__(self)
        self.interface = interface
        self.parser = parser
        if (parser.getErrors() != None):
            self.interface.updateStatus(self.parser.errors)
            raise NoSuchCommand()

        self.setName('Command')

    # does the command
    def run(self):
        message = self.parser.getMessage()
        if (message != None):
            tryAgain = True
            while(tryAgain):
                # serialize our message
                serializedMessage = pickle.dumps(message, 3)
                # put it in a dictionnary
                params = {Consts.POST_MESSAGE_KEYWORD : serializedMessage}
                # transform dictionnary into string
                params = urllib.parse.urlencode(params, doseq=True, encoding=Consts.POST_MESSAGE_ENCODING)
                # set the header as header for POST
                headers = {"Content-type": "application/x-www-form-urlencoded;charset=" + Consts.POST_MESSAGE_ENCODING, "Accept": "text/plain"}
                try :
                    self.interface.connection.request("POST", "", params, headers)
                    self.interface.connection.getresponse()
                    tryAgain = False
                except CannotSendRequest:
                    # retry later
                    tryAgain = True
                    time.sleep(2)
        else:
            raise NoSuchCommand()
