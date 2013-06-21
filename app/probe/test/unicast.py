
from tests import Test
from tests import Report
import socket
from probes import ProbeStorage
import consts


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
        self.targets = options[0:1]

    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    '''
        Does the actual test
    '''
    def doTest(self):
        self.socket.connect((ProbeStorage.getProbeById(self.targets[0]).getIp() , self.port))
        self.socket.sendall(self.messageSend.encode(self.ENCODING) )
        response = self.socket.recv(1024)

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
        cls.rcvSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.rcvSocket.bind(("", cls.port))
        cls.rcvSocket.listen(1)

    '''
        Actions that must be taken when the probe recieved the test
    '''
    @classmethod
    def replyTest(cls):
        connection, address = cls.rcvSocket.accept()
        msg = connection.recv(1024)
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
