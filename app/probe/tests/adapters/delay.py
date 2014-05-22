"""Adapters for the unix Commands to measure delay related metrics"""

import re

from managers.tests import TestServices

class PingFail(Exception):
    pass


class PingParseError(Exception):
    pass


class Ping(object):
    """An interface to the ping unix command"""
    _ping_cmd = "ping -n {opts} {ip}"

    DEFAULT_OPTIONS = {
        'count' : 1,
        'interval' : 1,
        'packetSize' : 56,
        'ttl' : None,
        'deadline' : None,
        'timeout' : None,
    #     'sweepPacketSizeMax' : '',
    #     'sweepPacketSizeMin' : '',
    #     'sweepPacketSizeInc' : ''
    }

    _OPT_SWITCHES = {
        'count' : '-c',
        'packetSize' : '-s',
        'ttl' : 't',
        'deadline' : '-w',
        'timeout' : '-W',
        'interval' : '-i'
    }

    @classmethod
    def makePing(cls, ip, **options):
        opts = {}
        opts.update(cls.DEFAULT_OPTIONS)
        opts.update(options)
        opstr = ''
        for opt, val in opts.items():
            opstr += cls._addOption(opt, val)
        stdout, stderr = TestServices.runCmd(cls._ping_cmd.format(opts = opstr, ip = ip))
        # if isSweep:
        #     return cls._parseSweepPing(str(stdout.decode()))
        return cls._parsePing(str(stdout.decode()))

    @classmethod
    def _addOption(cls, opt, value):
        if value is not None:
            switch = cls._OPT_SWITCHES[opt]
            return " %s %s" % (switch, value)
        return ""

    @classmethod
    def _parsePing(cls, pingOutput):
        # Parse ping output and return all data.
        #         errorTuple = (1, 0, 0, 0, 0, 0)
        # Check for downed link
        r = r'[uU]nreachable'
        m = re.search(r, pingOutput)
        if m is not None:
            raise PingFail('Destination unreachable')
        r = r'(\d+) (?:packets? )?transmitted, (\d+) (?:packets? )?received'
        m = re.search(r, pingOutput)
        if m is None:
            raise PingParseError("Can not parse sent/received output %s" % pingOutput)
        sent, received = int(m.group(1)), int(m.group(2))
        r = r'(?:(?:rtt)|(?:round-trip)) min/avg/max/(?:m|(?:std))dev = '
        r += r'(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms'
        m = re.search(r, pingOutput)
        if m is None:
            raise PingParseError('Could not parse ping summary output: %s' % pingOutput)
        try:
            rttmin = float(m.group(1))
            rttavg = float(m.group(2))
            rttmax = float(m.group(3))
            rttdev = float(m.group(4))
        except:
            raise PingParseError(
                'Could not parse ping numbers : %s/%s/%s/%s' % (m.group(1), m.group(2), m.group(3), m.group(4)))
        return sent, received, rttmin, rttavg, rttmax, rttdev

    @classmethod
    def _parseSweepPing(cls, pingOutput):
        # Parse ping output and return all data.
        #         errorTuple = (1, 0, 0, 0, 0, 0)
        # Check for downed link
        r = r'[uU]nreachable'
        m = re.search(r, pingOutput)
        if m is not None:
            raise PingFail('Destination unreachable')
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
