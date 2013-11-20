'''
Created on 17 juin 2013

@author: francois
'''

class Probe(object):

    def __init__(self, ID, IP, status = "None"):
        self.IP = IP
        self.ID = ID
        self.status = status

    def getIp(self):
        return self.IP

    def getId(self):
        return self.ID

    def getStatus(self):
        return self.status

class ProbeStatus(object):
    LOCAL = "local"
    ADDED = "added"
    CONNECTED = "connected"
    READY = "ready"
    LOST = "lost"
    TEST_IN_PROGRESS = "test in progress"

def statusFactory(status):
    return ", ".join(status)
