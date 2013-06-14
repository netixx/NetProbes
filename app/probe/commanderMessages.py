'''
Created on 7 juin 2013

@author: francois
'''

class CommanderMessage(object):
    def __init__(self, targetId):
        self.targetId = targetId;

'''----- Network discovery CommanderMessages -----'''

class Add(CommanderMessage):
    ''' Mean "Go introduce yourself to this new probe" '''
    def __init__(self, targetId, probeID, probeIP):
        CommanderMessage.__init__(self, targetId)
        self.probeID = probeID
        self.probeIP = probeIP
    

'''----- Internal communication CommanderMessages -----'''

class Transfer(CommanderMessage):
    ''' Means  "Please send this CommanderMessage for me" '''
    def __init__(self, targetId, message):
        CommanderMessage.__init__(self, targetId)
        self.message = message

class Do(CommanderMessage):
    def __init__(self, targetId, test):
        CommanderMessage.__init__(self, targetId)
        self.test = test
