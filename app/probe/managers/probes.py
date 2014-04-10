'''
Storage of the probes and probe object

@author: francois
'''
from threading import RLock
from consts import Consts, Identification
from exceptions import NoSuchProbe

class ProbeStorage(object):
    '''
    Stores all the Probes currently known by the current probe in a dictionnary
    Addition and deletion are thread safe implemented
    Contains the local probe (the probe of the computer it's running on)

    '''
    knownProbes = {}
    knownProbesLock = RLock()
        
    def __init__(self):
        pass

    @classmethod
    def delProbeById(c, probeid):
        with c.knownProbesLock:
            c.knownProbes[probeid].disconnect()
            c.knownProbes.pop(probeid)
    

    @classmethod
    def addProbe(cls, probe):
        assert isinstance(probe, Probe)
        with cls.knownProbesLock:
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
        with cls.knownProbesLock:
            try :
                return cls.knownProbes[probeId]
            except KeyError:
                raise NoSuchProbe

    @classmethod
    def closeAllConnections(cls):
        with cls.knownProbesLock:
            for probeId in cls.knownProbes.viewkeys():
                cls.disconnectFromProbe(probeId)

    @classmethod
    def clearAllProbes(cls):
        cls.closeAllConnections()
        cls.knownProbes.clear()

    @classmethod
    def numberOfConnections(cls):
        with cls.knownProbesLock:
            return len(cls.getConnectedProbes())
    
    @classmethod
    def getConnectedProbes(cls):
        return [k for k, probe in cls.knownProbes.items() if probe.connected]
    
    @classmethod
    def getAllProbes(cls):
        with cls.knownProbesLock:
            return cls.knownProbes.values()

    @classmethod
    def getAllOtherProbes(cls):
        with cls.knownProbesLock:
            return [ probe for probe in cls.knownProbes.values() if probe.getId() != Identification.PROBE_ID]

    @classmethod
    def getIdAllOtherProbes(cls):
        with cls.knownProbesLock:
            return [ probeId for probeId in cls.knownProbes.keys() if probeId != Identification.PROBE_ID]

    @classmethod
    def getKeys(cls):
        with cls.knownProbesLock:
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
from exceptions import ProbeConnectionException

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
