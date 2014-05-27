"""
Storage of the probes = dict of probes known to this probe
Probe object = description of a probe
ProbeConnections = methods to create, open and close a connection to a probe

@author: francois
"""
from threading import RLock

from consts import Consts, Identification
from interfaces.excs import NoSuchProbe


class ProbeStorage(object):
    """ Stores all the Probes currently known by the current probe in a (python) dictionary
    Addition and deletion are thread safe implemented
    Contains the local probe (the probe of the computer it's running on)

    """
    knownProbes = {}
    __knownProbesLock = RLock()

    """Query methods"""

    @classmethod
    def isKnownId(cls, probeId):
        """Is this ID in dict ?
        :param probeId: the ID of the probe to look for
        """
        with cls.__knownProbesLock:
            return probeId in cls.knownProbes.keys()

    @classmethod
    def isKnownIp(cls, ip):
        """Is this IP in dict
        :param ip: the ip to look for"""
        with cls.__knownProbesLock:
            return ip in [p.getIp() for p in cls.knownProbes.values()]

    @classmethod
    def getProbeById(cls, probeId):
        """Returns a probe by it's id
        :param probeId: id of the probe to look for"""
        with cls.__knownProbesLock:
            try:
                return cls.knownProbes[probeId]
            except KeyError as e:
                raise NoSuchProbe(e)

    @classmethod
    def getConnectedProbes(cls):
        """Returns the probe whose connection is active"""
        return [k for k, probe in cls.knownProbes.items() if probe.connected]

    @classmethod
    def getAllProbes(cls):
        """Returns all currently known probes"""
        with cls.__knownProbesLock:
            return cls.knownProbes.values()

    @classmethod
    def getIdAllProbes(cls):
        """Returns IDs of all the probes"""
        with cls.__knownProbesLock:
            return [p.getId() for p in cls.knownProbes.values()]

    @classmethod
    def getAllOtherProbes(cls):
        """Returns IDs of all the probes except your own"""
        with cls.__knownProbesLock:
            return [probe for probe in cls.knownProbes.values() if probe.getId() != Identification.PROBE_ID]

    @classmethod
    def getIdAllOtherProbes(cls):
        """Returns the IDs of all the probes except your own"""
        with cls.__knownProbesLock:
            return [probeId for probeId in cls.knownProbes.keys() if probeId != Identification.PROBE_ID]

    @classmethod
    def getIpAllOtherProbes(cls):
        """Returns the ip address of all the probes except your own"""
        with cls.__knownProbesLock:
            return [p.getIp() for p in cls.knownProbes.values() if p.getId() != Identification.PROBE_ID]

    ###Table manipulation methods

    @classmethod
    def addProbe(cls, probe):
        """Add a probe to the index
        :param probe: Probe object to add
        """
        assert isinstance(probe, Probe)
        with cls.__knownProbesLock:
            cls.knownProbes[probe.getId()] = probe


    @classmethod
    def delProbeById(cls, probeid):
        """Remove probe by it's ID"""
        with cls.__knownProbesLock:
            try:
                ProbeConnections.disconnectProbe(cls.knownProbes[probeid])
                cls.knownProbes.pop(probeid)
            except KeyError:
                raise NoSuchProbe()

    @classmethod
    def clearAllProbes(cls):
        """Remove all probes from dict"""
        cls.closeAllConnections()
        cls.knownProbes.clear()

    @staticmethod
    def newProbe(idProbe, ip):
        """Factory to create a new probe"""
        return Probe(idProbe, ip)

    @classmethod
    def addSelfProbe(cls):
        """Add the local probe to the index"""
        cls.addProbe(cls.newProbe(Identification.PROBE_ID, Consts.LOCAL_IP_ADDR))

    @classmethod
    def getNumberOfProbes(cls):
        with cls.__knownProbesLock:
            return len(cls.knownProbes)

    ###Connection methods

    @classmethod
    def connectToProbe(cls, probeId):
        """Create connection the probe probe with given id
        :param probeId: id of the probe to connect to
        """
        probe = cls.getProbeById(probeId)
        if not probe.connected:
            ProbeConnections.connectToProbe(probe)

    @classmethod
    def disconnectFromProbe(cls, probeId):
        """Sever connection to the given probe
        :param probeId : id of the probe to disconnect from
        """
        probe = cls.getProbeById(probeId)
        if probe.connected:
            ProbeConnections.disconnectProbe(probe)

    @classmethod
    def closeAllConnections(cls):
        """Sever all connection to probes"""
        with cls.__knownProbesLock:
            for probeId in cls.knownProbes.keys():
                cls.disconnectFromProbe(probeId)


class Probe(object):
    """Represents a probe.
    A probe is basically an (ip) address, an ID and a connection
    """

    def __init__(self, idProbe, address):
        self.address = address
        self.id = idProbe
        self.connection = None
        self.connected = False
        self.getAddress = self.getIp

    def getIp(self):
        """Returns this probe's (ip) address"""
        return self.address

    def getId(self):
        """Returns this probe's id"""
        return self.id

    def __getstate__(self):
        """Choose what to write when pickling"""
        return self.id, self.address

    def __setstate__(self, state):
        """Choose what to read when pickling"""
        self.id, self.address = state


from consts import Params
from interfaces.excs import ProbeConnectionException


class ProbeConnections(object):
    """Manages connection to probes. Connects and disconnect basically"""

    @classmethod
    def connectToProbe(cls, probe):
        """Connect to this probe
        :param probe: Probe to connect to
        """
        if probe.connection is None:
            probe.connection = Params.PROTOCOL.createConnection(probe)
        try:
            Params.PROTOCOL.connect(probe.connection)
            probe.connected = True
        except ProbeConnectionException:
            raise ProbeConnectionException("Connection to probe %s:%s failed" % (probe.id, probe.address))


    @classmethod
    def disconnectProbe(cls, probe):
        """Disconnect from this probe (only if we are not connected...
        :param probe: Probe to disconnect from"""
        try:
            if probe.connected:
                Params.PROTOCOL.disconnect(probe.connection)
                probe.connected = False
        except:
            probe.connected = False
