'''
Storage of the probes and probe object

@author: francois
'''
from threading import RLock
import http.client;
from consts import Consts, Identification
from exceptions import NoSuchProbe, ProbeConnection
from http.client import HTTPException, NotConnected

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
            probe.getConnection().connect()

    @classmethod
    def disconnectFromProbe(cls, probeId):
        probe = cls.getProbeById(probeId)
        if probe.connected:
            probe.getConnection().close()

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
            for probeId in cls.knownProbes.keys():
                cls.knownProbes[probeId].disconnect()

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
        self.__connection = http.client.HTTPConnection(self.getIp(), Consts.PORT_NUMBER)
        self.connected = False
        
    def getIp(self):
        return self.ip

    def getId(self):
        return self.id

    def connect(self):
        try:
            self.__connection.connect()
            self.connected = True
        except HTTPException:
            raise ProbeConnection("Connection to probe %s:%s failed" % (self.id, self.ip))

    def disconnect(self):
        try :
            self.__connection.close()
            self.connected = False
        except NotConnected:
            self.connected = False

    def getConnection(self):
        return self.__connection
    
    def __getstate__(self):
        """Choose what to write when pickling"""
        return (self.id, self.ip)

    def __setstate__(self, state):
        """Choose what to read when pickling"""
        self.id, self.ip = state
