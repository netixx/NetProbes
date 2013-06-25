'''
Storage of the probes and probe object

@author: francois
'''
from threading import RLock
import http.client;
from consts import Consts, Identification
from exceptions import NoSuchProbe

class ProbeStorage(object):
    '''
    Stores all the Probes currently known by the current probe in a dictionnary
    Addition and deletion are thread safe implemented
    Contains the local probe (the probe of the computer it's running on)

    '''
    connectedProbes = {}
    connectedProbesLock = RLock()
        
    def __init__(self):
        pass

    @classmethod
    def delProbe(c, probeID):
        with c.connectedProbesLock:
            c.connectedProbes[probeID].getConnection().close()
            c.connectedProbes.pop(probeID)

    @classmethod
    def addProbe(c, probe):
        assert isinstance(probe, Probe)
        with c.connectedProbesLock:
            c.connectedProbes[probe.getId()] = probe

    @classmethod
    def getProbeById(c, probeId):
        with c.connectedProbesLock:
            try :
                return c.connectedProbes[probeId]
            except KeyError:
                raise NoSuchProbe

    @classmethod
    def closeAllConnections(cls):
        with cls.connectedProbesLock:
            for probeId in cls.connectedProbes.keys():
                cls.connectedProbes[probeId].getConnection().close()
            cls.connectedProbes.clear()
    
    @classmethod
    def numberOfConnections(cls):
        with cls.connectedProbesLock:
            return len(cls.connectedProbes)
    
    @classmethod
    def getAllProbes(cls):
        with cls.connectedProbesLock:
            return cls.connectedProbes.values()

    @classmethod
    def getIdAllOtherProbes(cls):
        with cls.connectedProbesLock:
            ret = []
            for probeId in cls.connectedProbes.keys():
                if (probeId != Identification.PROBE_ID):
                    ret.append(probeId)
            return ret

    @classmethod
    def getKeys(cls):
        with cls.connectedProbesLock:
            return cls.connectedProbes.keys()


class Probe(object):
    '''
    Represents a probe
    '''
    def __init__(self, ID, IP, status="connected"):
        self.IP = IP
        self.ID = ID
        self.status = status
        self.connection = http.client.HTTPConnection(self.getIp(), Consts.PORT_NUMBER)
        self.connection.connect();
        
    def getIp(self):
        return self.IP

    def getId(self):
        return self.ID

    def getConnection(self):
        return self.connection
