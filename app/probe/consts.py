"""Module gathering the "constants" of the probe
Consts are things that do not change on runtime
Params can be changed on runtime
Identification provides means to identify this probe

@author: francois
"""

__all__ = ['Consts', 'Params', 'Identification']

import interfaces.inout.codecs as codecs
import interfaces.inout.protocols as protocols


class Consts(object):
    """Constants for the program"""
    PROPAGATION_RATE = 5
    LOCAL_IP_ADDR = "localhost"
    DEFAULT_LOG_FORMAT = "%(levelname)s\t%(asctime)s %(threadName)s (%(module)s)\t: %(message)s"
    GET_REMOTE_ID_RETRY=4
    GET_REMOVE_ID_RETRY_INTERVAL=2
    SEND_RETRY=2
    SEND_RETRY_INTERVAL=1



class Params(object):
    """Parameters for the runtime"""
    VERBOSE = 0
    COMMANDER = False
    WATCHERS = False
    MAX_OUTGOING_PROBETESTS = 5
    MAX_INCOMING_PROBETESTS = 10
    MAX_STANDALONETESTS = 10
    CODEC = codecs
    PROTOCOL = protocols


class Identification(object):
    """Identification elements of the probe"""

    PROBE_ID = "1122334455667788"

    @staticmethod
    def randomId():
        """Generate a random ID for this probe"""
        import random
        return '%05x' % random.randrange(16 ** 5)
