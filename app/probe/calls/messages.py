"""
Message to exchange information between probes
    Messages sent over the network to other probes

The messages are serialized before being sent and unserialized when received
They are then matched to the corresponding Action by the messagetoaction module
when received at the end host

"""
import random

__all__ = ['Message', 'Add', 'Hello', 'Bye',
           'BroadCast', 'TestMessage', 'Prepare',
           'TesterMessage', 'Over', 'Abort',
           'TesteeAnswer', 'Ready', 'Result']


class Message(object):
    """
    Super class to implement a message between probes
    Message are sent by the client to the targetId

    """

    def __init__(self, targetId):
        self.targetId = targetId
        self.recipientId = targetId
        self.hash = random.randint(0, 2**30)


    def setTarget(self, targetId):
        """Sets the recipient of the message
        :param targetId: the ID of the recipient probe
        """
        self.targetId = targetId

    def getTarget(self):
        """Returns the recipient of the message"""
        return self.targetId


###----- Network discovery messages -----###


class AddToOverlay(Message):
    """Add probe with given IP to overlay"""

    def __init__(self, targetId, probeIp, mergeRemoteOverlay = False):
        super().__init__(targetId)
        self.probeIp = probeIp
        self.mergeOverlays = mergeRemoteOverlay

    def getProbeIp(self):
        """Returns the Id of the probe to add"""
        return self.probeIp


class Add(Message):
    """
    Message to add a new probe (probeId, probeIp) to the overlay
    If the hello flag is an Hello message, then the recipient of
    this message is expected to send the hello message upon
    reception of this message

    """

    def __init__(self, targetId, probeID, probeIP, hello = None):
        super().__init__(targetId)
        self.probeID = probeID
        self.probeIP = probeIP
        self.hello = hello


class Hello(Message):
    """
    Tells a new probe about all other probes
    Sends the list of probes to a new probe

    """

    def __init__(self, targetId, probeList, sourceId, echo = None):
        super().__init__(targetId)
        self.probeList = probeList
        self.remoteIp = None
        self.sourceId = sourceId
        self.echo = echo

    def getProbeList(self):
        """Return the list of probes to add"""
        return self.probeList

    def setRemoteIp(self, ip):
        """Set the IP of the probe that sent this message
        :param ip: the ip of the probe who sent this message"""
        self.remoteIp = ip


class Bye(Message):
    """ Means "I am leaving the system" """

    def __init__(self, targetId, leavingId):
        super().__init__(targetId)
        self.leavingId = leavingId

    def getLeavingID(self):
        """Returns the ID of the probe to remove"""
        return self.leavingId


class BroadCast(Message):
    """
    Encapsulation of a given message as payload
    This allows broadcast of a message through (a subset of) the overlay
    @see: Client class for algorithmic implementation of the Broadcast

    """

    def __init__(self, targetId, sourceId, payload, propagateTo = None):
        super().__init__(targetId)
        self.propagate = propagateTo if propagateTo is not None else []
        self.payload = payload
        self.sourceId = sourceId

    def getNextTargets(self):
        """Returns the remaining targets for this broadcast"""
        return self.propagate

    def getMessage(self):
        """Return the Message encapsulated in broadcast"""
        return self.payload


class Do(Message):
    """Ask probe to do a test"""

    def __init__(self, targetId, testClass, testOptions):
        super().__init__(targetId)
        self.testClass = testClass
        self.testOptions = testOptions
        self.resultCallback = None
        self.errorCallback = None

    def getTestName(self):
        """Return the name of the test to perform"""
        return self.testClass

    def getTestOptions(self):
        """Return the options for this test"""
        return self.testOptions

    def setResultCallback(self, resultCallback):
        """Sets the callable to be called when results are processed
        :param resultCallback: The callable to execute"""
        self.resultCallback = resultCallback

    def setErrorCallback(self, errorCallback):
        """Sets the callable to be called when errors are processed
        :param errorCallback: The callable to execute"""
        self.errorCallback = errorCallback

    def getResultCallback(self):
        """Return the method to use for giving results"""
        return self.resultCallback

    def getErrorCallback(self):
        """Return the method to use for giving errors"""
        return self.errorCallback


###----- Messages to manage tests -----###


class TestMessage(Message):
    """
    Basic superclass for tests
    All tests are identified by a testId which is used for de-multiplexing
    at the other end

    """

    def __init__(self, targetId, testId):
        super().__init__(targetId)
        self.testId = testId

    def getTestId(self):
        """Return the id of the test the messages refer to"""
        return self.testId


class Prepare(TestMessage):
    """ Means "Get ready for the given test"""


    def __init__(self, targetId, testId, testName, testOptions, sourceId):
        super().__init__(targetId, testId)
        self.sourceId = sourceId
        self.testOptions = testOptions
        self.testName = testName

    def getSourceId(self):
        """Return the id of the probe who asks for this test"""
        return self.sourceId

    def getTestOptions(self):
        """Return the options for this test"""
        return self.testOptions

    def getTestName(self):
        """Return the name of the test to prepare for"""
        return self.testName


###----- Messages send by the probe starting the test after its been started-----###


class TesterMessage(TestMessage):
    """A message send by the probe who starts the test"""
    pass


class Over(TesterMessage):
    """ Means "Test is over, give me your report" """

    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)


class Abort(TesterMessage):
    """ Means "Never mind, this test is cancelled
    End the test at once

    """

    def __init__(self, targetId, testId):
        super().__init__(targetId, testId)


class TesteeAnswer(TestMessage):
    """ An answer from the probe being tested"""
    pass


class Ready(TesteeAnswer):
    """ Means "I'm ready to perform your test"""

    def __init__(self, targetId, testId, sourceId):
        super().__init__(targetId, testId)
        self.sourceId = sourceId

    def getSourceId(self):
        """Returns the id of the probe who sends the message"""
        return self.sourceId


class Result(TesteeAnswer):
    """ Means "You initiated a test, here are the results".
    Often comes in response to a Over message

    """

    def __init__(self, targetId, testId, report):
        super().__init__(targetId, testId)
        self.report = report

    def getReport(self):
        """Return the report that the receiving probe generated"""
        return self.report


class WatcherMessage(Message):
    """Message for speaking to watcher instances"""

    def __init__(self, targetId, watcherId):
        super().__init__(targetId)
        self.watcherId = watcherId


class InitializeWatcher(WatcherMessage):
    """Start the init phase of the watcher"""
    def __init__(self, targetId, watcherId, watcherOptions = None):
        super().__init__(targetId, watcherId)
        self.watcherOptions = watcherOptions

    def getWatcherOptions(self):
        return self.watcherOptions


class RunWatcher(WatcherMessage):
    """Start the run phase of the watcher"""
    pass


### For future uses ###

class StatusMessage(Message):
    """Message for telling current status to other probes"""
    pass


class StatusRequest(StatusMessage):
    """Message to ask a probe for it's status"""

    def __init__(self, idProbe):
        StatusMessage.__init__(self, idProbe)
        self.response = None

    def getResponse(self):
        return self.response

    def setResponse(self, response):
        self.response = response


class StatusResponse(StatusMessage):
    """Message to tell a probe about my current stati"""

    def __init__(self, idProbe):
        StatusMessage.__init__(self, idProbe)
        self.stati = []

    def addStatus(self, status):
        self.stati.append(status)

    def getStatus(self):
        return self.stati
