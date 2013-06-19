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


class Transfer(CommanderMessage):
    def __init__(self, targetId, message):
        CommanderMessage.__init__(self, targetId)
        self.message = message

class Do(CommanderMessage):
    def __init__(self, targetId, test):
        CommanderMessage.__init__(self, targetId)
        self.test = test
