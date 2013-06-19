'''
Created on 7 juin 2013

@author: francois
'''

class CommanderMessage(object):
    def __init__(self, targetId):
        self.targetId = targetId;


class Add(object):
    def __init__(self, targetIp):
        self.targetIp = targetIp


class Do(CommanderMessage):
    def __init__(self, targetId, test):
        CommanderMessage.__init__(self, targetId)
        self.test = test


class Delete(CommanderMessage):
    def __init__(self, targetId):
        CommanderMessage.__init__(self, targetId)
    
