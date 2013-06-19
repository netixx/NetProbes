'''
Created on 7 juin 2013

@author: francois

Add
Hello




'''


class Message(object):
    '''  Super class to implement a message between probes  '''
    def __init__(self, targetId):
        self.targetId = targetId;
    
    def setTarget(self, targetId):
        self.targetId = targetId



'''----- Network discovery messages -----'''

class Add(Message):
    ''' Mean "Go introduce yourself to this new probe" '''
    def __init__(self, targetId, probeID, probeIP, hello=False):
        Message.__init__(self, targetId)
        self.probeID = probeID
        self.probeIP = probeIP
        self.doHello = hello
    
    def getHello(self):
        return self.doHello


class Hello(Message):
    '''  Means " Hello, my name is myId" ''' 
    def __init__(self, targetId, myId):
        Message.__init__(self, targetId)
        self.myId = myId
        self.remoteIP = None
        
    def setRemoteIP(self, remoteIP):
        self.remoteIP = remoteIP
        
    def getRemoteIP(self):
        return self.remoteIP
    
    def getRemoteID(self):
        return self.myId
    
    

class Hi(Message):
    '''  Means "Hi, I have now met you" ''' 
    def __init__(self, targetId, myId):
        Message.__init__(self, targetId)
        self.myId = myId
        

class Bye(Message):
    ''' Means "Sorry, I'm leaving, forget me" '''
    ''' Could also mean "This probe has left, forget it" '''
    def __init__(self, targetId, myId):
        Message.__init__(self, targetId)
        self.myId = myId



'''----- Internal communication messages -----'''

class Transfer(Message):
    ''' Means  "Please send this message for me" '''
    def __init__(self, targetId, message):
        Message.__init__(self, targetId)
        self.message = message



'''----- Messages to manage tests -----'''

class Prepare(Message):
    ''' Means "Get ready for the given test, stop processing other messages and answer when you're ready" '''
    def __init__(self, targetId):
        Message.__init__(self, targetId)
    


class Ready(Message):
    ''' Means "I'm ready to perform your test, I won't answer to other messages" '''
    def __init__(self, targetId):
        Message.__init__(self, targetId)



class Abort(Message):
    ''' Means "Never mind, this test is cancelled, forget about it, resume answering to other messages" '''
    def __init__(self, targetId):
        Message.__init__(self, targetId)

class Over(Message):
    ''' Means "I no longer need you for this test, forget about it, resume answering to other messages" '''
    def __init__(self, targetId):
        Message.__init__(self, targetId)


class Result(Message):
    ''' Means "You initiated a test, here are the results" '''
    def __init__(self, targetId):
        Message.__init__(self, targetId)




