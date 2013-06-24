from tests import Test
from tests import Report
import socket
from probes import ProbeStorage
import consts
import argparse
from consts import Identification

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
        parser = argparse.ArgumentParser(description="Parses the unicast test target")
        parser.add_argument('target', metavar='target', nargs=1)
        parser.add_argument('opts', nargs=argparse.REMAINDER)
        opts = parser.parse_args(options)

        optParser = argparse.ArgumentParser(description="Parses the unicast test options")
        optParser.add_argument('--port', type=int, metavar='port', default=self.port)
        optParser.add_argument('--protocol', metavar='protocol', default='tcp', choices=['tcp', 'udp'])
        optParser.add_argument('--timeout', metavar='timeout', default=self.timeout, type=float)
        popt = []
        for op in opts.opts:
            popt.extend(('--' + op).split())
        optParser.parse_args(popt, opts)

        self.targets = opts.target
        self.options = opts
    
    @staticmethod
    def protocolToUnix(protocol):
        if (protocol == 'udp'):
            return socket.SOCK_DGRAM

        return socket.SOCK_STREAM

    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, self.protocolToUnix(self.options.protocol))

    '''
        Does the actual test
    '''
    def doTest(self):
        consts.debug("Unicast : Starting test")
        self.socket.connect((ProbeStorage.getProbeById(self.targets[0]).getIp() , self.options.port))
        consts.debug("Unicast : Sending message")
        self.socket.sendall(self.messageSend.encode(self.ENCODING) )
        consts.debug("Unicast : Waiting for response message")
        self.socket.settimeout(self.options.timeout)
        response = self.socket.recv( len(self.messageReply) )
        consts.debug("Unicast : Message received")
        if (response == self.messageReply):
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
        for report in reports:
            if not report.isSuccess():
                fail.append(report.getProbeId())
            else:
                ok.append(report.getProbeId())

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
        cls.rcvSocket = socket.socket(socket.AF_INET, cls.protocolToUnix(cls.options.protocol))
        cls.rcvSocket.bind(("", cls.options.port))
        cls.rcvSocket.listen(1)

    '''
        Actions that must be taken when the probe recieved the test
    '''
    @classmethod
    def replyTest(cls):
        connection, address = cls.rcvSocket.accept()
        consts.debug("Unicast : Waiting for message")
        cls.rcvSocket.settimeout(cls.options.timeout)
        msg = connection.recv(len(cls.messageSend))
        consts.debug("Unicast : Message received")
        cls.msgReceived = True
        if (msg == cls.messageSend):
            connection.sendall(cls.messageReply.encode( cls.ENCODING) )
        cls.msgSent = True
            

    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    @classmethod
    def replyOver(cls):
        cls.rcvSocket.close()
        report = Report(Identification.PROBE_ID)
        if not (cls.messageReply and cls.msgSent):
            report.isSuccess = False

        return report
