'''
Created on 16 juin 2013

@author: francois
'''
from threading import Thread, Event

import time, shlex, argparse

from common.commanderMessages import Add, Do, Delete
from exceptions import ProbeConnectionFailed, NoSuchCommand
from common.consts import Params as cParams

class Interface(object):
    targetIp = "127.0.0.1"
    targetId = None
    PROBE_REFRESH_TIME = 10
    RESULTS_REFRESH_TIME = 10

    def __init__(self, ip):
        self.targetIp = ip
        self.targetId = self.getTargetId(ip)
        self.isRunning = True
        self.doFetchProbes = Event()
        self.doFetchResults = Event()
        try :
            self.connection = cParams.PROTOCOL.createConnection(self.targetIp)
            cParams.PROTOCOL.connect(self.connection)
            self.connectionProbes = cParams.PROTOCOL.createConnection(self.targetIp)
            cParams.PROTOCOL.connect(self.connectionProbes)
            self.connectionResults = cParams.PROTOCOL.createConnection(self.targetIp)
            cParams.PROTOCOL.connect(self.connectionResults)
        except ProbeConnectionFailed as e:
            raise ProbeConnectionFailed("Error while attempting to perform an HTTP request to the probe %s" % self.targetIp)
        except ConnectionRefusedError:
            raise ProbeConnectionFailed("Error while connecting to probe : connection refused")

    def doCommand(self, command):
        self.updateStatus("Executing command : " + command)
        time.sleep(0.3)
        try:
            cmd = Command(Parser(command, self), self)
            cmd.start()
#             cmd.join()
        except (ValueError, NoSuchCommand):
            pass
#       self.updateStatus("Command is false or unkown")
    
    @staticmethod
    def getTargetId(ip):
        return cParams.PROTOCOL.getRemoteId(ip)

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
        return cParams.PROTOCOL.Sender().requestProbes(self.connectionProbes)
#         return [Probe("id", "10.0.0.2"), Probe("id 2", "10.0.0.2")]

    def fetchResults(self):
        self.doFetchResults.clear()
        return cParams.PROTOCOL.Sender().requestResults(self.connectionResults)

    def updateStatus(self, status):
        pass
    
    def addResult(self, result):
        pass

    def quit(self):
        try:
            cParams.PROTOCOL.disconnect(self.connection)
            cParams.PROTOCOL.disconnect(self.connectionProbes)
            cParams.PROTOCOL.disconnect(self.connectionResults)
        except:
            pass

'''
    Parses a command from user input into a commanderMessage
'''
class Parser(object):

    def __init__(self, command, interface):
        self.rcommand = command
        self.message = None
        self.errors = None
        args = argparse.ArgumentParser(description="Parses the user command")
        args.add_argument('-t', '--target-probe',
                          dest = 'target_probe',
                          metavar = 'target-ip',
                          help = "Ip of the target to control",
                          default = interface.targetId)

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
        subp3.add_argument('id', 
                           metavar='id',
                           default = interface.targetId,
                           help='The id of the probe you wish to remove')
        subp3.set_defaults(func=self.setRemove)
        

        try:
            self.command = args.parse_args(shlex.split(command))
            self.command.func()
        except (argparse.ArgumentError, SystemExit):
            self.errors = args.format_usage()
#         if (len(self.aCommand) < 2):
#             raise ValueError("The argument supplied must at least have 2 words")

    def getCommand(self):
        return self.rcommand

    def getParams(self):
        return self.command

    def getErrors(self):
        return self.errors

    def setAdd(self):
        self.message = Add(self.command.target_probe,
                           self.command.ip)

    def setDo(self):
        self.message = Do(self.command.target_probe,
                          self.command.test,
                          self.command.options)

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
            cParams.PROTOCOL.Sender().send(self.interface.connection, message)
            time.sleep(0.3)
            self.interface.triggerFetchProbes()
            self.interface.updateStatus("Command '%s' sent" % self.parser.getCommand())
        else:
            raise NoSuchCommand()
