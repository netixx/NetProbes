from tests import Test
from tests import Report
import socket
from probes import ProbeStorage
import consts
import argparse
import struct
from consts import Identification
from exceptions import TestArgumentError

class Multicast(Test):
    
    ENCODING = "latin1"
    port = 6789
    timeout = 3.0
    ttl = 20
    broadcast_address = "224.1.1.1"
    messageSend = "Multicast Test"
    
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
        parser = argparse.ArgumentParser(description="Parses the multicast test target")
        parser.add_argument('target', metavar='target', nargs="+")
        parser.add_argument('--port', type=int, metavar='port', default=self.port)
        parser.add_argument('--timeout', metavar='timeout', default=self.timeout, type=float)
        parser.add_argument('--ttl', metavar='ttl', default=self.ttl, type=int)
        parser.add_argument('-ma', '--m-address', metavar='multicast-address', default=self.broadcast_address)

        try:
            opts = parser.parse_args(options)
            self.targets = opts.target
            self.options = opts
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())


    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM , socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', self.options.ttl) )
        
    '''
        Does the actual test
    '''
    def doTest(self):
        consts.debug("Multicast : Starting test / Sending message")
        self.socket.sendto(self.messageSend.encode(self.ENCODING), (self.options.m_address, self.options.port))
        

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
            self.result = "Ok, probe replied successfully."
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
        cls.rcvSocket.bind( ('', cls.options.port) )
        
        ''' On ajoute la sonde au groupe multicast  '''
        consts.debug("Multicast : On ajoute la sonde au groupe multicast")
        group = socket.inet_aton(cls.options.m_address)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        cls.rcvSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        consts.debug("Multicast : Sonde ajoutée au groupe multicast")
        

    '''
        Actions that must be taken when the probe received the test
    '''
    @classmethod
    def replyTest(cls):
        consts.debug("Multicast : Waiting for message")
        try:
            cls.rcvSocket.settimeout(cls.options.timeout)
            msg, address = cls.rcvSocket.recvfrom( len(cls.messageSend) )
            msg = msg.decode(cls.ENCODING)
            consts.debug("Multicast : Message received")
            cls.msgReceived = msg == cls.messageSend
        except socket.timeout:
            cls.msgReceived = False
            consts.debug("Multicast : ReplyTest -> socket timeout")
        except:
            cls.msgReceived = False
            consts.debug("Multicast : ReplyTest -> unknown error")


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
