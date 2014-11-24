"""
Service that tries to find out variations in delay in a network

@author: francois

"""
from threading import Event
from argparse import Namespace, ArgumentParser

from .link_detection import LinkDetection, KMeans
from .link_detection import Probe as abstractProbe
from managers.watchers import WatcherServices

#TODO: replace ip with names
class WatcherDelay(LinkDetection):
    """Watch the network for delay changes wrt baseline"""

    PING_TEST_NAME = 'sping'
    ICMP_HEADER_SIZE = 8
    D_PING_PACKET_SIZE = 56
    D_NPINGS = 10


    def __init__(self, options, logger):
        self.D_DELAY_METRIC_WEIGHT = 1
        super().__init__(options, logger)
        self.name = 'delay'
        self.measureClass = PingStats

    def newProbe(self, *args, **kwargs):
        return Probe(*args, **kwargs)

    def newGroup(self):
        return Group()

    def _resetWork(self):
        super()._resetWork()
        self.clustering = KMeans(clusterClass = Group, distanceThreshold = PingStats(rttavg = self.options.x), logger = self.logger)

    def parseOptions(self, opts, nameSpace = None):
        self.logger.info("options : >%s<\n"%opts)
        parser = ArgumentParser()
        parser.add_argument('--delay-metric-weight',
                            dest = 'delayMetricWeight',
                            type = float,
                            default = self.D_DELAY_METRIC_WEIGHT)

        args, rest = parser.parse_known_args(opts, Namespace(
            nPings = self.D_NPINGS,
            packetSize = self.D_PING_PACKET_SIZE,
            rttdevThreshold = 10,  # threshold above which to throw results (rttdev in ms)
        )
        )
        self.D_DELAY_METRIC_WEIGHT = args.delayMetricWeight
        if args.delayMetricWeight > 0:
            self.metrics.append((args.delayMetricWeight, self.metricDelay))
        super().parseOptions(rest, args)
        self.options.pingOptions = ['--parallel', '-c %s' % self.options.nPings, '-s %s' % self.options.packetSize, "-i 0.5"]
        Probe.packetSize = self.options.packetSize

    def initialize(self):
        super().initialize()
        self.maxDelay = max([p.baseline.rttavg for p in self.lp.values()])

    def makeMeasures(self, s):
        opts = self.options.pingOptions + [probe.address for probe in s]
        resContainer = self.TestResult()
        WatcherServices.doStandaloneTest(self.PING_TEST_NAME, opts, resContainer.addResult, resContainer.addError)
        # protect against tests hanging
        resContainer.resultCollected.wait(30)
        if not resContainer.resultCollected.is_set():
            self.makeMeasures(s)
            return
        redoMeasure = []
        for host, ping in resContainer.results.items():
            if ping.rttdev > self.options.rttdevThreshold:
                redoMeasure.append(self.lp[host])
            self.lp[host].add(ping)
        if len(redoMeasure) > 0:
            self.logger.info("Retaking measure for %s", repr(redoMeasure))
            print("Retaking measure for %s" % repr(redoMeasure))
            self.makeMeasures(redoMeasure)

    def makeBaseline(self, hosts):
        super().makeBaseline(hosts)
        opts = self.options.pingOptions + [self.lp[host].address for host in hosts]
        resContainer = self.TestResult()
        WatcherServices.doStandaloneTest(self.PING_TEST_NAME, opts, resContainer.addResult, resContainer.addError)
        resContainer.resultCollected.wait()
        redoBl = []
        for host, ping in resContainer.results.items():
            # check that values are consistent, redo if not
            if ping.rttdev > self.options.rttdevThreshold:
                redoBl.append(host)
            self.lp[host].baseline = ping
        if len(redoBl) > 0:
            self.logger.info("Retaking baseline for %s", repr(redoBl))
            print("Retaking baseline for %s" % repr(redoBl))
            self.makeBaseline(redoBl)

    def isSeparated(self, sets):
        white, black = sets
        rw = white.representative
        aw = rw.rttavg
        dw = rw.sdev

        rb = black.representative
        ab = rb.rttavg
        db = rb.sdev

        return abs(aw - ab) - (db + dw) / 2.0 > self.options.x

    def metricDelay(self, host):
        # TODO : reduce f in noisy measures ?
        # try to spread delay (wrt baseline) to get a broader spectrum
        f = 1
        m = 1
        tested = self.tested
        # le = 0
        # if len(tested) == 0:
        # return f, self._MAX_METRIC
        # TODO : silence hosts with high rttdev ??
        m = self.getTotalMetric(host, tested, hostDelayDistance, self.maxDelay)
        # for p in tested:
        # m += self.setDistance(p.baseline.rttavg - host.baseline.rttavg, self.maxDelay)
        # le += 1
        # m /= le
        return f, m * self.MAX_METRIC

    class TestResult(object):
        def __init__(self):
            self.resultCollected = Event()
            self.results = {}
            self.testId = None

        def addResult(self, testId, result):
            if result is not None:
                for h, r in result.items():
                    self.results[h] = PingStats(r.sent,
                                                r.received,
                                                r.rttmin,
                                                r.rttavg,
                                                r.rttmax,
                                                r.rttdev)
            self.resultCollected.set()

        def addError(self, testId, error):
            self.resultCollected.set()

        def __hash__(self, *args, **kwargs):
            if self.testId is None:
                return object.__hash__(self, *args, **kwargs)
            else:
                return self.testId


def hostDelayDistance(host1, host2):
    return abs(host1.baseline.rttavg - host2.baseline.rttavg)


class Probe(abstractProbe):
    packetSize = 0

    def __init__(self, address, id, measureClass):
        super().__init__(address, id, measureClass)

    def getBaselineAvg(self):
        return self.baseline.rttavg

    def getMeasure(self):
        # TODO : check baseline stddev
        p = self.measures[-1]
        return PingStats(sent = p.sent,
                         received = p.received,
                         rttmin = (p.rttmin - self.baseline.rttmin),
                         rttavg = (p.rttavg - self.baseline.rttavg),
                         rttmax = (p.rttmax - self.baseline.rttmax),
                         rttdev = (p.rttdev + self.baseline.rttdev) / 2.0)

    @property
    def nPackets(self):
        return sum(p.sent for p in self.measures)

    @property
    def bytes(self):
        return self.nPackets * self.packetSize

    def __str__(self):
        return "%s:%s" % (str(self.address), '{:.2f}'.format(self.getMeasure().rttavg) if len(self.measures) > 0 else 'none')


class Group(list):
    @property
    def representative(self):
        import math
        # TODO: do better for rttdev
        if not len(self) > 0:
            return PingStats()

        mean = sum(p.getMeasure().rttavg for p in self) / len(self)
        return PingStats(
            rttmin = min([p.getMeasure().rttmin for p in self]),
            rttmax = max([p.getMeasure().rttmin for p in self]),
            rttavg = mean,
            rttdev = math.sqrt(sum(p.getMeasure().rttdev ** 2 for p in self) / len(self)),
            sdev = math.sqrt(sum((p.getMeasure().rttavg - mean) ** 2 for p in self) / len(self)))

    def printRepresentative(self):
        return "{:.2f}".format(float(self.representative.rttavg))

    def __str__(self):
        return "%s: %s" % (self.printRepresentative(), super().__repr__())


class PingStats(object):
    def __init__(self, sent = 0.0, received = 0.0, rttmin = 0.0, rttavg = 0.0, rttmax = 0.0, rttdev = 0.0, sdev = 0.0):
        self.sent = sent
        self.received = received
        self.rttmin = rttmin
        self.rttavg = rttavg
        self.rttmax = rttmax
        self.rttdev = rttdev
        self.sdev = sdev

    def printAvg(self):
        return "{:.2f}".format(self.rttavg)

    def printAvgDev(self):
        return "{:.2f}@{:.2f}".format(self.rttavg, self.rttdev)

    def printAll(self):
        return """
        sent : %d, received %d
        avg : %.2f,
        min : %.2f, max : %.2f
        stddev : %.2f
        """ % (self.sent, self.received, self.rttavg, self.rttmin, self.rttmax, self.rttdev)

    def toDict(self):
        return {
            'rttavg': self.rttavg,
            'rttmin': self.rttmin,
            'rttmax': self.rttmax,
            'rttdev': self.rttdev,
            'sent': self.sent,
            'received': self.received
        }
