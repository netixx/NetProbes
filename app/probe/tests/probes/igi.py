import re
import argparse
import signal

from consts import Identification
from interfaces.probetest import TesterTest, TesteeTest, Report
from interfaces.excs import TestArgumentError
from managers.tests import TestServices

#reason for IGI selection can be found in 
# Espinet, François, Joumblatt, Diana and Rossi, Dario, 
# Zen and the art of network troubleshooting: a hands on experimental study
#. In Traffic Monitoring and Analysis (TMA'15), Barcellona, Spain, Apr 2015. 

name = 'igi'


class Igi(object):
    def getName(self):
        return name

    N_PROBES = 60
    PACKET_SIZE = "500B"
    N_TRAINS = 3

    _PTR_TPL = r'PTR:\s+(?P<bw>\d+\.\d+)\s+Mpbs(?: (suggested))?'
    _IGI_TPL = r'IGI:\s+(?P<bw>\d+\.\d+)\s+Mpbs'


    def __init__(self):
        self.name = name
        self.options = None

    def parseOptions(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('targets', metavar = 'targets', nargs = "+")
        parser.add_argument('--n-probes',
                            dest = "nProbes",
                            type = int,
                            default = self.N_PROBES)

        parser.add_argument('--n-trains',
                            dest = "nTrains",
                            type = int,
                            default = self.N_TRAINS)

        parser.add_argument('--packet-size',
                            dest = "packetSize",
                            default = self.PACKET_SIZE)

        try:
            self.options = parser.parse_args(self.opts)
            self.targets = self.options.targets
            # if self.options.protocol == self.PROTO_UDP:
            # self.options.proto = self.P_UDP
            #     opts['udpBw'] = '-b %s' % opts['udpBw']
            # else:
            #     opts['udpBw'] = ''
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())


    @classmethod
    def _parseCliIgi(cls, cliOut):
        r = BwStats()
        ptr = re.search(cls._PTR_TPL, cliOut)
        if ptr is not None:
            r = BwStats(bw = float(ptr.group('bw')) * (1000 ** 2))
        igi = re.search(cls._IGI_TPL, cliOut)
        if igi is not None:
            r = BwStats(bw = float(igi.group('bw')) * (1000 ** 2))
        return r


class TesterIgi(TesterTest, Igi):
    """
    Tester is the Client for Igi : do nothing for prepare
    """

    # prepareTimeout = DEFAULT_PREPARE_TIMEOUT
    doTimeout = 600
    # resultTimeout = DEFAULT_RESULT_TIMEOUT


    _EXEC = 'ptr-client'
    cliCmd = '{exec} -n {nprobes} -s {packetSize} -k {ntrains} {serverIp}'

    # prepareTimeout = DEFAULT_PREPARE_TIMEOUT
    # doTimeout = DEFAULT_DO_TIMEOUT
    # resultTimeout = DEFAULT_RESULT_TIMEOUT
    #
    # def __init__(self, options):
    # _Test.__init__(self, '%020x' % random.randrange(256 ** 15), options)
    #     self.targets = []
    #     self.rawResult = None

    def __init__(self, options):
        Igi.__init__(self)
        TesterTest.__init__(self, options)
        self.parseOptions()
        self.outputs = {}
        self.bws = {}
        self.cmd = self.cliCmd.format(exec = self._EXEC,
                                      nprobes = self.options.nProbes,
                                      ntrains = self.options.nTrains,
                                      packetSize = self.options.packetSize,
                                      serverIp = "{ip}")

    def doTest(self):
        """Does the actual test"""
        for target in self.targets:
            targetIp = TestServices.getProbeIpById(target)
            self.outputs[target] = TestServices.runCmd(self.cmd.format(ip = targetIp))

    def doOver(self):
        """Wrap up the test"""
        for target, output in self.outputs.items():
            cliout, clierr, exitcode = output
            self.bws[target] = self._parseCliIgi(cliout.decode())

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
        # for probeId, report in reports.items():
        #     rbw = self.rawResult[probeId]
        #     bw = report.getBwStats()
        #     #copy all additional info we have
        #     if bw.sent > 0:
        #         rbw.sent = bw.sent
        #     if bw.received > 0:
        #         rbw.received = bw.received
        #     if bw.bw > 0:
        #         #average bw between sending bw and receiving bw
        #         rbw.bw += bw.bw
        #         rbw.bw /= 2
        #     if bw.jitter > 0:
        #         rbw.jitter = bw.jitter
        #     if bw.errors > 0:
        #         rbw.errors = bw.errors
        #     if bw.loss > 0:
        #         rbw.loss = bw.loss
        #     if bw.outoforder > 0:
        #         rbw.outoforder = bw.outoforder
        self.result = "\n".join("%s : %s" % (k, v.printAll()) for k, v in self.rawResult.items())

    def getRawResult(self):
        """Return result in bare form (not string) if necessary"""
        return self.rawResult


class TesteeIgi(TesteeTest, Igi):
    """Methods for the probe(s) which receive the test"""

    overTimeout = 300


    _EXEC = 'ptr-server'

    srvCmd = '{exec}'
    # overTimeout = DEFAULT_OVER_TIMEOUT
    #
    def __init__(self, options, testId):
        Igi.__init__(self)
        TesteeTest.__init__(self, options, testId)
        self.parseOptions()
        self.process = None
        self.cmd = self.srvCmd.format(exec = self._EXEC)

    def replyPrepare(self):
        """Actions that the probe must perform in order to be ready for the test"""
        self.process = TestServices.popen(self.cmd)

    def replyOver(self):
        """Actions that the probe must perform when the test is over
        generates the report and returns it!!!"""
        self.process.send_signal(signal.SIGINT)
        # out, err = self.process.communicate()
        return Report(probeId = Identification.PROBE_ID, isSuccess = True)


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
                                                                            self.bw / (1000.0 ** 2),
                                                                            self.jitter,
                                                                            self.errors,
                                                                            self.loss,
                                                                            self.outoforder)

