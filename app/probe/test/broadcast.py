from tests import Test
from tests import Report
import socket
from probes import ProbeStorage
import argparse
from consts import Identification
from exceptions import TestArgumentError


class Broadcast(Test):
    
    ENCODING = "latin1"
    port = 5678
    timeout = 3.0
    messageSend = "Unicast Test"
    
    msgReceived = False
    def __init__(self, options):
        super().__init__(options)
        self.socket = None

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self, options):
        parser = argparse.ArgumentParser(description="Parses the broadcast test options")
        parser.add_argument('--port', type=int, metavar='port', default=self.port)
        parser.add_argument('--timeout', metavar='timeout', default=self.timeout, type=float)

        try:
            opts = parser.parse_args(options)
            self.targets = ProbeStorage.getIdAllOtherProbes()
            self.options = opts
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())

    
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

    rcvSocket = None
    '''
        Actions that the probe must perform in order to be ready
    '''
    @classmethod
    def replyPrepare(cls):
        cls.rcvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cls.rcvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.rcvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        cls.rcvSocket.bind(('', cls.options.port))

    '''
        Actions that must be taken when the probe received the test
    '''
    @classmethod
    def replyTest(cls):
        message , address = cls.rcvSocket.recvfrom(len(cls.messageSend))
        if (message.decode(cls.ENCODING) == cls.messageSend):
            cls.msgReceived = True
            

    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    @classmethod
    def replyOver(cls):
        cls.rcvSocket.close()
        report = Report(Identification.PROBE_ID)
        report.isSuccess = cls.msgReceived
        return report
