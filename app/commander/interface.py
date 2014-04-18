"""Main module for interfacing the user with the commander
Master class which must be subclassed to provide interaction with the user

@author: francois
"""
from threading import Thread, Event, Timer
import time
import shlex
import argparse
import logging

from exceptions import NoSuchCommand
from common.commanderMessages import Add, Do, Delete
from common.consts import Params as cParams
from common.intfs.exceptions import ProbeConnectionFailed

class Interface(object):
    """The interface class provides a basic API for interacting with the
    remote commander Server instance"""
    targetIp = "127.0.0.1"
    targetId = None
    PROBE_REFRESH_TIME = 10
    RESULTS_REFRESH_TIME = 10

    def __init__(self, ip):
        self.logger = logging.getLogger()
        self.targetIp = ip
        self.targetId = self.getTargetId(ip)
        self.isRunning = True
        self.doFetchProbes = Event()
        self.doFetchResults = Event()
        self.resFetchTimer = None
        self.probeFetchTimer = None
        try:
            self.connection = cParams.PROTOCOL.createConnection(self.targetIp)
            cParams.PROTOCOL.connect(self.connection)
            self.connectionProbes = cParams.PROTOCOL.createConnection(self.targetIp)
            cParams.PROTOCOL.connect(self.connectionProbes)
            self.connectionResults = cParams.PROTOCOL.createConnection(self.targetIp)
            cParams.PROTOCOL.connect(self.connectionResults)
        except ProbeConnectionFailed:
            raise ProbeConnectionFailed(
                "Error while attempting to perform an HTTP request to the probe %s" % self.targetIp)
        except ConnectionRefusedError:
            raise ProbeConnectionFailed("Error while connecting to probe : connection refused")

    def doCommand(self, command):
        """Execute a command given by the user
        :param command: command entered by the user

        """
        self.updateStatus("Executing command : " + command)
        time.sleep(0.3)
        try:
            cmd = Command(Parser(command, self), self)
            cmd.start()
        #             cmd.join()
        except (ValueError, NoSuchCommand):
            pass
        except ProbeConnectionFailed:
            self.logger.error("Error while sending command : connection failed", exc_info = 1)
            self.updateStatus("Cannot send command")
            #       self.updateStatus("Command is false or unkown")

    @staticmethod
    def getTargetId(ip):
        """Return the ID of the target of this commander
        :param ip: address to query"""
        return cParams.PROTOCOL.getRemoteId(ip)

    def updateProbes(self):
        """Update the list of known probes"""
        pass

    def updateResults(self):
        """Update the results of the tests"""
        pass

    def probeFetcherScheduler(self):
        """Schedule a query to fetch the list of probes"""
        self.triggerFetchProbes()
        self.probeFetchTimer = Timer(self.PROBE_REFRESH_TIME, self.probeFetcherScheduler)
        self.probeFetchTimer.start()

    #TODO: refactor with Timer objects
    def triggerFetchProbes(self):
        """Set the doFetchProbes flag"""
        self.doFetchProbes.set()
        # self.doFetchProbes.clear()

    def resultFetcherScheduler(self):
        """Recursive function that schedules fetching the results"""
        self.triggerFetchResult()
        self.resFetchTimer = Timer(self.RESULTS_REFRESH_TIME, self.resultFetcherScheduler)
        self.resFetchTimer.start()
        # self.resFetchTimer.clear()

    def triggerFetchResult(self):
        """Set the doFetchResults flag"""
        self.doFetchResults.set()
        # self.doFetchResults.clear()

    def fetchProbes(self):
        """Get the list of currently known probes from the target"""
        self.doFetchProbes.clear()
        return cParams.PROTOCOL.Sender.requestProbes(self.connectionProbes)

    def fetchResults(self):
        """Get the results from the target"""
        self.doFetchResults.clear()
        return cParams.PROTOCOL.Sender.requestResults(self.connectionResults)

    def updateStatus(self, status):
        """Update the status of the commander
        :param status: new status
        """
        pass

    def addResult(self, result):
        """Add a result to the results of the interface
        :param result: result to add
        """
        pass

    def quit(self):
        """Exit the commander interface properly"""
        try:
            self.logger.debug("Shutting down interface")
            self.isRunning = False
            if self.resFetchTimer is not None:
                self.resFetchTimer.cancel()
            if self.probeFetchTimer is not None:
                self.probeFetchTimer.cancel()
            cParams.PROTOCOL.disconnect(self.connection)
            cParams.PROTOCOL.disconnect(self.connectionProbes)
            cParams.PROTOCOL.disconnect(self.connectionResults)
        except:
            pass


class Parser(object):
    """Parses a command from user input into a commanderMessage"""

    def __init__(self, command, interface):
        self.rcommand = command
        self.message = None
        self.errors = None
        args = argparse.ArgumentParser(description = "Parses the user command")
        args.add_argument('-t', '--target-probe',
                          dest = 'target_probe',
                          metavar = 'target-ip',
                          help = "Ip of the target to control",
                          default = interface.targetId)

        subp = args.add_subparsers(dest = 'subparser_name')

        # parser for the add command
        subp1 = subp.add_parser('add')
        subp1.add_argument('ip', metavar = 'ip',
                           help = 'The ip you want to add')
        subp1.set_defaults(func = self.setAdd)

        # parser for the do command
        subp2 = subp.add_parser('do')
        subp2.add_argument('test', metavar = 'test',
                           help = 'The message you want to send to the probe')
        subp2.add_argument('options', nargs = argparse.REMAINDER)
        subp2.set_defaults(func = self.setDo)

        # parse for the remove command
        subp3 = subp.add_parser('remove')
        subp3.add_argument('id',
                           metavar = 'id',
                           default = interface.targetId,
                           help = 'The id of the probe you wish to remove')
        subp3.set_defaults(func = self.setRemove)

        try:
            self.command = args.parse_args(shlex.split(command))
            self.command.func()
        except (argparse.ArgumentError, SystemExit):
            self.errors = args.format_usage()
            #         if (len(self.aCommand) < 2):
            #             raise ValueError("The argument supplied must at least have 2 words")

    def getCommand(self):
        """Return the raw command entered by the user"""
        return self.rcommand

    def getParams(self):
        """Return the parsed command"""
        return self.command

    def getErrors(self):
        """Return the errors that may have occurred during parsing"""
        return self.errors

    def setAdd(self):
        """Set what should be done when the command is add"""
        self.message = Add(self.command.target_probe,
                           self.command.ip)

    def setDo(self):
        """Set what should be done when the command is do"""
        self.message = Do(self.command.target_probe,
                          self.command.test,
                          self.command.options)

    def setRemove(self):
        """Set what should be done when the command is remove"""
        self.message = Delete(self.command.id)

    def getMessage(self):
        return self.message


class Command(Thread):
    """Runs the command of the user (in a new Thread)"""

    def __init__(self, parser, interface):
        Thread.__init__(self)
        self.interface = interface
        self.parser = parser
        if parser.getErrors() is not None:
            self.interface.updateStatus(self.parser.errors)
            raise NoSuchCommand()

        self.setName('Command')

    # does the command
    def run(self):
        """Run the command"""
        message = self.parser.getMessage()
        if message is not None:
            cParams.PROTOCOL.Sender.send(self.interface.connection, message)
            time.sleep(0.3)
            self.interface.triggerFetchProbes()
            self.interface.updateStatus("Command '%s' sent" % self.parser.getCommand())
        else:
            raise NoSuchCommand()
