"""Objects useful for representing probes to the user

@author: francois
"""


class Probe(object):
    """Representation of a probe to be sent and displayed to the
    user"""

    def __init__(self, ID, IP, status = "None"):
        self.IP = IP
        self.ID = ID
        self.status = status

    def getIp(self):
        """Return the IP of the probe"""
        return self.IP

    def getId(self):
        """Return the ID of the probe"""
        return self.ID

    def getStatus(self):
        """Return the status list for the probe"""
        return self.status


class ProbeStatus(object):
    """Different status that a probe can have
    A probe can have on or more of those statuses"""
    LOCAL = "local"
    ADDED = "added"
    CONNECTED = "connected"
    READY = "ready"
    LOST = "lost"
    TEST_IN_PROGRESS = "test in progress"


def statusFactory(status):
    """A factory to generate status string from given status list
    :param status: status list to generate the string from
    """
    return ", ".join(status)
