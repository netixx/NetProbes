'''
Module gathering the constants of the probe

@author: francois
'''

__all__ = ['Consts', 'Params', 'Identification']

import interfaces.inout.codecs as codecs
import interfaces.inout.protocols as protocols


class Consts(object):
    PROPAGATION_RATE = 5
    LOCAL_IP_ADDR = "localhost"
    DEFAULT_LOG_FORMAT = "%(levelname)s\t%(asctime)s %(threadName)s (%(module)s)\t: %(message)s"


class Params(object):
    '''Parameters for the runtime'''
    DEBUG = False
    COMMANDER = False
    WATCHERS = False
    MAX_OUTGOING_PROBETESTS = 5
    MAX_INCOMMING_PROBETESTS = 10
    MAX_STANDALONETESTS = 10
    CODEC = codecs
    PROTOCOL = protocols
    COMMANDER_PROTOCOL = protocols


class Identification(object):
    '''Identification elements of the probe'''

    PROBE_ID = "1122334455667788"

    @staticmethod
    def randomId():
        import random

        return '%05x' % random.randrange(16 ** 5)
