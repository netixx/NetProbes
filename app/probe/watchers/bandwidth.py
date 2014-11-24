"""
Service that tries to find out variations in delay in a network

@author: francois

"""
from threading import Event
from argparse import ArgumentParser

from .link_detection import LinkDetection, KMeans
from .link_detection import Probe as abstractProbe
from managers.watchers import WatcherServices


class WatcherBandwidth(LinkDetection):
    """Watch the network for delay changes wrt baseline"""

    BW_TEST_NAME = 'igi'
    # BW_TEST_NAME = 'iperf'

    def __init__(self, options, logger):
        super().__init__(options, logger)
        self.name = 'bandwidth'
        self.measureClass = BwStats

    def newProbe(self, *args, **kwargs):
        return Probe(*args, **kwargs)

    def newGroup(self):
        return Group()

    def _resetWork(self):
        super()._resetWork()
        self.clustering = KMeans(clusterClass = Group,
                                 distanceThreshold = BwStats(bw = self.options.x * BwStats.NORM_FACTOR_MB),
                                 logger = self.logger,
                                 axes = ['bw'])

    def parseOptions(self, opts, nameSpace = None):
        self.logger.info("options : >%s<\n" % opts)
        parser = ArgumentParser()
        parser.add_argument('--bw-metric-weight',
                            dest = 'bwMetricWeight',
                            type = float,
                            default = 0)

        args, rest = parser.parse_known_args(opts)
        if args.bwMetricWeight > 0:
            self.metrics.append((args.bwMetricWeight, self.metricBw))
        super().parseOptions(rest, args)
        self.options.bytesThreshold = 10**20

    def initialize(self):
        super().initialize()
        self.maxBw = max(p.baseline.bw for p in self.lp.values())

    def isSeparated(self, sets):
        white, black = sets
        rw = white.representative
        aw = rw.bw
        dw = rw.sdev

        rb = black.representative
        ab = rb.bw
        db = rb.sdev

        return abs(aw - ab) - (db + dw) > self.options.x

    def makeMeasures(self, s):
        opts = [probe.id for probe in s]
        id2ip = {v.id: v.address for v in s}
        resContainer = self.TestResult()
        self._makeMeasure(opts, resContainer)
        # if not resContainer.resultCollected.is_set():
        #     self.makeMeasures(s)
        #     return
        # redoMeasure = []
        for host, bw in resContainer.results.items():
            # if ping.rttdev > self.options.rttdevThreshold:
            # redoMeasure.append(self.lp[host])
            self.lp[id2ip[host]].add(bw)
            # if len(redoMeasure) > 0:
            # self.logger.info("Retaking measure for %s", repr(redoMeasure))
            #     print("Retaking measure for %s" % repr(redoMeasure))
            #     self.makeMeasures(redoMeasure)

    def makeBaseline(self, hosts):
        super().makeBaseline(hosts)
        # remapping to host id
        opts = [self.lp[host].id for host in hosts]
        id2ip = {self.lp[host].id: self.lp[host].address for host in hosts}
        resContainer = self.TestResult()
        self._makeMeasure(opts, resContainer)
        # redoBl = []
        for host, bw in resContainer.results.items():
            self.lp[id2ip[host]].baseline = bw
            # if len(redoBl) > 0:
            # self.logger.info("Retaking baseline for %s", repr(redoBl))
            #     print("Retaking baseline for %s" % repr(redoBl))
            #     self.makeBaseline(redoBl)

    def _makeMeasure(self, probes, resContainer):
        import datetime

        for probe in probes:
            WatcherServices.doTest(self.BW_TEST_NAME, [probe], resContainer.addResult, resContainer.addError)
            resContainer.resultCollected.wait()
            self.logger.info("%s : Bw checked for probe %s\n" % (datetime.datetime.now(), probe))
            resContainer.resultCollected.clear()
        resContainer.resultCollected.set()
        self.logger.info("Results in : %s" % (" ".join(["%s:%s" % (repr(host), bw.printAvg()) for host, bw in resContainer.results.items()])))

    def metricBw(self, host):
        # TODO : reduce f in noisy measures ?
        # try to spread delay (wrt baseline) to get a broader spectrum
        f = 1
        m = 1
        tested = self.tested
        # TODO : silence hosts with high rttdev ??
        m = self.getTotalMetric(host, tested, hostBwDistance, self.maxBw)
        return f, m * self.MAX_METRIC

    class TestResult(object):
        def __init__(self):
            self.resultCollected = Event()
            self.results = {}
            self.testId = None

        def addResult(self, testId, result):
            if result is not None:
                for h, r in result.items():
                    self.results[h] = BwStats(sent = r.sent,
                                              received = r.received,
                                              transfer = r.transfer,
                                              bw = r.bw,
                                              jitter = r.jitter,
                                              errors = r.errors,
                                              loss = r.loss,
                                              outoforder = r.outoforder)
            self.resultCollected.set()

        def addError(self, testId, error):
            self.resultCollected.set()

        def __hash__(self, *args, **kwargs):
            if self.testId is None:
                return object.__hash__(self, *args, **kwargs)
            else:
                return self.testId


def hostBwDistance(host1, host2):
    return abs(host1.baseline.bw - host2.baseline.bw)


class Probe(abstractProbe):
    def __init__(self, address, id, measureClass):
        super().__init__(address, id, measureClass)

    def getBaselineAvg(self):
        return self.baseline.rttavg

    def getMeasure(self):
        # TODO : check baseline stddev
        p = self.measures[-1]
        return BwStats(sent = p.sent,
                       received = p.received,
                       bw = (p.bw - self.baseline.bw))

    @property
    def nPackets(self):
        return sum(p.sent for p in self.measures)

    @property
    def bytes(self):
        return sum(b.transfer for b in self.measures)


    def __str__(self):
        return "%s:%s" % (str(self.address), '{:.2f}'.format(self.getMeasure().bw) if len(self.measures) > 0 else 'none')


class Group(list):
    @property
    def representative(self):
        import math

        if not len(self) > 0:
            return BwStats()

        mean = sum(p.getMeasure().bw for p in self) / len(self)
        return BwStats(
            bw = mean,
            sdev = math.sqrt(sum((p.getMeasure().bw - mean) ** 2 for p in self) / len(self)))

    def printRepresentative(self):
        return "{:.2f}".format(float(self.representative.bw)/BwStats.NORM_FACTOR_MB)

    def __str__(self):
        return "%s: %s" % (self.printRepresentative(), super().__repr__())


class BwStats(object):
    NORM_FACTOR_MB = 1000.0 ** 2

    def __init__(self, sent = 0.0, received = 0.0, transfer = 0.0, bw = 0.0, jitter = 0.0, errors = 0.0,
                 loss = 0.0, outoforder = 0.0, sdev = 0.0):
        self.sent = sent
        self.received = received
        self.transfer = transfer
        self.bw = bw
        self.jitter = jitter
        self.errors = errors
        self.loss = loss
        self.outoforder = outoforder
        self.sdev = sdev

    def printAvg(self):
        return "{:.3f}".format(self.bw / self.NORM_FACTOR_MB)

    def printAvgDev(self):
        return self.printAvg()

    # def printAvgDev(self):
    # return "{:.2f}@{:.2f}".format(self.rttavg, self.rttdev)

    def printAll(self):
        return """
        sent : %d, received %d
        bw : %.2f
        """ % (self.sent, self.received, self.bw / self.NORM_FACTOR_MB)

    def toDict(self):
        return {
            'sent': self.sent,
            'received': self.received,
            'bw': self.bw / self.NORM_FACTOR_MB
        }
