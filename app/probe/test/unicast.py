
from tests import Test
from tests import Report
import socket
from probes import ProbeStorage
import consts
import argparse

class Unicast(Test):
    
    ENCODING = "latin1"
    port = 5678
    messageSend = "Unicast Test"
    messageReply = ""
    
    def __init__(self, options):
        super().__init__(options)
        self.socket = None

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self, options):
        parser = argparse.ArgumentParser(description="Parses the unicast test options")
        parser.add_argument('target', metavar='target')
        parser.add_argument('--port', type=int, metavar='port', default=self.port)
        parser.add_argument('--protocol', metavar='protocol', default='tcp', choices=['tcp', 'udp'])

        opts = parser.parse_args(options)
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
        consts.debug("Unicast : Receiving message")
        response = self.socket.recv( len(self.messageReply) )
        consts.debug("Unicast : Message received")

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
        for report in reports:
            pass
        self.result = "Ok, probe replied successfully"

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
        msg = connection.recv(len(cls.messageSend))
        consts.debug("Test : Message received")
        if (msg == cls.messageSend):
            connection.sendall(cls.messageReply.encode( cls.ENCODING) )
            

    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    @classmethod
    def replyOver(cls):
        cls.rcvSocket.close()
        return Report()
