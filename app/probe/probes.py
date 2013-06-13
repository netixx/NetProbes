'''
Created on 13 juin 2013

@author: francois
'''
from threading import RLock
import http.client;
from consts import Consts


class ProbeStorage(object):
    dicoIPID = {}
    dicoConnection = {}
    connectedProbes = {}
    connectedProbesLock = RLock()
        
    def __init__(self):
        pass

    @classmethod
    def delProbe(c, probeID):
        with c.connectedProbesLock:
            c.dicoIPID.pop(probeID)
            c.dicoConnection[probeID].close()
            c.dicoConnection.pop(probeID)

    @classmethod
    def addProbe(c, probe):
        assert isinstance(probe, Probe)
        with c.connectedProbesLock:
            c.dicoIPID[probe.getId()] = probe.getIp()
            c.dicoConnection[probe.getId()] = http.client.HTTPConnection(probe.getIp(), Consts.PORT_NUMBER)
            c.dicoConnection[probe.getId()].connect()
            c.connectedProbes[probe.getId] = probe

    @classmethod
    def getProbeById(c, probeId):
        with c.connectedProbesLock:
            return c.connectedProbes.get(probeId)


class Probe(object):

    def __init__(self, ID, IP, status="connected"):
        self.IP = IP
        self.ID = ID
        self.status = status
        
    def getIp(self):
        return self.IP

    def getId(self):
        return self.ID
