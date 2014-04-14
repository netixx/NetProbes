'''
Storage of the probes and probe object

@author: francois
'''
from threading import RLock
from consts import Consts, Identification
from interfaces.excs import NoSuchProbe

class ProbeStorage(object):
    '''
    Stores all the Probes currently known by the current probe in a dictionnary
    Addition and deletion are thread safe implemented
    Contains the local probe (the probe of the computer it's running on)

    '''
    knownProbes = {}
    __knownProbesLock = RLock()
        
    def __init__(self):
        pass
    
    @classmethod
    def isKnownId(cls, probeId):
        with cls.__knownProbesLock:
            return probeId in cls.knownProbes.keys()

    @classmethod
    def isKnownIp(cls, ip):
        with cls.__knownProbesLock:
            return ip in [p.getIp() for p in cls.knownProbes.values()]

    @classmethod
    def delProbeById(c, probeid):
        with c.__knownProbesLock:
            try:
                Params.PROTOCOL.disconnect(c.knownProbes[probeid].connection)
                c.knownProbes.pop(probeid)
            except KeyError:
                raise NoSuchProbe()
    

    @classmethod
    def addProbe(cls, probe):
        assert isinstance(probe, Probe)
        with cls.__knownProbesLock:
            cls.knownProbes[probe.getId()] = probe

    @classmethod
    def connectToProbe(cls, probeId):
        probe = cls.getProbeById(probeId)
        if not probe.connected:
            ProbeConnections.connectToProbe(probe)

    @classmethod
    def disconnectFromProbe(cls, probeId):
        probe = cls.getProbeById(probeId)
        if probe.connected:
            ProbeConnections.disconnectProbe(probe)

    @classmethod
    def getProbeById(cls, probeId):
        with cls.__knownProbesLock:
            try :
                return cls.knownProbes[probeId]
            except KeyError as e:
                raise NoSuchProbe(e)

    @classmethod
    def closeAllConnections(cls):
        with cls.__knownProbesLock:
            for probeId in cls.knownProbes.keys():
                cls.disconnectFromProbe(probeId)

    @classmethod
    def clearAllProbes(cls):
        cls.closeAllConnections()
        cls.knownProbes.clear()

    @classmethod
    def numberOfConnections(cls):
        with cls.__knownProbesLock:
            return len(cls.getConnectedProbes())
    
    @classmethod
    def getConnectedProbes(cls):
        return [k for k, probe in cls.knownProbes.items() if probe.connected]
    
    @classmethod
    def getAllProbes(cls):
        with cls.__knownProbesLock:
            return cls.knownProbes.values()
    @classmethod
    def getIdAllProbes(cls):
        with cls.__knownProbesLock:
            return [p.getId() for p in cls.knownProbes.values()]

    @classmethod
    def getAllOtherProbes(cls):
        with cls.__knownProbesLock:
            return [ probe for probe in cls.knownProbes.values() if probe.getId() != Identification.PROBE_ID]

    @classmethod
    def getIdAllOtherProbes(cls):
        with cls.__knownProbesLock:
            return [ probeId for probeId in cls.knownProbes.keys() if probeId != Identification.PROBE_ID]

    @classmethod
    def getKeys(cls):
        with cls.__knownProbesLock:
            return cls.knownProbes.keys()
        
    @staticmethod
    def newProbe(idProbe, ip):
        return Probe(idProbe, ip)
        
    @classmethod
    def addSelfProbe(cls):
        cls.addProbe(cls.newProbe(Identification.PROBE_ID, Consts.LOCAL_IP_ADDR))


class Probe(object):
    '''
    Represents a probe
    '''
    def __init__(self, idProbe, ip):
        self.ip = ip
        self.id = idProbe
        self.connection = None
        self.connected = False
        
    def getIp(self):
        return self.ip

    def getId(self):
        return self.id

    def __getstate__(self):
        """Choose what to write when pickling"""
        return (self.id, self.ip)

    def __setstate__(self, state):
        """Choose what to read when pickling"""
        self.id, self.ip = state

from consts import Params
from interfaces.excs import ProbeConnectionException

class ProbeConnections(object):

    @classmethod
    def connectToProbe(cls, probe):
        if probe.connection is None:
            probe.connection = Params.PROTOCOL.createConnection(probe)
        try:
            Params.PROTOCOL.connect(probe.connection)
            probe.connected = True
        except:
            raise ProbeConnectionException("Connection to probe %s:%s failed" % (probe.id, probe.ip))

        probe.connection.connect()
        probe.connected = True

    @classmethod
    def disconnectProbe(cls, probe):
        try :
            Params.PROTOCOL.disconnect(probe.connection)
            probe.connected = False
        except:
            probe.connected = False
