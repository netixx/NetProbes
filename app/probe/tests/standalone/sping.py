"""
Implementation of a unicast test
Protocols tcp and udp are supported

"""
__all__ = ['Ping']

import argparse
from threading import Thread, Semaphore

from interfaces.standalonetest import Test
from interfaces.excs import TestError, TestArgumentError
from tests.adapters import delay

name = "Sping"

#TODO: enable either IPs or names
class PingFail(TestError):
    pass


class PingParseError(TestError):
    pass


class Sping(Test):
    npings = 1
    maxThreads = 100

    def __init__(self, options):
        super().__init__(options)
        self.options = None
        self.stats = None
        self.isSweep = False
        self.parallelPing = False
        self.parseOptions()
        self.errors = {}
        self.semaphore = Semaphore(self.maxThreads)


    def parseOptions(self):
        # ping -c 3 -t 30 -m 10 -W 2 -s 50 -i 1 -D
        parser = argparse.ArgumentParser(prog = name,
                                         description = "Parses the ping test options")
        parser.add_argument('targets',
                            metavar = 'TARGETS',
                            nargs = "+")
        parser.add_argument('--parallel',
                            dest = 'parallel',
                            default = False,
                            action = 'store_true',
                            help = 'Do ping on multiple targets in parallel')
        # option for ping reciprocity
        # regular ping options
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
        # parser.add_argument('-T',
        #                     metavar = 'TTL',
        #                     dest = 'multicastTtl',
        #                     type = int,
        #                     help = 'Set IP TTL value for multicast packets')
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

        # sweepParamsGrp.add_argument('-G',
        #                             metavar = 'SWEEP_MAX_SIZE',
        #                             dest = 'swpMaxSize',
        #                             type = int,
        #                             help = 'Maximum size of payload when sweeping'
        # )
        # sweepParamsGrp.add_argument('-g',
        #                             metavar = 'SWEEP_MIN_SIZE',
        #                             dest = 'swpMinSize',
        #                             type = int,
        #                             help = 'Size of payload to start sweeping')
        # sweepParamsGrp.add_argument('-H',
        #                             metavar = 'SWEEP_INC_SIZE',
        #                             type = int,
        #                             dest = 'swpIncSize',
        #                             help = 'Payload size increment for each sweep')
        parser.add_argument('-i',
                            metavar = "WAIT_TIME",
                            dest = 'waitSend',
                            type = float,
                            help = 'Time to wait between sending ping')
        # parser.add_argument('-D',
        #                     #                             metavar = "DON'T_FRAGMENT",
        #                     dest = 'df',
        #                     action = 'store_true',
        #                     help = "Set the don't fragment bit")

        try:
            opts = parser.parse_args(self.opts)
            self.targets = opts.targets
            self.options = {
                'count': opts.nPings,
                'deadline': opts.timeout,
                'ttl': opts.ipTtl,
                'packetSize': opts.packetSize,
                'timeout': opts.waitReply,
            }
            self.parallelPing = opts.parallel
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())

    rformat = "Ping statistics for %s : %s\n"
    eformat = "Ping failed %s"

    '''
        Does the actual test
    '''

    def doTest(self):
        self.logger.info("Starting test")

        self.stats = {}
        self.psuccess = {}
        self.perrors = {}
        # self.threads = []
        for target in self.targets:
            try:
                if self.parallelPing:
                    self.semaphore.acquire()
                    t = Thread(target = self.makeAPing, args = [target], name = "Ping-%s" % target)
                    # self.threads.append(t)
                    t.start()
                else:
                    self.makeAPing(target)
            except PingFail as e:
                # TODO: self.stats[target] = e ?
                self.perrors[target] = e
                self.psuccess[target] = True
            except (PingParseError, Exception) as e:
                self.psuccess[target] = False
                self.perrors[target] = TestError(e)
        if self.parallelPing:
            for _ in range(self.maxThreads):
                self.semaphore.acquire()
            # for t in self.threads:
            #     t.join()


    def makeAPing(self, probeIp):
        try:
            r = delay.Ping.makePing(probeIp, **self.options)
            # if self.isSweep:
            #     self.stats[probeIp] = SweepStats(*r)
            # else:
            self.stats[probeIp] = PingStats(*r)
            self.psuccess[probeIp] = True
        except delay.PingFail as e:
            raise PingFail(e)
        except delay.PingParseError as e:
            raise PingParseError(e)
        finally:
            self.semaphore.release()

    ###
    ###    Generate the result of the test given the set of reports from the tested probes
    ###    Should populate self.result
    ###

    def doResult(self):
        self.result = ""
        self.errors = ""
        for target in self.targets:
            if not self.psuccess[target]:
                self.result += str(self.perrors[target])
            else:
                if target in self.perrors and self.perrors[target] is not None:
                    self.result += self.eformat % (target, self.perrors[target])
                else:
                    self.result += self.rformat % (target, self.stats[target].printAll())
                    #         self.rawResult = self.errors
        self.rawResult = self.stats


#         else:
#             raise TestError(self.errors)

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
        rtt min/avg/max/mdev : %s/%s/%s/%s ms""" % (
            self.sent, self.received, self.rttmin, self.rttavg, self.rttmax, self.rttdev)


class SweepStats(object):
    def __init__(self, sent, received, packetsDetails):
        self.sent = sent
        self.received = received
        self.packets = packetsDetails

    def printAll(self):
        return """Packets sent : %s, packets received : %s
        size received : %s""" % (self.sent, self.received, ", ".join([str(p[1]) for p in self.packets]))
