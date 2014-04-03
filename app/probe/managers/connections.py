'''
Created on 26 nov. 2013

@author: francois
'''

from .probes import ProbeStorage as ps
from inout.client import Client
from calls.messages import StatusRequest

class ProbeConnections(object):

    @classmethod
    def getStatusConnectedProbes(cls):
        for probe in ps.getConnectedProbes():
            Client.send(StatusRequest(probe.getId()))

