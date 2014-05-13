"""
Implementation of a multicast test

"""
__all__ = ['TesterMulticast', 'TesteeMulticast']

import socket
import argparse
import struct

from consts import Identification
from interfaces.excs import TestArgumentError
from interfaces.probetest import Report, TesterTest, TesteeTest


name = "Multicast"


class Multicast(object):
    ENCODING = "latin1"
    DEFAULT_PORT = 6789
    DEFAULT_TIMEOUT = 3.0
    DEFAULT_TTL = 20
    DEFAULT_BCAST_ADDRESS = "224.1.1.1"
    messageSend = "Multicast Test"

    def __init__(self):
        self.socket = None
        self.port = self.DEFAULT_PORT
        self.timeout = self.DEFAULT_TIMEOUT
        self.ttl = self.DEFAULT_TTL
        self.broadcast_address = self.DEFAULT_BCAST_ADDRESS
        self.options = None
        self.name = name

    def getName(self):
        return name

    ### Methods for the probe which starts the test###
    ###
        # Parse the options for the current test
        # should populate at least the targets list
    ###

    def parseOptions(self):
        parser = argparse.ArgumentParser(description = "Parses the multicast test target")
        parser.add_argument('targets', metavar = 'targets', nargs = "+")
        parser.add_argument('--port', type = int, metavar = 'port', default = self.port)
        parser.add_argument('--timeout', metavar = 'timeout', default = self.timeout, type = float)
        parser.add_argument('--ttl', metavar = 'ttl', default = self.ttl, type = int)
        parser.add_argument('-ma', '--m-address', metavar = 'multicast-address', default = self.broadcast_address)

        try:
            opts = parser.parse_args(self.opts)
            self.targets = opts.targets
            self.options = opts
        except (argparse.ArgumentError, SystemExit):
            raise TestArgumentError(parser.format_usage())


class TesterMulticast(TesterTest, Multicast):
    def __init__(self, options):
        Multicast.__init__(self)
        TesterTest.__init__(self, options)
        self.parseOptions()

    ###
    ###    Prepare yourself for the test
    ###

    def doPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', self.options.ttl))

    ###
    ###    Does the actual test
    ###

    def doTest(self):
        self.logger.info("Starting test / Sending message")
        self.socket.sendto(self.messageSend.encode(self.ENCODING), (self.options.m_address, self.options.port))


    ###
    ###    Prepare yourself for finish
    ###

    def doOver(self):
        self.socket.close()

    ###
    ###    Generate the result of the test given the set of reports from the tested probes
    ###    Should populate self.result
    ###

    def doResult(self, reports):
        ok = []
        fail = []
        for probeId, report in reports.items():
            if not report.isSuccess:
                fail.append(probeId)
            else:
                ok.append(probeId)

        if len(ok) == len(reports):
            self.result = "Ok, probe replied successfully."
        else:
            self.result = "Fail, probe did not receive the message."

        self.result += "\n Id ok : " + ", ".join(ok) + "\n Id fail : " + ", ".join(fail)


class TesteeMulticast(TesteeTest, Multicast):
    def __init__(self, options, testId):
        Multicast.__init__(self)
        TesteeTest.__init__(self, options, testId)
        self.parseOptions()
        self.msgReceived = False

    ###
    ###     Actions that the probe must perform in order to be ready
    ###

    def replyPrepare(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', self.options.port))

        ### Add probe to multicast group (IGMP)
        self.logger.debug("Trying to add probe to multicast group")
        group = socket.inet_aton(self.options.m_address)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.logger.info("Added Probe to multicast group")


    ###
    ###    Actions that must be taken when the probe received the test
    ###

    def replyTest(self):
        self.logger.info("Waiting for message")
        try:
            self.socket.settimeout(self.options.timeout)
            msg, address = self.socket.recvfrom(len(self.messageSend))
            msg = msg.decode(self.ENCODING)
            self.logger.info("Message received")
            self.msgReceived = msg == self.messageSend
        except socket.timeout:
            self.msgReceived = False
            self.logger.warning("ReplyTest -> socket timeout")
        except:
            self.msgReceived = False
            self.logger.warning("ReplyTest -> unknown error", exc_info = 1)


    ###
    ###    Actions that the probe must perform when the test is over
    ###    generates the report and returns it!!!
    ###

    def replyOver(self):
        self.socket.close()
        report = Report(Identification.PROBE_ID)
        report.isSuccess = self.msgReceived
        return report
