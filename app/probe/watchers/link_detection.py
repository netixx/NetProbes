"""
Service that tries to find out variations in delay in a network

@author: francois

"""
from argparse import ArgumentParser, ArgumentError
import random
import time
import argparse
import socket
import struct
import math
import abc
from consts import Identification

from interfaces.watcher import Watcher, WatcherArgumentError
from managers.watchers import WatcherServices


class LinkDetection(Watcher):
    """Watch the network for delay changes wrt baseline"""

    PROBALISTIC_BUCKET = 'probabilistic-bucket'
    ORDERED_BUCKET = 'ordered-bucket'
    PROBALISTIC_POWER_BUCKET = 'probabilistic-power-bucket'

    MAX_METRIC = 100

    def __init__(self, options, logger):
        super().__init__(self.__class__.__name__, options, logger)
        self.D_GRANULARITY = 2
        self.D_BYTES_THRESHOLD = 1000000
        self.D_MAX_RUNS = 1000
        self.D_BUCKET_TYPE = self.ORDERED_BUCKET
        self.D_SAMPLE_SIZE = 0.7
        self.D_RANDOM_METRIC_WEIGHT = 1
        self.D_BALANCED_METRIC_WEIGHT = 0
        self.D_IP_METRIC_WEIGHT = 0
        self.D_OVERLAY_SIZE = 128
        self.D_X = 90
        self.name = 'link_detection'
        self.options = None
        self.clustering = None
        self.measureClass = dict
        self.metrics = []
        self.stop = False
        self._resetAll()

    def _resetAll(self):
        self.parseOptions(self.getOpts(self.opts))
        self.lp = None
        self._resetWork()

    def newGroup(self):
        return Group()

    def _resetWork(self):
        self.bytes = 0
        self.runs = 0
        self.black = self.newGroup()
        self.white = self.newGroup()

    def getOpts(self, optstr):
        opts = []
        for arg in filter(None, optstr.split(",")):
            opts.append('--' + arg)
        return opts

    def parseOptions(self, opts, nameSpace = None):
        parser = ArgumentParser()
        parser.add_argument('--x',
                            dest = 'x',
                            type = float,
                            default = self.D_X)
        parser.add_argument('--granularity',
                            dest = 'granularity',
                            type = int,
                            default = self.D_GRANULARITY)
        parser.add_argument('--random-metric-weight',
                            dest = 'randomMetricWeight',
                            type = float,
                            default = self.D_RANDOM_METRIC_WEIGHT)
        parser.add_argument('--ip-metric-weight',
                            dest = "ipMetricWeight",
                            type = float,
                            default = self.D_IP_METRIC_WEIGHT)
        parser.add_argument('--balanced-metric-weight',
                            dest = 'balancedMetricWeight',
                            type = float,
                            default = self.D_BALANCED_METRIC_WEIGHT)

        parser.add_argument('--bucket-type',
                            dest = 'bucket_type',
                            choices = [self.PROBALISTIC_BUCKET, self.ORDERED_BUCKET, self.PROBALISTIC_POWER_BUCKET],
                            default = self.D_BUCKET_TYPE)

        parser.add_argument('--sample-size',
                            dest = 'sampleSize',
                            type = float,
                            default = self.D_SAMPLE_SIZE)

        parser.add_argument('--overlay-size',
                            dest = 'overlay_size',
                            type = int,
                            default = self.D_OVERLAY_SIZE)
        try:
            if nameSpace is not None:
                self.options = argparse.Namespace(
                    **vars(nameSpace)
                )
            else:
                self.options = argparse.Namespace()

            self.options.bytesThreshold = self.D_BYTES_THRESHOLD
            self.options.maxRuns = self.D_MAX_RUNS

            parser.parse_args(opts, self.options)

            if self.options.randomMetricWeight > 0:
                self.metrics.append((self.options.randomMetricWeight, self.metricRandom))
            if self.options.balancedMetricWeight > 0:
                self.metrics.append((self.options.balancedMetricWeight, self.metricBalance))
            if self.options.ipMetricWeight > 0:
                self.metrics.append((self.options.ipMetricWeight, self.metricIp))


            if self.options.bucket_type == self.PROBALISTIC_BUCKET:
                self.options.bucket = ProbabilisticBucket
            elif self.options.bucket_type == self.ORDERED_BUCKET:
                self.options.bucket = OrderedBucket
            elif self.options.bucket_type == self.PROBALISTIC_POWER_BUCKET:
                self.options.bucket = ProbabilisticPowerBucket

            self.D_X = self.options.x
            self.D_GRANULARITY = self.options.granularity
            self.D_RANDOM_METRIC_WEIGHT = self.options.randomMetricWeight
            self.D_IP_METRIC_WEIGHT = self.options.ipMetricWeight
            self.D_BALANCED_METRIC_WEIGHT = self.options.balancedMetricWeight
            self.D_BUCKET_TYPE = self.options.bucket_type
            self.D_SAMPLE_SIZE = self.options.sampleSize
            self.D_OVERLAY_SIZE = self.options.overlay_size

            print(self.options)
        except (SystemExit, ArgumentError):
            self.logger.error("Error while parsing options %s", parser.format_usage())
            raise WatcherArgumentError(parser.format_usage())

    @abc.abstractclassmethod
    def makeMeasures(self, s):
        pass

    @property
    def tested(self):
        return [p for p in self.lp.values() if p.nMeasures() > 0]


    @property
    def untested(self):
        return self.options.bucket([p for p in self.lp.values() if p.nMeasures() < 1])


    def makeBaseline(self, hosts):
        self.logger.info("Getting a baseline for hosts %s", repr(hosts))
        print("get baseline %s" % hosts)


    def run(self):
        # TODO : remove lines
        import time
        while len(WatcherServices.getAllOtherProbes()) < self.options.overlay_size - 1:
            self.logger.info("Length of other probes %s", len(WatcherServices.getAllOtherProbes()))
            time.sleep(10)
        WatcherServices.writeOutput('up', '1', 'w')
        time.sleep(45)
        from managers.actions import ActionMan

        ActionMan.actionQueue.join()
        # self.initializeEvent.set()
        while not self.stop:
            self.initializeEvent.wait()
            self.initialize()
            self.initializeEvent.clear()
            WatcherServices.writeOutput('events', '1', 'w')
            # work until new initialisation is asked
            while not self.stop and not self.initializeEvent.is_set():
                while not self.initializeEvent.is_set() and not self.workEvent.is_set():
                    self.workEvent.wait(2.0)
                if self.initializeEvent.is_set():
                    break
                try:
                    self.work()
                    self._resetWork()
                    self.workEvent.clear()
                finally:
                    WatcherServices.writeOutput('done', '1', 'w')

    def newProbe(self, *args, **kwargs):
        return Probe(*args, **kwargs)

    def setLp(self):
        self.lp = {p.address: self.newProbe(p.address, p.id, self.measureClass) for p in WatcherServices.getAllOtherProbes()}

    def initialize(self):
        print("INIT..")
        self.logger.info("Initialising algorithm")
        self._resetAll()
        self.setLp()
        while len(self.lp) < 1:
            self.setLp()
            time.sleep(2)
        self.makeBaseline(self.lp.keys())
        self.logger.info("Parameters : \n%s", "\n".join(["%s : %s" % (k, v) for k, v in vars(self.options).items()]))
        self.logger.info("Baseline done : %s", ", ".join(["%s: %s" % (p.address, p.baseline.printAvgDev()) for p in self.lp.values()]))
        self.maxIpDistance = max([ip2int(p.address) for p in self.lp.values()]) - min([ip2int(p.address) for p in self.lp.values()])


    def stopCondition(self):
        return (self.runs < self.options.maxRuns
                and len(self.untested) > 0
                and len(self.tested) <= self.sampleSize()
                and self.bytes < self.options.bytesThreshold)

    def sampleSize(self):
        #sampleSize as percentage
        if self.options.sampleSize <= 1:
            # round to the next int
            return int(self.options.sampleSize * len(self.lp) + 0.5)
        else:
            return int(self.options.sampleSize)


    @abc.abstractmethod
    def isSeparated(self, sets):
        pass

    def hasConverged(self, sets):
        return self.isSeparated(sets) and self.isThourough(sets)

    def isThourough(self, sets):
        return sum(len(s) for s in sets) + 1 >= self.sampleSize()

    def work(self):
        try:
            print("WORK...")
            self.logger.info("Starting algorithm ...\nProbes : %s", ", ".join(self.lp.keys()))
            # self.untested = self.options.bucket(self.lp.values())
            while not self.stop and self.stopCondition():
                # TODO : update for more than one set
                # and self.untested.largest(self.metric) > self.options.metricThreshold):
                self.runs += 1
                s = self.untested.getN(self.options.granularity, self.metric)
                print("sel", s)
                ndraws = 0
                while len(s) < 1 and ndraws < self.options.nDrawsThreshold:
                    self.logger.info("Empty selection from bucket, rerunning selection.")
                    s = self.untested.getN(self.options.maxTests, self.metric)
                    ndraws += 1
                if len(s) < 1:
                    break
                self.logger.info("Selection : %s" % repr(s))
                self.makeMeasures(s)
                clusters = self.clustering.cluster(self.tested)
                self.grey = clusters[KMeans.greySet]
                # TODO : remove names black and white
                self.sets = clusters['clusters']
                self.black = clusters['clusters'][0]
                self.white = clusters['clusters'][1]
                # update number of bytes
                self.bytes += sum(p.bytes for p in self.lp.values())

                self.logger.info("Step done, bytes used : %s KB, unknown host size %s, untested hosts : %s", self.bytes / (1024.0), len(self.grey),
                                 len(self.untested))
                self.logger.info("  white: %s\n  black: %s\n  grey: %s\n",
                                 self.white,
                                 self.black,
                                 self.grey)
                print("  white: %s\n  black: %s\n  grey: %s" % (
                    self.white,
                    self.black,
                    self.grey))
                self.logger.info("")

                if self.hasConverged(self.sets):
                    break

            print("Terminating :\n  white (%s): %s\n  black (%s): %s\n  grey : %s" % (
                self.white.printRepresentative(),
                ", ".join([p.address for p in self.white]),
                self.black.printRepresentative(),
                ", ".join([p.address for p in self.black]),
                self.grey))
            from consts import Identification

            parameters = vars(self.options)
            out = {
                'sets': {
                    'black': {
                        'hosts': [{'address': p.address,
                                   'stats': p.getMeasure().toDict()} for p in self.black],
                        'representative': self.black.representative.toDict()
                    },
                    'white': {
                        'hosts': [{'address': p.address,
                                   'stats': p.getMeasure().toDict()} for p in self.white],
                        'representative': self.white.representative.toDict()
                    }
                },
                'grey': [{'address': p.address,
                          'stats': p.getMeasure().toDict()} for p in self.grey],
                'bytes': self.bytes,
                'runs': self.runs,
                'untested': [{'address': p.address} for p in self.untested],
                'parameters': parameters,
                'watcher': Identification.PROBE_ID
            }
            self.logger.info("Terminating :\nRuns : %s\nBytes : %s KB\n  white (%s): %s\n  black (%s): %s\n  grey : %s",
                             self.runs,
                             self.bytes / (1024.0),
                             self.white.printRepresentative(),
                             ", ".join([str(p) for p in self.white]),
                             self.black.printRepresentative(),
                             ", ".join([str(p) for p in self.black]),
                             self.grey)

            import json
            import datetime

            jout = json.dumps(out, default = name)
            print(jout)
            WatcherServices.writeOutput("%s.json" % self.name, jout, mode = 'w')
            WatcherServices.writeOutput("%s-%s.json" % (self.name, datetime.datetime.now()), jout, mode = 'w')
        except Exception as e:
            self.logger.error("error %s", e, exc_info = 1)
            import traceback

            traceback.print_exc()
        # finally:
            # WatcherServices.writeOutput('done', '1', 'w')
            # kill this probe (auto mode)
            # import signal
            # import os

            # os.kill(os.getpid(), signal.SIGKILL)

    def quit(self):
        self.stop = True

    def metric(self, host):
        mets = []
        for w, m in self.metrics:
            f, metric = m(host)
            mets.append((w, f, metric))
        # metrics are between 0 and self.MAX_METRIC
        # factors represent the trust put in this metric by the metric calculator between 0 and 1 ?
        weights, factors, metrics = zip(*mets)
        # print(host.address, repr(metrics))
        metric = sum(w*f*m for w, f, m in mets)
        # for i, w in enumerate(self.options.metricWeights):
        #     metric += w * factors[i] * metrics[i]
        s = sum(weights)
        if s != 0:
            metric /= s
        return metric

    def metricRandom(self, host):
        return 1, random.randint(0, self.MAX_METRIC)

    def metricIp(self, host):
        #TODO: add closest probe as first probe
        # try to spread IP to get a broader spectrum
        # assign higher numbers to probes who are the furthest from the tested set
        # m = 0
        f = 1
        tested = self.tested
        # if len(tested) < 1:
        #     m = self.getTotalMetric(host, [self.newProbe(address..., Identification.PROBE_ID, self.measureClass)], hostIpDistance, self.maxIpDistance)
        # if len(tested) == 0:
        # return f, self._MAX_METRIC
        m = self.getTotalMetric(host, tested, hostIpDistance, self.maxIpDistance)
        # for p in tested:
        # m += self.setDistance(ipDistance(p.address, host.address), self.maxIpDistance)
        # m /= len(tested)
        return f, m * self.MAX_METRIC

    def getTotalMetric(self, host, baseSet, distance, maxDistance):
        m = 1
        if len(baseSet) < 1:
            return m
        for p in baseSet:
            m *= math.sqrt(abs(distance(host, p) / float(maxDistance)))
        return m ** (1.0 / float(len(baseSet)))


    def metricBalance(self, host):
        # TODO : update for more than one set ?
        # TODO : reduce f in case of biggestSet ?
        # try to get a balanced sets
        bl = len(self.black)
        wh = len(self.white)
        m = 1
        f = 1
        l = len(self.tested)
        # TODO : add condition on separation of sets/correct clustering
        if l > 0:
            f = float(abs(bl - wh)) / float(l)
            smallestSet = None
            biggestSet = None
            if bl == 0 and wh == 0:
                return f, self.MAX_METRIC
                # if abs(bl - wh) > self.sampleSize() * self.options.balancedSetsFactor:
                # give higher priority to the probes that are the closest in the IP range to
                # the ones belonging in the smallest set
            if bl > wh:
                # no host in white, take the opposite of black
                if wh == 0:
                    biggestSet = self.black
                else:
                    smallestSet = self.white
            elif bl < wh:
                if bl == 0:
                    biggestSet = self.white
                else:
                    smallestSet = self.black
            else:
                f = 1
            # else:
            # return f, self._MAX_METRIC
            if smallestSet is not None:
                m = self.getTotalMetric(host, smallestSet, hostIpDistance, self.maxIpDistance)
                # for p in smallestSet:
                # m += self.setDistance(ipDistance(p.address, host.address), self.maxIpDistance)
                # m /= len(smallestSet)
                # m is smaller when host is close to the probes in the smallest set
                # invert to give bigger weight to smaller distances
                m = 1 - m
            elif biggestSet is not None:
                f *= 0.8
                m = self.getTotalMetric(host, biggestSet, hostIpDistance, self.maxIpDistance)
                # for p in biggestSet:
                # m += self.setDistance(ipDistance(p.address, host.address), self.maxIpDistance)
                # m /= len(biggestSet)
                # m is smaller when host is close to the probes in the biggest set
                # return m to give bigger weight to higher distances

        return f, m * self.MAX_METRIC


def name(obj):
    return obj.__name__


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


def hostIpDistance(host1, host2):
    return ipDistance(host1.address, host2.address)


def ipDistance(addr1, addr2):
    return abs(ip2int(addr1) - ip2int(addr2))


class OrderedBucket(list):
    def getOne(self, metric):
        return self.getN(1, metric)[0]

    def getN(self, n, metric):
        if n > len(self):
            n = len(self)
        return sorted(self, key = metric, reverse = True)[:n]

        # def getNThreshold(self, n, threshold, metric):
        # return [host for host in self.getN(n, metric) if metric(host) > threshold]


class ProbabilisticBucket(OrderedBucket):
    def treatMetric(self, m):
        return int(m + 0.5)

    def getN(self, n, metric):
        s = []
        r = [(self.treatMetric(metric(host)), host) for host in self]

        while len(s) < n and len(r) > 0:
            w = 0
            rand = random.randint(0, sum(p[0] for p in r))
            for p in r:
                w += p[0]
                if rand <= w:
                    s.append(p[1])
                    r.remove(p)
                    break

        return s


class ProbabilisticPowerBucket(OrderedBucket):
    power = 3

    def treatMetric(self, m):
        return int((LinkDetection.MAX_METRIC * (m / float(LinkDetection.MAX_METRIC)) ** self.power) + 0.5)

    def getN(self, n, metric):
        s = []
        r = [(self.treatMetric(metric(host)), host) for host in self]

        while len(s) < n and len(r) > 0:
            w = 0
            rand = random.randint(0, sum(p[0] for p in r))
            for p in r:
                w += p[0]
                if rand <= w:
                    s.append(p[1])
                    r.remove(p)
                    break

        return s


class Group(list):

    @abc.abstractproperty
    def representative(self):
        return 0

    @abc.abstractclassmethod
    def printRepresentative(self):
        return ""

    def __str__(self):
        return "%s: %s" % (self.printRepresentative(), super().__repr__())


class Probe(object):
    def __init__(self, address, id, measureClass):
        self.id = id
        self.address = address
        self.measures = []
        self.resetMeasures()
        self.baseline = measureClass()
        self.measureClass = measureClass

    def add(self, measure):
        self.measures.append(measure)

    def getRawMeasure(self):
        return self.measures[-1]

    @abc.abstractclassmethod
    def getBaselineAvg(self):
        return 0

    @abc.abstractclassmethod
    def getMeasure(self):
        return self.measureClass()

    def nMeasures(self):
        return len(self.measures)

    @abc.abstractproperty
    def bytes(self):
        return 0

    def __str__(self):
        return "%s" % str(self.address)

    def __repr__(self):
        return str(self)

    def resetMeasures(self):
        self.measures = []


class KMeans(object):
    greySet = 'grey'
    D_AXES = ['rttavg']
    D_K = 2

    def __init__(self, clusterClass = Group, distanceThreshold = None, axes = None, distance = None, logger = None):
        self.axes = axes if axes is not None else self.D_AXES
        self.logger = logger
        self.newCluster = clusterClass
        self.distance = distance if distance is not None else self.euclidian
        self.K = self.D_K
        self.threshold = self._getDistance(distanceThreshold, None)

        self.maxLoops = 200

    def newClusters(self):
        return [self.newCluster() for _ in range(self.K)]


    def _clusterDistances(self, clusters):
        d = {}
        for i in range(0, len(clusters) - 1):
            for j in range(i + 1, len(clusters)):
                d[(i, j)] = self._getDistance(clusters[i].representative, clusters[j].representative)
        return d

    def cluster(self, data):
        grey = self.newCluster()
        # Do pure kmeans once
        self.K = 2

        while self.K >= 1:
            self.logger.info("Clustering with K = %s", self.K)
            clusters = self.kmeans(data)
            if len(clusters) <= 1:
                break
            allClustersFilled = all(len(c) > 0 for c in clusters)
            if allClustersFilled:
                # try to detect if some clusters are too close to each other
                d = self._clusterDistances(clusters)
                minDistIndex = min(d, key = d.get)
                self.logger.info("Dmin between clusters : %s, dists = %s", math.sqrt(abs(d[minDistIndex])), repr(d))
                # reduce K if they are too close
                if d[minDistIndex] < self.threshold:
                    self.logger.info("Clusters are too close dmin = %s, K = %s", d[minDistIndex], self.K)
                    self.K -= 1
                else:
                    break
            else:
                self.logger.error("At least on cluster was empty")
                # at least one cluster was empty (sort of should not happen)
                break


        # TODO : remove and adapt upper for variable length of clusters
        while len(clusters) < 2:
            clusters.append(self.newCluster())
        r = {self.greySet: grey,
             'clusters': clusters}

        return r

    def kmeans(self, data):
        reps = self._seeds(data)
        # initiate signatures
        sigs = None
        psigs = None
        loop = 0
        clusters = None
        while self._differs(sigs, psigs) and loop <= self.maxLoops:
            # print('rep', reps)
            psigs = self._signatures(reps)
            clusters = self.newClusters()
            for probe in data:
                cl, d = self._getClosest(probe, reps)
                # if d < self.threshold:
                clusters[cl].append(probe)
                # else:
                # add to grey cluster if max distance is too great
                # grey.append(probe)
            self.updateRepresentatives(reps, clusters)
            sigs = self._signatures(reps)
            loop += 1

        return clusters

    def _seeds(self, data):
        reps = []
        while len(reps) < self.K:
            s = self.newCluster([data[random.randint(0, len(data) - 1)]]).representative
            if s not in reps:
                reps.append(s)

        return reps

    def updateRepresentatives(self, reps, clusters):
        for cn, r in enumerate(reps):
            reps[cn] = clusters[cn].representative

    def _signatures(self, reps):
        s = []
        for r in reps:
            s.append(self._getDistance(r))
        return s

    def _differs(self, sig1, sig2):
        if sig1 is None or sig2 is None:
            return True
        if set(sig1) != set(sig2):
            return True

        return False


    def _getClosest(self, probe, reps):
        dmin = float('inf')
        closest = None
        for cn, c in enumerate(reps):
            d = self._getDistance(c, probe.getMeasure())
            if d < dmin:
                dmin = d
                closest = cn

        return closest, dmin


    def _getDistance(self, p1, p2 = None):
        v1 = self.Vector(p1.toDict(), self.axes)
        if p2 is None:
            v2 = self.Vector({k: 0.0 for k in p1.toDict().keys()}, self.axes)
        else:
            v2 = self.Vector(p2.toDict(), self.axes)
        return self.distance(v1, v2, self.axes)


    class Vector(dict):

        def __init__(self, data, axes):
            super().__init__()
            for a in axes:
                self[a] = data[a]

    @staticmethod
    def euclidian(v1, v2, axes):
        d = 0
        for axis in axes:
            d += (v1[axis] - v2[axis]) ** 2

        return d
