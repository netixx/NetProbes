'''
Message to exchange information between probes
    Messages sent over the network to other probes

The messages are serialized before being sent and unserialized when received
They are then matched to the corresponding Action by the messagetoaction class

'''

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
    If the hello flag is set to true, then the recipient of
    the message is expected to send a hello message to the probe (probeId, probeIp)

    '''
    def __init__(self, targetId, probeID, probeIP, doHello = False):
        Message.__init__(self, targetId)
        self.probeID = probeID
        self.probeIP = probeIP
        self.doHello = doHello
    
class Connect(Message):
    '''Establish a connection to a probe so that tests can be performed with this probe'''
    def __init__(self, targetId):
        Message.__init__(self, targetId)
        self.targetId = targetId


class Hello(Message):
    '''
    Tells a new probe about all other probes

    '''
    def __init__(self, targetId, probeList, sourceId):
        Message.__init__(self, targetId)
        self.probeList = probeList
        self.remoteIp = None
        self.sourceId = sourceId

    def getProbeList(self):
        return self.probeList
    
    def setRemoteIp(self, ip):
        self.remoteIp = ip

class Bye(Message):
    ''' Means "I am leaving the system" '''

    def __init__(self, targetId, leavingId):
        Message.__init__(self, targetId)
        self.leavingId = leavingId
        
    def getLeavingID(self):
        return self.leavingId


class BroadCast(Message):
    '''Encapsulation of a given message as payload
        This allows broadcast of a message through (a subset of) the overlay
    @see: Client class for algorithmic implementation of the Broadcast

    '''
    def __init__(self, targetId, payload, propagateTo = []):
        Message.__init__(self, targetId)
        self.propagate = propagateTo
        self.payload = payload

    def getNextTargets(self):
        return self.propagate

    def getMessage(self):
        return self.payload

'''----- Messages to manage tests -----'''

class TestMessage(Message):
    def __init__(self, targetId, testId):
        super().__init__(targetId)
        self.testId = testId

    def getTestId(self):
        return self.testId

class Prepare(TestMessage):
    ''' Means "Get ready for the given test,
    stop processing other messages and answer when you're ready"

    '''
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
    ''' Means "Never mind, this test is cancelled,
    forget about it, resume answering to other messages"

    '''
    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)
        

class TesteeAnswer(TestMessage):
    ''' An answer from the probe being tested'''
    pass

class Ready(TesteeAnswer):
    ''' Means "I'm ready to perform your test,
    I won't answer to other messages and my sockets/whatever are ready"

    '''
    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)


class Result(TesteeAnswer):
    ''' Means "You initiated a test, here are the results".
    Often comes in response to a Over message

    '''
    def __init__(self, targetId, testId, sourceId, report):
        super().__init__(targetId, testId)
        self.report = report
        self.sourceId = sourceId
        
    def getReport(self):
        return self.report

    def getSourceId(self):
        return self.sourceId
