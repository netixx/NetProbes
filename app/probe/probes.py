'''
Created on 13 juin 2013

@author: francois
'''
from threading import RLock
import http.client;
from consts import Consts
from exceptions import NoSuchProbe

'''
    Stores all the Probes currently known by the current probe in a dictionnary
    Addition and deletion are thread safe implemented
    Contains the local probe (the probe of the computer it's running on)
'''
class ProbeStorage(object):
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
        for probeId in cls.connectedProbes.keys():
            cls.delProbe(probeId)
    
    @classmethod
    def numberOfConnections(cls):
        return len(cls.connectedProbes)
    


'''
    Represents a probe
'''
class Probe(object):

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
