'''
Created on 7 juin 2013

@author: francois
'''


class CommanderMessage(object):
    def __init__(self, targetId):
        self.targetId = targetId;


'''Adds a probe in the directory of available probes'''


class Add(CommanderMessage):
    def __init__(self, targetId, targetIp):
        super().__init__(targetId)
        self.targetIp = targetIp


class Do(CommanderMessage):
    def __init__(self, targetId, test, testOptions = None):
        CommanderMessage.__init__(self, targetId)
        self.test = test
        self.testOptions = testOptions


class Delete(CommanderMessage):
    def __init__(self, targetId):
        CommanderMessage.__init__(self, targetId)
