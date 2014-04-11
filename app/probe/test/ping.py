'''
Implementation of a unicast test
Protocols tcp and udp are supported

'''
__all__ = ['TesterPing', 'TesteePing']

from consts import Identification
from exceptions import TestArgumentError, TestError
from tests import Report, TestServices, TesterTest, TesteeTest
import re, argparse

name = "Ping"

class PingError(TestError):
    pass

class PingParseError(TestError):
    pass


class Ping(object):
    CMD = 'ping -c 1 '
    npings = 1

    def __init__(self):
        self.options = None
        self.name = name
        self.stats = None
        self.isSweep = False

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOptions(self):
        # ping -c 3 -t 30 -m 10 -W 2 -s 50 -i 1 -D
        parser = argparse.ArgumentParser(prog = name,
                                         description = "Parses the ping test options")
        parser.add_argument('targets',
                            metavar = 'TARGETS',
                            nargs = "+")
        parser.add_argument('-c',
                            type = int,
                            metavar = 'NPINGS',
                            dest = 'nPings',
                            default = self.npings,
                            help = 'Number of pings packets to send')
        parser.add_argument('-t',
                            metavar = 'TIMEOUT',
                            dest = 'timeout',
                            type = float,
                            help = 'Timeout before ping command exits')
        parser.add_argument('-T',
                            metavar = 'TTL',
                            dest = 'multicastTtl',
                            type = int,
                            help = 'Set IP TTL value for multicast packets')
        parser.add_argument('-m',
                            metavar = 'IP_TTL',
                            dest = 'ipTtl',
                            type = int,
                            help = 'Ip TTL')
        parser.add_argument('-W',
                            metavar = 'WAIT_TIME',
                            dest = 'waitReply',
                            type = int,
                            help = 'Time to wait for reply')

        sweepGrp = parser.add_mutually_exclusive_group()
        sweepParamsGrp = sweepGrp.add_argument_group()
        sweepGrp.add_argument('-s',
                            metavar = 'PACKET_SIZE',
                            type = int,
                            dest = 'packetSize',
                            help = 'Size of payload')

        sweepParamsGrp.add_argument('-G',
                            metavar = 'SWEEP_MAX_SIZE',
                            dest = 'swpMaxSize',
                            type = int,
                            help = 'Maximum size of payload when sweeping'
                            )
        sweepParamsGrp.add_argument('-g',
                            metavar = 'SWEEP_MIN_SIZE',
                            dest = 'swpMinSize',
                            type = int,
                            help = 'Size of payload to start sweeping')
        sweepParamsGrp.add_argument('-H',
                            metavar = 'SWEEP_INC_SIZE',
                            type = int,
                            dest = 'swpIncSize',
                            help = 'Payload size increment for each sweep')
        parser.add_argument('-i',
                            metavar = "WAIT_TIME",
                            dest = 'waitSend',
                            type = float,
                            help = 'Time to wait between sending ping')
        parser.add_argument('-D', 
#                             metavar = "DON'T_FRAGMENT",
                            dest = 'df',
                            action = 'store_true',
                            help = "Set the don't fragment bit")

        try:
            opts = parser.parse_args(self.opts)
            self.targets = opts.targets
            self.options = "-c %s" % opts.nPings
            self.options += self._addOption("-t", opts.timeout)
            self.options += self._addOption("-T", opts.multicastTtl)
            self.options += self._addOption("-m", opts.ipTtl)
            self.options += self._addOption("-W", opts.waitReply)
            self.options += self._addOption("-s", opts.packetSize)
            self.options += self._addOption("-G", opts.swpMaxSize)
            self.options += self._addOption("-g", opts.swpMinSize)
            self.options += self._addOption("-h", opts.swpIncSize)
            self.options += self._addOption("-i", opts.waitSend)
            if opts.df:
                self.options += " -D"
            if opts.swpIncSize or opts.swpMaxSize or opts.swpMinSize:
                self.isSweep = True
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())

    def _addOption(self, opt, value):
        if value is not None:
            return " %s %s" % (opt, value)
        return ""

    def makePing(self, ip):
        stdout, stderr = TestServices.runCmd('ping %s %s' % (self.options, ip))
        if self.isSweep:
            return self._parseSweepPing(str(stdout.decode()))
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

    def _parseSweepPing(self, pingOutput):
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
        r = r'(\d+) bytes from .*: icmp_seq=(\d+)'
        m = re.findall(r, pingOutput)
        sweep = []
        if m is not None:
            for line in m:
                sweep.append((int(line[1]), int(line[0])))
        return sent, received, sweep


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
        self.logger.info("Starting test")
        try:
            probeIp = TestServices.getProbeIpById(self.targets[0])
            r = self.makePing(probeIp)
            self.stats = []
            if self.isSweep:
                self.stats.append(SweepStats(*r))
            else:
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
        return """Packets sent : %s, packets received : %s
        rtt min/avg/max/mdev : %s/%s/%s/%s ms""" % (self.sent, self.received, self.rttmin, self.rttavg, self.rttmax, self.rttdev)

class SweepStats(object):
    def __init__(self, sent, received, packetsDetails):
        self.sent = sent
        self.received = received
        self.packets = packetsDetails
        
    def printAll(self):
        return """Packets sent : %s, packets received : %s
        size received : %s""" % (self.sent, self.received, ", ".join([str(p[1]) for p in self.packets]))
