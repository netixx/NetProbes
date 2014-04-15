'''
Message to exchange information between probes
    Messages sent over the network to other probes

The messages are serialized before being sent and unserialized when received
They are then matched to the corresponding Action by the messagetoaction class
when received at the end host

'''
__all__ = ['Message', 'Add', 'Hello', 'Bye',
           'BroadCast', 'TestMessage', 'Prepare',
           'TesterMessage', 'Over', 'Abort',
           'TesteeAnswer', 'Ready', 'Result']

class Message(object):
    '''
    Super class to implement a message between probes
    Message are sent by the client to the targetId

    '''
    def __init__(self, targetId):
        self.targetId = targetId;
    
    def setTarget(self, targetId):
        self.targetId = targetId

    def getTarget(self):
        return self.targetId


'''----- Network discovery messages -----'''
class AddToOverlay(Message):
    '''Add probe with given IP to overlay'''

    def __init__(self, targetId, probeIp):
        super().__init__(targetId)
        self.probeIp = probeIp

    def getProbeIp(self):
        return self.probeIp


class Add(Message):
    '''
    Message to add a new probe (probeId, probeIp) to the overlay
    If the hello flag is set to true, then the recipient of
    this message is expected to send a hello message to the probe (probeId, probeIp)

    '''
    def __init__(self, targetId, probeID, probeIP, doHello = False):
        super().__init__(targetId)
        self.probeID = probeID
        self.probeIP = probeIP
        self.doHello = doHello


class Hello(Message):
    '''
    Tells a new probe about all other probes
    Sends the list of probes to a new probe

    '''
    def __init__(self, targetId, probeList, sourceId):
        super().__init__(targetId)
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
        super().__init__(targetId)
        self.leavingId = leavingId
        
    def getLeavingID(self):
        return self.leavingId


class BroadCast(Message):
    '''
    Encapsulation of a given message as payload
    This allows broadcast of a message through (a subset of) the overlay
    @see: Client class for algorithmic implementation of the Broadcast

    '''

    def __init__(self, targetId, payload, propagateTo = []):
        super().__init__(targetId)
        self.propagate = propagateTo
        self.payload = payload

    def getNextTargets(self):
        return self.propagate

    def getMessage(self):
        return self.payload

class Do(Message):
    '''Ask probe to do a test'''

    def __init__(self, targetId, testClass, testOptions):
        super().__init__(targetId)
        self.testClass = testClass
        self.testOptions = testOptions
        self.resultCallback = None
        self.errorCallback = None

    def getTestName(self):
        return self.testClass

    def getTestOptions(self):
        return self.testOptions

    def setResultCallback(self, resultCallback):
        self.resultCallback = resultCallback

    def setErrorCallback(self, errorCallback):
        self.errorCallback = errorCallback

    def getResultCallback(self):
        return self.resultCallback

    def getErrorCallback(self):
        return self.errorCallback


'''----- Messages to manage tests -----'''

class TestMessage(Message):
    """
    Basic superclass for tests
    All tests are identified by a testId which is used for demultiplexing
    at the other end

    """

    def __init__(self, targetId, testId):
        super().__init__(targetId)
        self.testId = testId

    def getTestId(self):
        return self.testId

class Prepare(TestMessage):
    ''' Means "Get ready for the given test"'''


    def __init__(self, targetId, testId, testName, testOptions, sourceId):
        super().__init__(targetId, testId)
        self.sourceId = sourceId
        self.testOptions = testOptions
        self.testName = testName

    def getSourceId(self):
        return self.sourceId

    def getTestOptions(self):
        return self.testOptions

    def getTestName(self):
        return self.testName


'''----- Messages send by the probe starting the test after its been started-----'''

class TesterMessage(TestMessage):
#     def __init__(self, targetId, testId):
#         super().__init__(targetId, testId)
    pass

class Over(TesterMessage):
    ''' Means "Test is over, give me your report" '''

    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)

class Abort(TesterMessage):
    ''' Means "Never mind, this test is cancelled
    End the test at once

    '''

    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)
        

class TesteeAnswer(TestMessage):
    ''' An answer from the probe being tested'''
#     def __init__(self, targetId, testId):
#         super().__init__(targetId, testId)
    pass

class Ready(TesteeAnswer):
    ''' Means "I'm ready to perform your test"'''

    def __init__(self, targetId, testId, sourceId):
        super().__init__(targetId, testId)
        self.sourceId = sourceId

    def getSourceId(self):
        return self.sourceId


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


''' For future uses'''
class StatusMessage(Message):
    pass


class StatusRequest(StatusMessage):

    def __init__(self, idProbe):
        StatusMessage.__init__(self, idProbe)
        self.response = None

    def getResponse(self):
        return self.response

    def setResponse(self, response):
        self.response = response


class StatusResponse(StatusMessage):
    def __init__(self, idProbe):
        StatusMessage.__init__(self, idProbe)
        self.stati = []

    def addStatus(self, status):
        self.stati.append(status)

    def getStatus(self):
        return self.stati
