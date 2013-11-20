'''
Storage of the probes and probe object

@author: francois
'''
from threading import RLock
import http.client;
from consts import Consts, Identification
from exceptions import NoSuchProbe, ProbeConnection
from http.client import HTTPException

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
    def delProbe(c, probeID):
        with c.knownProbesLock:
            c.knownProbes[probeID].disconnect()
            c.knownProbes.pop(probeID)
    

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
    def getProbeById(c, probeId):
        with c.knownProbesLock:
            try :
                return c.knownProbes[probeId]
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
            return len([k for k, probe in cls.knownProbes.items() if probe.connected])

    @classmethod
    def getAllProbes(cls):
        with cls.knownProbesLock:
            return cls.knownProbes.values()

    @classmethod
    def getIdAllOtherProbes(cls):
        with cls.knownProbesLock:
            return [ probeId for probeId in cls.knownProbes.keys() if probeId != Identification.PROBE_ID]

    @classmethod
    def getKeys(cls):
        with cls.knownProbesLock:
            return cls.knownProbes.keys()


class Probe(object):
    '''
    Represents a probe
    '''
    def __init__(self, ID, IP):
        self.IP = IP
        self.ID = ID
        self.__connection = http.client.HTTPConnection(self.getIp(), Consts.PORT_NUMBER)
        self.connected = False
        
    def getIp(self):
        return self.IP

    def getId(self):
        return self.ID

    def connect(self):
        try:
            self.__connection.connect()
            self.connected = True
        except HTTPException:
            raise ProbeConnection("Connection to probe %s:%s failed" % (self.id, self.ip))

    def disconnect(self):
        self.__connection.close()
        self.connected = False

    def getConnection(self):
        return self.__connection
    
    def __getstate__(self):
        """Choose what to write when pickling"""
        return (self.ID, self.IP)

    def __setstate__(self, state):
        """Choose what to read when pickling"""
        self.ID, self.IP = state
