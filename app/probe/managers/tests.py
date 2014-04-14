'''
Manager that wraps tests with all the preparation necessary

The probe that initiates the test uses the TestManager class
Internally the TestManager creates a _TestManager thread for each tests.
The probe that receives the test uses the TestResponder class
Internally the TestResponder creates a _TestResponder thread for each tests.

'''
__all__ = ['TestManager', 'TestResponder']

import importlib, logging
from interfaces.nettests import LOGGER_NAME
testLogger = logging.getLogger(LOGGER_NAME)

def testFactory(test, mode = ""):
    '''
    A factory to get the class from the name of the test
    test : test to instanciate
    mode : Tester mode or Testee mode
    '''
    mod = importlib.import_module("test." + test)
    return getattr(mod, mode + test.capitalize())

from threading import RLock, Event, Thread
from inout.client import Client
from calls.messages import Prepare, Over, Abort, Ready, Result, TesterMessage, \
    TesteeAnswer
from consts import Identification
from interfaces.excs import TestError, TestAborted
import time
from managers.probes import ProbeStorage

class _TestManager(Thread):
    NAME_TPL = "TestManager_%s-%s"

    def __init__(self, test, formatResult, resultCallback, errorCallback):
        super().__init__()
        self.setName(self.NAME_TPL % (test.getName(), test.getId()))
        '''
        test : an instance of the test to run
        '''
        self.readies = 0
        self.readyLock = RLock()
        self.isReadyForTest = Event()
        self.reportsLock = RLock()
        self.reports = {}
        self.areReportsCollected = Event()
        self.test = test
        self.testError = None
        self.resultCallback = resultCallback
        self.errorCallback = errorCallback
        self.formatResult = formatResult


    def run(self):
        '''
        starts the process of testing
        '''
        testLogger.info("Starting test %s-%s", self.test.getName(), self.test.getId())
        try:
            self.prepare()
            self.performTest()
            self.over()
            self.result()
        except TestError as e:
            self.testError = e
        finally:
            self.finish()


    def prepare(self):
        # TODO: echanger doPrepare et messages ????
        # prepare everyone
        self.test.doPrepare()
        for target in self.test.getTargets():
            ProbeStorage.connectToProbe(target)
            # prepare for the test width given id
            Client.send(Prepare(target, self.test.getId(), self.test.getName(), self.test.getOptions(), Identification.PROBE_ID))

        # wait for everyone to be ready
        self.isReadyForTest.wait(self.test.prepareTimeout)
        if not self.isReadyForTest.is_set():
            # TODO: send abort ?
            self.testError = TestError("Prepare action timed out, probes did not reply in time")
        self.isReadyForTest.clear()
        if self.testError:
            raise self.testError

        testLogger.info("Prepare over, executing test")

    def performTest(self):
        self.test.doTest()
        testLogger.info("Actual test is done")


    def over(self):
        # @todo : cf supra
        self.test.doOver()
        for target in self.test.getTargets():
            # this test is over!
            Client.send(Over(target, self.test.getId()))

        self.areReportsCollected.wait(self.test.resultTimeout)
        # if a timeout occurs
        if not self.areReportsCollected.is_set():
            # TODO: send abort to the probe that did answer ?
            self.testError = TestError("All probes did not give results in time")
        self.areReportsCollected.clear()
        testLogger.info("Over done, processing results")

    def abort(self):
        self.testError = TestAborted("A probe send an abort signal")
        for target in self.test.getTargets():
            # this test is aborted!
            Client.send(Abort(target, self.test.getId()))
        testLogger.ddebug("Abort message broadcast")
        self.test.doOver()
        self.isReadyForTest.set()
        testLogger.info("Test cancelled")

    def result(self):
        for target in self.test.getTargets():
            ProbeStorage.disconnectFromProbe(target)
        self.test.doResult(self.reports)
        testLogger.info("Results processing over, test is done")


    def getCurrentTestId(self):
        return self.test.getId()

    '''Tools methods'''
    def addReady(self, message):
        # TODO: parse message to get finer details
        with self.readyLock:
            testLogger.ddebug("Received new Ready from target probe")
            self.readies += 1
            if (self.readies == self.test.getProbeNumber()):
                testLogger.info("All Readies received, proceeding with test")
                time.sleep(0.2)
                self.isReadyForTest.set()
                self.readies = 0


    def addReport(self, probeId, report):
        with self.reportsLock:
            self.reports[probeId] = report
            testLogger.ddebug("Received new report from target probe")
            if(len(self.reports) == self.test.getProbeNumber()):
                testLogger.info("All reports received, proceeding with result")
                self.areReportsCollected.set()

    def finish(self):
        # TODO: give id instead of name when raw result is asked
        TestManager.cleanTest(self.test.getId())
        if self.testError is not None:
            if self.formatResult:
                self.errorCallback(self.test.getName(), self.testError.getReason())
            else:
                self.errorCallback(self.test.getId(), self.testError)
            testLogger.error("An error occurred during test %s", self.testError.getReason())
        else :
            if self.formatResult:
                self.resultCallback(self.test.getName(), self.test.getResult())
            else:
                self.resultCallback(self.test.getId(), self.test.getRawResult())


from consts import Params as p
from interfaces.excs import ToManyTestsInProgress, TestArgumentError
from interfaces.nettests import TESTER_MODE

class TestManager(object):
    '''
    In charge of running a test
    Started by the probes who receives the Do message/command
    TesteeAnswer are handed down to this object by the Server

    Starts a new _TestManager thread for each new request to
    start a test. It is possible to control the maximum number
    of concurrent tests by setting the Params.MAX_OUTGOING_TESTS
    variable.

    '''
    __testManLock = RLock()
    testManagers = {}

    @classmethod
    def startTest(cls, testName, testOptions, resultCallback, errorCallback, formatResult = True):
        '''
        Method to call in order to start a test.
        It places a new instance of the TestManager into the static field for access purposes
        testName : (class) name of the test to perform
        testOptions : option (in string format) for this test

        '''
        try:
            with cls.__testManLock:
                if len(cls.testManagers) >= p.MAX_OUTGOING_TESTS:
                    raise ToManyTestsInProgress("To much tests are currently running : %s on %s allowed" % (len(cls.testManagers), p.MAX_OUTGOING_TESTS))
                try :
                    test = cls.getTesterTestClass(testName)(testOptions)
                except TestArgumentError as e:
                    errorCallback(testName, e.getUsage())
                    testLogger.warning("Test called with wrong arguments or syntax : %s", testOptions)
                    return
                tm = _TestManager(test, formatResult, resultCallback, errorCallback)
                testLogger.info("Creating test %s with id : %s", test.getName(), test.getId())
                cls.testManagers[test.getId()] = tm
                tm.start()
                return tm.test.getId()
        except ToManyTestsInProgress:
            raise
        except TestError as e:
            testLogger.error("Failed to run test : \n" + e.getReason(), exc_info = 1)
            raise
        except ImportError as e:
            raise TestError("Could not load test class for test : %s", testName)
        except:
            raise TestError("Unexpected error occurred while loading test %s", e)

    @classmethod
    def handleMessage(cls, message):
        try:
            assert isinstance(message, TesteeAnswer)
            testMan = cls.testManagers[message.getTestId()]
            testLogger.debug("Handling test message : %s", message.__class__.__name__)
            if isinstance(message, Result):
                testMan.addReport(message.getSourceId(), message.getReport())
            elif isinstance(message, Ready):
                testMan.addReady(message)
            elif isinstance(message, Abort):
                testMan.abort()
            else:
                pass
        except KeyError:
            testLogger.error("TestManager not found for test %s", message.getTestId())

    @staticmethod
    def getTesterTestClass(testName):
        return testFactory(testName.lower(), TESTER_MODE)

    @classmethod
    def cleanTest(cls, testId):
        try:
            cls.testManagers.pop(testId)
        except KeyError:
            pass

class _TestResponder(Thread):
    NAME_TPL = "TestResponder_%s-%s"
    '''
        Manages one test on the testee's side

    '''

    def __init__(self, test, sourceId):
        super().__init__()
        self.setName(self.NAME_TPL % (test.getName(), test.getId()))
        self.test = test
        self.sourceId = sourceId
        self.testDone = Event()
        self.report = None
        self.testFinished = Event()

    def run(self):
        try :
            self.replyPrepare()
            self.replyTest()
            self.testFinished.wait(self.test.overTimeout)
        finally :
            testLogger.info("Test is over")
            self.finish()

    def replyPrepare(self):
        self.test.replyPrepare()
        Client.send(Ready(self.sourceId, self.test.getId()))

    def replyTest(self):
        self.test.replyTest()
        self.testDone.set()

    def replyOver(self):
        # TODO: change timeout
        self.testDone.wait(self.test.overTimeout)
        self.report = self.test.replyOver()
        self.testFinished.set()

#     def replyAbort(self):
#         self.testDone.set()

    def finish(self):
        if self.report is not None:
            Client.send(Result(self.sourceId, self.test.getId(), Identification.PROBE_ID, self.report))
        TestResponder.cleanTest(self.test.getId())


from interfaces.nettests import TESTEE_MODE

class TestResponder(object):
    '''
    Manager for the test on the testee side.
    Starts a _TestResponder thread for each request to
    answer a test
    TesterMessages are automatically handed over to him
    by the server (no processing is done)

    '''
    testResponders = {}

    @classmethod
    def startTest(cls, testId, testName, sourceId, options):
        testLogger.debug("TestResponder : received request to do test")
        # only if we are not already responding to too many tests!
#         if len(cls.currentTests) > p.MAX_INCOMMING_TESTS:
#             raise ToManyTestsInProgress("Already responding to the maximum allowed number of tests : %s" % p.MAX_INCOMMING_TESTS)
        try :
            tr = _TestResponder(cls.getTesteeTestClass(testName)(options, testId), sourceId)
            cls.testResponders[testId] = tr
            testLogger.info("TestResponder : responding new test %s with id : %s from source : %s", testName, testId, sourceId)
            tr.start()
        except ImportError:
            raise TestError("Error while loading responder test %s" % testName)


    @staticmethod
    def getTesteeTestClass(testName):
        return testFactory(testName.lower(), TESTEE_MODE)

    @classmethod
    def handleMessage(cls, message):
        testLogger.debug("Handling request for test : " + message.__class__.__name__)
        assert isinstance(message, TesterMessage)
        tr = cls.testResponders[message.getTestId()]
        testLogger.ddebug("Got message for manager %s", tr.getName())
        if(isinstance(message, Over)):
            testLogger.debug("Over message received for manager %s", tr.getName())
            tr.replyOver()
        # TODO: support abort
#         elif(isinstance(message, Abort)):
#             testLogger.debug("TestResponder : Abort message received")
#             tr.finish()
#         else:
#             pass
        # TODO: implementer

    @classmethod
    def cleanTest(cls, testId):
        try :
            cls.testResponders.pop(testId)
        except KeyError as e:
            testLogger.warning('Failed to remove test responder from list : %s', e)
