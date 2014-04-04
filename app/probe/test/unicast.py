from tests import Test, Report, TestServices
import socket
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
        # creating the parsers
        parser = argparse.ArgumentParser(prog = self.__class__.__name__, description = "Parses the unicast test target")
        parser.add_argument('target', metavar='target', nargs=1)
        parser.add_argument('--port', type=int, metavar='port', default=self.port)
        parser.add_argument('--protocol', metavar = 'protocol', default = 'tcp', choices = ['tcp', 'udp'])
        parser.add_argument('--timeout', metavar='timeout', default=self.timeout, type=float)
        try:
            opts = parser.parse_args(options)
            self.targets = opts.target
            self.options = opts
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())


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

    ''' Methods for the probe(s) which receive the test'''

    rcvSocket = None
    '''
        Actions that the probe must perform in order to be ready
    '''
    @classmethod
    def replyPrepare(cls):
        cls.rcvSocket = socket.socket(socket.AF_INET, cls.protocolToUnix(cls.options.protocol))
        cls.rcvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cls.rcvSocket.bind(("", cls.options.port))
        if(cls.rcvSocket.type == socket.SOCK_STREAM):
            cls.rcvSocket.listen(1)

    '''
        Actions that must be taken when the probe received the test
    '''
    @classmethod
    def replyTest(cls):
        cls.logger.debug("Unicast : Replying to unicast test")
        try:
            cls.rcvSocket.settimeout(cls.options.timeout)
            print(repr(cls.rcvSocket.type))
            print(repr(socket.SOCK_STREAM))
            if cls.options.protocol == "tcp":
                cls.logger.debug("Unicast : Accepting TCP connections")
                connection, address = cls.rcvSocket.accept()
                cls.logger.info("Unicast : Waiting for TCP message")
                msg = connection.recv(len(cls.messageSend))
                cls.logger.info("Unicast : Message received")
                cls.msgReceived = True
                if (msg.decode(cls.ENCODING) == cls.messageSend):
                    connection.sendall(cls.messageReply.encode(cls.ENCODING))
                    cls.msgSent = True
                
            elif cls.options.protocol == "udp":
                cls.logger.info("Unicast : Waiting for UDP message")
                msg , adr = cls.rcvSocket.recvfrom( len(cls.messageSend) )
                cls.logger.info("Unicast : Message received")
                cls.msgReceived = True
                if (msg.decode(cls.ENCODING) == cls.messageSend):
                    cls.rcvSocket.sendto( cls.messageReply.encode( cls.ENCODING), adr )
                    cls.msgSent = True

        except socket.timeout:
                cls.msgReceived = False
                cls.logger.info("Unicast : Unable to receive message : Socket timeout")
        except:
            cls.msgReceived = False
            cls.logger.info("Unicast : Unable to receive message")
            
    
    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    @classmethod
    def replyOver(cls):
        cls.logger.info("Unicast : Replying over")
        if cls.rcvSocket.type == socket.SOCK_STREAM:
            try:
                cls.rcvSocket.shutdown(socket.SHUT_RDWR)
            except:
                cls.logger.info("Unicast : unable to shutdown socket")

        cls.rcvSocket.close()
        report = Report(Identification.PROBE_ID)
        if not (cls.msgReceived and cls.msgSent):
            report.isSuccess = False
        cls.logger.info("Unicast : Report created")
        return report
