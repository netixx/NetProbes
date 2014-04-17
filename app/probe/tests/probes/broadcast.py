'''
Implementation of a broadcast test

'''
__all__ = ['TesterBroadcast', 'TesteeBroadcast']

import socket
import argparse

from interfaces.probetest import Report, TesterTest, TesteeTest
from managers.tests import TestServices
from consts import Identification
from interfaces.excs import TestArgumentError


name = "Broadcast"

class Broadcast(object):
    
    ENCODING = "latin1"
    DEFAULT_PORT = 5678
    DEFAULT_TIMEOUT = 3.0

    messageSend = "Unicast Test"
    
    def __init__(self):
        self.socket = None
        self.port = self.DEFAULT_PORT
        self.timeout = self.DEFAULT_TIMEOUT
        self.options = None
        self.name = name

    def getName(self):
        return name

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self):
        parser = argparse.ArgumentParser(description="Parses the broadcast test options")
        parser.add_argument('--port', type=int, metavar='port', default=self.port)
        parser.add_argument('--timeout', metavar='timeout', default=self.timeout, type=float)

        try:
            opts = parser.parse_args(self.opts)
            self.targets = TestServices.getIdAllOtherProbes()
            self.options = opts
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())

class TesterBroadcast(TesterTest, Broadcast):

    def __init__(self, options):
        Broadcast.__init__(self)
        TesterTest.__init__(self, options)
        self.parseOptions()

    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        self.socket.settimeout(self.options.timeout)

    '''
        Does the actual test
    '''
    def doTest(self):
        self.logger.info("BroadCast : Starting test")
        self.logger.info("BroadCast : Sending message")
        self.socket.sendto(self.messageSend.encode(self.ENCODING), ('<broadcast>' , self.options.port))
        self.logger.info("BroadCast : Waiting for response message")
#         self.socket.settimeout(self.options.timeout)

    '''
        Prepare yourself for finish
    '''
    def doOver(self):
        self.socket.close()

    '''
        Generate the result of the test given the set of reports from the tested probes
        Should populate self.result
    '''
    def doResult(self, reports):
        ok = []
        fail = []
        for probeId, report in reports.items():
            if not report.isSuccess:
                fail.append(probeId)
            else:
                ok.append(probeId)

        if (len(ok) == len(reports)):
            self.result = "Ok : probe received the message."
        else:
            self.result = "Fail, probe did not receive the message."

        self.result += "\n Id ok : " + ", ".join(ok) + "\n Id fail : " + ", ".join(fail)

    ''' Methods for the probe(s) which receive the test'''

class TesteeBroadcast(TesteeTest, Broadcast):

    def __init__(self, options, testId):
        Broadcast.__init__(self)
        TesteeTest.__init__(self, options, testId)
        self.parseOptions()
        self.msgReceived = False

    '''
        Actions that the probe must perform in order to be ready
    '''
    def replyPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.bind(('', self.options.port))

    '''
        Actions that must be taken when the probe received the test
    '''
    def replyTest(self):
        message , address = self.socket.recvfrom(len(self.messageSend))
        if (message.decode(self.ENCODING) == self.messageSend):
            self.msgReceived = True
            
    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    def replyOver(self):
        self.socket.close()
        report = Report(Identification.PROBE_ID)
        report.isSuccess = self.msgReceived
        return report
