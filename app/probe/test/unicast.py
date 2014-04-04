'''
Implementation of a unicast test
Protocols tcp and udp are supported

'''
__all__ = ['TesterUnicast', 'TesteeUnicast']

import socket, argparse
from consts import Identification
from exceptions import TestArgumentError
from tests import Report, TestServices, TesterTest, TesteeTest

class Unicast(object):
    ENCODING = "latin1"
    port = 5678
    timeout = 3.0
    messageSend = "Unicast Test"
    messageReply = "Unicast Reply"

    def __init__(self):
        self.socket = None

    @staticmethod
    def protocolToUnix(protocol):
        if (protocol == 'udp'):
            return socket.SOCK_DGRAM

        return socket.SOCK_STREAM

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self, options):
        # creating the parsers
        parser = argparse.ArgumentParser(prog = self.__class__.__name__, description = "Parses the unicast test target")
        parser.add_argument('target', metavar = 'target', nargs = 1)
        parser.add_argument('--port', type = int, metavar = 'port', default = self.port)
        parser.add_argument('--protocol', metavar = 'protocol', default = 'tcp', choices = ['tcp', 'udp'])
        parser.add_argument('--timeout', metavar = 'timeout', default = self.timeout, type = float)
        try:
            opts = parser.parse_args(options)
            self.targets = opts.target
            self.options = opts
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())

class TesterUnicast(TesterTest, Unicast):

    def __init__(self, options):
        Unicast.__init__(self)
        TesterTest.__init__(self, options)
    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, self.protocolToUnix(self.options.protocol))

    '''
        Does the actual test
    '''
    def doTest(self):
        self.logger.info("Unicast : Starting test")
        try:
            self.socket.settimeout(self.options.timeout)
            self.socket.connect((TestServices.getProbeIpById(self.targets[0]) , self.options.port))
            self.logger.info("Unicast : Sending message")
            self.socket.sendall(self.messageSend.encode(self.ENCODING))
            self.logger.info("Unicast : Waiting for response message")

            response = self.socket.recv(len(self.messageReply))
            self.logger.info("Unicast : Message received")
            if (response.decode(self.ENCODING) == self.messageReply):
                self.success = True
        except socket.timeout:
            self.success = False

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


class TesteeUnicast(TesteeTest, Unicast):

    def __init__(self, options, testId):
        Unicast.__init__(self)
        TesteeTest.__init__(self, options, testId)
        self.msgReceived = False
        self.msgSent = False
        self.success = False

    '''
        Actions that the probe must perform in order to be ready
    '''
    def replyPrepare(self):
        self.socket = socket.socket(socket.AF_INET, self.protocolToUnix(self.options.protocol))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", self.options.port))
        if(self.socket.type == socket.SOCK_STREAM):
            self.socket.listen(1)

    '''
        Actions that must be taken when the probe received the test
    '''
    def replyTest(self):
        self.logger.debug("Unicast : Replying to unicast test")
        try:
            self.socket.settimeout(self.options.timeout)
            print(repr(self.socket.type))
            print(repr(socket.SOCK_STREAM))
            if self.options.protocol == "tcp":
                self.logger.debug("Unicast : Accepting TCP connections")
                connection, address = self.socket.accept()
                self.logger.info("Unicast : Waiting for TCP message")
                msg = connection.recv(len(self.messageSend))
                self.logger.info("Unicast : Message received")
                self.msgReceived = True
                if (msg.decode(self.ENCODING) == self.messageSend):
                    connection.sendall(self.messageReply.encode(self.ENCODING))
                    self.msgSent = True
                
            elif self.options.protocol == "udp":
                self.logger.info("Unicast : Waiting for UDP message")
                msg , adr = self.socket.recvfrom(len(self.messageSend))
                self.logger.info("Unicast : Message received")
                self.msgReceived = True
                if (msg.decode(self.ENCODING) == self.messageSend):
                    self.socket.sendto(self.messageReply.encode(self.ENCODING), adr)
                    self.msgSent = True

        except socket.timeout:
                self.msgReceived = False
                self.logger.info("Unicast : Unable to receive message : Socket timeout")
        except:
            self.msgReceived = False
            self.logger.info("Unicast : Unable to receive message")
            
    
    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    def replyOver(self):
        self.logger.info("Unicast : Replying over")
        if self.socket.type == socket.SOCK_STREAM:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                self.logger.info("Unicast : unable to shutdown socket")

        self.socket.close()
        report = Report(Identification.PROBE_ID)
        if not (self.msgReceived and self.msgSent):
            report.isSuccess = False
        self.logger.info("Unicast : Report created")
        return report
