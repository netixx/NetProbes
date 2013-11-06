class Message(object):
    '''  Super class to implement a message between probes  '''
    def __init__(self, targetId):
        self.targetId = targetId;
    
    def setTarget(self, targetId):
        self.targetId = targetId


'''----- Network discovery messages -----'''

class Add(Message):
    '''
    Message to add a new probe
    If the hello flag is set to true, then the recepient of
    the message is expected to send a hello message to the probe (probeId, probeIp)

    '''
    def __init__(self, targetId, probeID, probeIP, hello=False):
        Message.__init__(self, targetId)
        self.probeID = probeID
        self.probeIP = probeIP
        self.doHello = hello
    
    def getHello(self):
        return self.doHello


class Hello(Message):
    '''
    Means " Hello, my name is myId"
    Enables the contacted probe (targetId, remoteIp) to add the probe with id myId to the list of known probes

    '''
    def __init__(self, targetId, myId, remoteIp=None):
        Message.__init__(self, targetId)
        self.myId = myId
        self.remoteIP = remoteIp
        
    def setRemoteIP(self, remoteIP):
        self.remoteIP = remoteIP
        
    def getRemoteIP(self):
        return self.remoteIP
    
    def getRemoteID(self):
        return self.myId
    
class Bye(Message):
    ''' Means "I am leaving the system" '''
    def __init__(self, targetId, leavingId):
        Message.__init__(self, targetId)
        self.leavingId = leavingId
        
    def getLeavingID(self):
        return self.leavingId


'''----- Messages to manage tests -----'''

class TestMessage(Message):
    def __init__(self, targetId, testId):
        super().__init__(targetId)
        self.testId = testId

    def getTestId(self):
        return self.testId

class Prepare(TestMessage):
    ''' Means "Get ready for the given test, stop processing other messages and answer when you're ready" '''
    def __init__(self, targetId, testId, sourceId, testOptions):
        super().__init__(targetId, testId)
        self.sourceId = sourceId
        self.testOptions = testOptions

    def getSourceId(self):
        return self.sourceId

    def getTestOptions(self):
        return self.testOptions

'''----- Messages send by the probe starting the test after its been started-----'''


class TesterMessage(TestMessage):
    pass

class Over(TesterMessage):
    ''' Means "Test is over, give me your report" '''
    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)

class Abort(TesterMessage):
    ''' Means "Never mind, this test is cancelled, forget about it, resume answering to other messages" '''
    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)
        
'''
    An answers from the probe being tested
'''
class TesteeAnswer(TestMessage):
    pass

class Ready(TesteeAnswer):
    ''' Means "I'm ready to perform your test, I won't answer to other messages and my sockets/whatever are ready" '''
    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)


class Result(TesteeAnswer):
    ''' Means "You initiated a test, here are the results". Often comes in response to a Over message'''
    def __init__(self, targetId, testId, sourceId, report):
        super().__init__(targetId, testId)
        self.report = report
        self.sourceId = sourceId
        
    def getReport(self):
        return self.report

    def getSourceId(self):
        return self.sourceId
