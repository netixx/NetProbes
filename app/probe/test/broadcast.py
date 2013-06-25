from tests import Test
from tests import Report
import socket
from probes import ProbeStorage
import consts
import argparse
from consts import Identification
from exceptions import TestArgumentError


class Unicast(Test):
    
    ENCODING = "latin1"
    port = 5678
    timeout = 3.0
    messageSend = "Unicast Test"
    messageReply = "Unicast Reply"
    
    msgReceived = False
    msgSent = False
    success = False
    def __init__(self, options):
        super().__init__(options)
        self.socket = None

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self, options):
        popt = []
        for op in options:
            popt.extend(('--' + op).split())

        parser = argparse.ArgumentParser(description="Parses the broadcast test options")
        parser.add_argument('--port', type=int, metavar='port', default=self.port)
        parser.add_argument('--timeout', metavar='timeout', default=self.timeout, type=float)

        try:
            opts = parser.parse_args(popt)
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())
        self.targets = opts.target
        self.options = opts
    
    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
        self.socket = socket.socket(socket.AF_INET, self.protocolToUnix(self.options.protocol))
        self.socket.settimeout(self.options.timeout)

    '''
        Does the actual test
    '''
    def doTest(self):
        consts.debug("BroadCast : Starting test")
        consts.debug("BroadCast : Sending message")
        self.sendto(self.messageSend, ('<broadcast>' , self.options.port))
        consts.debug("BroadCast : Waiting for response message")
#         self.socket.settimeout(self.options.timeout)
        response = self.socket.recv(len(self.messageReply))
        consts.debug("BroadCast : Message received")
        if (response.decode(self.ENCODING) == self.messageReply):
            self.success = True

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

        if (len(ok) == len(reports) and self.success):
            self.result = "Ok, probe replied successfully."
        elif (len(ok) == len(reports)):
            self.result = "Partial Fail : probe received the message but didn't reply correctly."
        else:
            self.result = "Fail, probe did not receive the message."

        self.result += "\n Id tested :" + " ".join(ok) + " ".join(fail)

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
        Actions that must be taken when the probe recieved the test
    '''
    @classmethod
    def replyTest(cls):
        message , address = cls.rcvSocket.recvfrom(len(cls.messageSend))
        cls.msgReceived = True
        if (message.decode(cls.ENCODING) == cls.messageSend):
            cls.rcvSocket.sendto(cls.messageReply.encode(cls.ENCODING), address)
            

    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    @classmethod
    def replyOver(cls):
        cls.rcvSocket.close()
        report = Report(Identification.PROBE_ID)
        if not (cls.msgReceived and cls.msgSent):
            report.isSuccess = False

        return report
