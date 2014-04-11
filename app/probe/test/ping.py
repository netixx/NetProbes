'''
Implementation of a unicast test
Protocols tcp and udp are supported

'''

__all__ = ['TesterPing', 'TesteePing']

from consts import Identification
from exceptions import TestArgumentError, TestError
from tests import Report, TestServices, TesterTest, TesteeTest
import re

name = "Ping"

class PingError(TestError):
    pass

class PingParseError(TestError):
    pass


class Ping(object):
    CMD = 'ping -c 1 '

    def __init__(self):
        self.options = None
        self.name = name
        self.stats = None

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self):
        self.options = "-c1"
        self.targets = self.opts

    def makePing(self, ip):
        stdout, stderr = TestServices.runCmd('ping %s %s' % (self.options, ip))
        return self._parsePing(str(stdout.decode()))

    def _parsePing(self, pingOutput):
        # Parse ping output and return all data.
#         errorTuple = (1, 0, 0, 0, 0, 0)
        # Check for downed link
        r = r'[uU]nreachable'
        m = re.search(r, pingOutput)
        if m is not None:
            raise PingError('Destination unreachable')
        r = r'(\d+) packets transmitted, (\d+) (?:packets)? received'
        m = re.search(r, pingOutput)
        if m is None:
            raise PingParseError("Can not parse output %s" % pingOutput)
        sent, received = int(m.group(1)), int(m.group(2))
        r = r'(?:rtt)|(?:round-trip) min/avg/max/m|(?:std)dev = '
        r += r'(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms'
        m = re.search(r, pingOutput)
        if m is None:
            raise PingParseError('Could not parse ping output: %s' % pingOutput)
        rttmin = float(m.group(1))
        rttavg = float(m.group(2))
        rttmax = float(m.group(3))
        rttdev = float(m.group(4))
        return sent, received, rttmin, rttavg, rttmax, rttdev


class TesterPing(TesterTest, Ping):
    
    rformat = "Ping statistics %s"
    eformat = "Ping failed %s"
    
    def __init__(self, options):
        self.process = None
        Ping.__init__(self)
        TesterTest.__init__(self, options)
        self.parseOptions()
        self.format = None

    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        pass

    '''
        Does the actual test
    '''
    def doTest(self):
        self.logger.info("Unicast : Starting test")
        try:
            probeIp = TestServices.getProbeIpById(self.targets[0])
            r = self.makePing(probeIp)
            self.stats = []
            self.stats.append(PingStats(*r))
            self.success = True
        except PingError as e:
            self.errors = e
            self.success = True
        except (PingParseError, Exception) as e:
            self.success = False
            raise TestError(e)

    '''
        Prepare yourself for finish
    '''
    def doOver(self):
        pass

    '''
        Generate the result of the test given the set of reports from the tested probes
        Should populate self.result
    '''
    def doResult(self, reports):
        if self.success:
            if self.errors is not None:
                self.result = self.eformats % self.errors
                self.rawResult = self.errors
            else:   
                self.result = self.rformat % self.stats[0].printAll()
                self.rawResult = self.stats
        else:
            raise TestError(self.errors)

class TesteePing(TesteeTest, Ping):

    def __init__(self, options, testId):
        Ping.__init__(self)
        TesteeTest.__init__(self, options, testId)
        self.parseOptions()
        self.msgReceived = False
        self.msgSent = False
        self.success = False

    '''
        Actions that the probe must perform in order to be ready
    '''
    def replyPrepare(self):
        pass

    '''
        Actions that must be taken when the probe received the test
    '''
    def replyTest(self):
        pass
            
    
    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    def replyOver(self):
        return Report(Identification.PROBE_ID)

class PingStats(object):
    def __init__(self, sent, received, rttmin, rttavg, rttmax, rttdev):
        self.sent = sent
        self.received = received
        self.rttmin = rttmin
        self.rttavg = rttavg
        self.rttmax = rttmax
        self.rttdev = rttdev

    def printAll(self):
        return """Packets sent :%s, packets received : %s
        rtt min/avg/max/mdev : %s/%s/%s/%s ms""" % (self.sent, self.received, self.rttmin, self.rttavg, self.rttmax, self.rttdev)
