import re
import time
import argparse
import signal
from consts import Identification

from interfaces.probetest import TesterTest, TesteeTest, Report
from interfaces.excs import TestArgumentError

from managers.tests import TestServices
name = 'iperf'

class Iperf(object):

    def getName(self):
        return name


    _EXEC = 'iperf'

    PROTO_TCP="tcp"
    PROTO_UDP="udp"
    P_TCP = ''
    P_UDP = '-u'
    D_UDP_BW = '10M'
    D_PORT = 5001

    _CLIENT_MODE = '-c'
    _SERVER_MODE = '-s'

    _CLI_TPL = r'(?P<timestamp>[^,]+),,,,,(?P<id>[^,]+),(?P<interval>[^,]+),(?P<transfer>\d+),(?P<bw>\d+)'
    _SRV_TPL = r'(?P<timestamp>[^,]+),,,,,(?P<id>[^,]+),(?P<interval>[^,]+),(?P<transfer>\d+),(?P<bw>\d+)(?P<udp>.*)?'
    _UDP_SRV_TPL = r',(?P<jitter>\d+\.\d+),(?P<errors>\d+),(?P<datagrams>\d+),(?P<loss>\d+\.\d+),(?P<outoforder>\d+)?'

    def __init__(self):
        self.name = name
        self.options = None

    def parseOptions(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('targets', metavar = 'targets', nargs = "+")
        parser.add_argument('--protocol',
                            dest = "protocol",
                            choices = [self.PROTO_TCP, self.PROTO_UDP],
                            default = self.PROTO_TCP)

        parser.add_argument('--udp-bw',
                            dest = 'udpbw',
                            default = self.D_UDP_BW)

        parser.add_argument('--port',
                            dest = 'port',
                            default = self.D_PORT)

        transmit = parser.add_mutually_exclusive_group()
        transmit.add_argument('-t', '--time',
                              dest = 'time',
                              default = 10)

        transmit.add_argument('-n', '--num',
                              dest = 'num',
                              default = None)

        try:
            self.options = parser.parse_args(self.opts)
            self.targets = self.options.targets
            # if self.options.protocol == self.PROTO_UDP:
            #     self.options.proto = self.P_UDP
            #     opts['udpBw'] = '-b %s' % opts['udpBw']
            # else:
            #     opts['udpBw'] = ''
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())


    @classmethod
    def _parseSrvIperf(cls, srvOut):
        r = BwStats()
        for line in srvOut.splitlines():
            m = re.match(cls._SRV_TPL, line)
            if m is not None:
                bw = float(m.group('bw'))
                transfer = float(m.group('transfer'))
                if 'udp' in m.groupdict() and m.group('udp') != '':
                    u = re.match(cls._UDP_SRV_TPL, m.group('udp'))
                    if u is not None:
                        sent = float(u.group('datagrams'))
                        errors = float(u.group('errors'))
                        received = sent - errors
                        r = BwStats(sent = sent, received = received,
                                    loss = float(u.group('loss')),
                                    outoforder = float(u.group('outoforder')),
                                    bw = bw,
                                    jitter = float(u.group('jitter')),
                                    transfer = transfer,
                                    errors = errors)
                    else:
                        r = BwStats(bw = bw, transfer = transfer)
                else:
                    r = BwStats(bw = bw, transfer = transfer)
        return r

    @classmethod
    def _parseCliIperf(cls, cliOut):
        r = BwStats()
        for line in cliOut.splitlines():
            m = re.match(cls._CLI_TPL, line)
            if m is not None:
                bw = float(m.group('bw'))
                transfer = float(m.group('transfer'))
                r = BwStats(bw = bw, transfer = transfer)
        return r


class TesterIperf(TesterTest, Iperf):
    iperfCmd = '{exec} {mode} {ip} -y c --reportexclude CMSV {proto}{udpBw} -p {port} {transmit}'
    MAX_ATTEMPTS = 5
    # prepareTimeout = DEFAULT_PREPARE_TIMEOUT
    # doTimeout = DEFAULT_DO_TIMEOUT
    # resultTimeout = DEFAULT_RESULT_TIMEOUT
    #
    # def __init__(self, options):
    #     _Test.__init__(self, '%020x' % random.randrange(256 ** 15), options)
    #     self.targets = []
    #     self.rawResult = None

    def __init__(self, options):
        Iperf.__init__(self)
        TesterTest.__init__(self, options)
        self.parseOptions()
        self.outputs = {}
        self.bws = {}
        self.cmd = self.iperfCmd.format(exec = self._EXEC,
                                        proto = self.P_UDP if self.options.protocol == self.PROTO_UDP else self.P_TCP,
                                        port = self.options.port,
                                        transmit = '-n %s' % self.options.num if self.options.num is not None else '-t %s' % self.options.time,
                                        mode = self._CLIENT_MODE,
                                        udpBw = ' -b %s' % self.options.udpbw if self.options.protocol == self.PROTO_UDP else '',
                                        ip = "{ip}")
    def doTest(self):
        """Does the actual test"""
        for target in self.targets:
            targetIp = TestServices.getProbeIpById(target)
            if self.options.protocol == self.PROTO_TCP:
                attempts = 0
                telnetCli = 'sh -c "echo A | telnet -e A {ip} {port}"'
                while ('Connected' not in TestServices.runCmd(telnetCli.format(ip = targetIp, port = self.options.port))[0].decode()
                       and attempts < self.MAX_ATTEMPTS):
                    attempts += 1
                    time.sleep(.5)
            self.outputs[target] = TestServices.runCmd(self.cmd.format(ip = targetIp))

    def doOver(self):
        """Wrap up the test"""
        for target, output in self.outputs.items():
            cliout, clierr, exitcode = output
            self.bws[target] = self._parseCliIperf(cliout.decode())

    def doAbort(self):
        """Abort the test, should be similar to doOver()"""
        pass

    def doResult(self, reports):
        """Generate the result of the test given the set of reports from the tested probes
        Should populate self.result and self.rawResult
        :param reports: list of reports from the target probes
        """
        #TODO : check for errors
        self.rawResult = {}
        self.rawResult.update(self.bws)
        for probeId, report in reports.items():
            rbw = self.rawResult[probeId]
            bw = report.getBwStats()
            #copy all additional info we have
            if bw.sent > 0:
                rbw.sent = bw.sent
            if bw.received > 0:
                rbw.received = bw.received
            if bw.bw > 0:
                #average bw between sending bw and receiving bw
                rbw.bw += bw.bw
                rbw.bw /= 2
            if bw.jitter > 0:
                rbw.jitter = bw.jitter
            if bw.errors > 0:
                rbw.errors = bw.errors
            if bw.loss > 0:
                rbw.loss = bw.loss
            if bw.outoforder > 0:
                rbw.outoforder = bw.outoforder
        self.result = "\n".join("%s : %s"%(k, v.printAll()) for k, v in self.rawResult.items())

    def getRawResult(self):
        """Return result in bare form (not string) if necessary"""
        return self.rawResult


class IperfReport(Report):
    def __init__(self, probeId, isSuccess = True, bwStats = None):
        super().__init__(probeId, isSuccess)
        self.bwStats = bwStats

    def getBwStats(self):
        return self.bwStats


class TesteeIperf(TesteeTest, Iperf):
    """Methods for the probe(s) which receive the test"""

    iperfCmd = '{exec} {mode} -y c --reportexclude CMSV {proto} -p {port}'
    # overTimeout = DEFAULT_OVER_TIMEOUT
    #
    def __init__(self, options, testId):
        Iperf.__init__(self)
        TesteeTest.__init__(self, options, testId)
        self.parseOptions()
        self.process = None
        self.cmd = self.iperfCmd.format(exec = self._EXEC,
                                        proto = self.P_UDP if self.options.protocol == self.PROTO_UDP else self.P_TCP,
                                        port = self.options.port,
                                        mode = self._SERVER_MODE)

    def replyPrepare(self):
        """Actions that the probe must perform in order to be ready for the test"""
        self.process = TestServices.popen(self.cmd)

    def replyOver(self):
        """Actions that the probe must perform when the test is over
        generates the report and returns it!!!"""
        self.process.send_signal(signal.SIGINT)
        out, err = self.process.communicate()
        bw = self._parseSrvIperf(out.decode())
        return IperfReport(probeId = Identification.PROBE_ID, isSuccess=True, bwStats = bw)


class BwStats(object):
    def __init__(self, sent = 0.0, received = 0.0, transfer = 0.0, bw = 0.0, jitter = 0.0, errors = 0.0,
                 loss = 0.0, outoforder = 0.0):
        self.sent = sent
        self.received = received
        self.transfer = transfer
        self.bw = bw
        self.jitter = jitter
        self.errors = errors
        self.loss = loss
        self.outoforder = outoforder

    def printAll(self):
        return "sent: {:6.0f}, received: {:6.0f}, " \
               "transfer: {:10.0f}, bw: {:4.2f}Mbps, jitter: {:5.3f}, " \
               "errors: {:4.0f}, loss: {:5.3f}, outoforder: {:4.0f}".format(self.sent,
                                                                           self.received,
                                                                           self.transfer,
                                                                           self.bw/(1000.0**2),
                                                                           self.jitter,
                                                                           self.errors,
                                                                           self.loss,
                                                                           self.outoforder)

