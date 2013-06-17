'''
Created on 17 juin 2013

@author: francois
'''

class Probe(object):

    def __init__(self, ID, IP, status="connected"):
        self.IP = IP
        self.ID = ID
        self.status = status

    def getIp(self):
        return self.IP

    def getId(self):
        return self.ID
