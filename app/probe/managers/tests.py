'''
Manager that wraps tests with all the preparation necessary

The probe that initiates the test uses a TestManager instance
The probe that receives the test uses the TestResponder class methods

'''

import importlib
import logging
from tests import Test, LOGGER_NAME
from managers.probes import ProbeStorage

testLogger = logging.getLogger(LOGGER_NAME)


'''
A factory to get the class from the name of the test

'''

__all__ = ['TestManager', 'TestResponder']


def testFactory(test):
    mod = importlib.import_module("test." + test)
    return getattr(mod, test.capitalize())

from threading import RLock,Event
from inout.client import Client
from calls.messages import Prepare, Over, Abort, Ready, Result
from consts import Identification
from exceptions import TestError, TestAborted
import time


class _TestManager(object):
    
    def __init__(self, test):
        '''
        test : an instance of the test to run
        '''
        assert(isinstance(test, Test))
        self.readies = 0
        self.readyLock = RLock()
        self.isReadyForTest = Event()

        self.reportsLock = RLock()
        self.reports = {}
        self.areReportsCollected = Event()
        self.test = test
        self.testError = None

    def prepare(self):
        # @todo : echanger doPrepare et messages ????
        #prepare everyone
        self.test.doPrepare()
        for target in self.test.getTargets():
            ProbeStorage.connectToProbe(target)
            # prepare for the test width given id
            Client.send(Prepare(target, self.test.getId(), Identification.PROBE_ID, self.test.getOptions()))

        #wait for everyone to be ready
        self.isReadyForTest.wait()
        self.isReadyForTest.clear()
        if self.testError:
            raise self.testError
        
        testLogger.info("TestManager : Prepare over, executing test")
      
    def performTest(self):
        self.test.doTest()
        testLogger.info("TestManager : actual test is done")


    def over(self):
        # @todo : cf supra
        self.test.doOver()
        for target in self.test.getTargets():
            # this test is over!
            Client.send(Over(target, self.test.getId()))

        self.areReportsCollected.wait()
        self.areReportsCollected.clear()
        testLogger.info("TestManager : over done, processing results")
        
    def abort(self):
        self.testError = TestAborted("A probe send an abort signal")
        for target in self.test.getTargets():
            # this test is aborted!
            Client.send( Abort(target, self.test.getId()) )
        testLogger.debug("TestManager : Abort message broadcast")
        self.test.doOver()
        self.isReadyForTest.set()
        testLogger.info("TestManager : Test cancelled")
    
    def result(self):
        self.test.doResult(self.reports)
        for target in self.test.getTargets():
            ProbeStorage.disconnectFromProbe(target)
        testLogger.info("TestManager : results processing over, test is done")


    def start(self):
        '''
        starts the process of testing
        '''
        testLogger.info("TestManager : Starting test")
        try:
            self.prepare()
            self.performTest()
            self.over()
            self.result()
        except TestError as e:
            testLogger.error("TestManager : An error accured : " + e.getReason(), exc_info = 1)

    def getCurrentTestId(self):
        return self.test.getId()

    '''Tools methods'''
    def addReady(self):
        with self.readyLock:
            testLogger.debug("TestManager : received new Ready from target probe")
            self.readies += 1
            if (self.readies == self.test.getProbeNumber()):
                testLogger.info("TestManager : all Readies received, proceeding with test")
                time.sleep(0.2)
                self.isReadyForTest.set()
                self.readies = 0


    def addReport(self, probeId, report):
        with self.reportsLock:
            self.reports[probeId] = report
            testLogger.debug("TestManager : received new report from target probe")
            if(len(self.reports) == self.test.getProbeNumber()):
                testLogger.info("TestManager : all reports received, proceeding with result")
                self.areReportsCollected.set()


class TestManager(object):
    '''
    In charge of running a test
    Started by the probes who receives the Do message/command
    TesteeAnswer are handed down to this object by the Server
    '''
    testManager = None

    @classmethod
    def initTest(cls, test):
        '''
        Method to call in order to start a test.
        It places a new instance of the TestManager into the static field for access purposes
        test : an instance of the test to perform
        '''
        testLogger.debug("TestManager : Trying to start test : " + test.__class__.__name__)
        try:
            if cls.testManager is not None:
                raise TestInProgress("Test with id : %s is already running" % test.getId())
            cls.testManager = _TestManager(test)
            testLogger.info("TestManager : creating test with id : " + "(" + " ".join(test.getId()) + ")")
            cls.testManager.start()
            testLogger.info("TestManager : Test " + test.__class__.__name__ + " is done.")
        except TestError as e:
            testLogger.error("TestManager : Failed to start test : \n" + e.getReason(), exc_info = 1)
            raise
        finally:
            cls.testManager = None
    
    @classmethod
    def handleMessage(cls, message):
        testLogger.debug("TestManager : Handling test message : " + message.__class__.__name__)
        if isinstance(message, Result):
            cls.testManager.addReport(message.getSourceId(), message.getReport())
        elif isinstance(message, Ready):
            cls.testManager.addReady()
        elif isinstance(message, Abort):
            cls.testManager.abort()
        else:
            pass


from probe.exceptions import TestInProgress

class TestResponder(object):
    '''
    Manager for the test on the testee side.
    All static class that responds to the request of the tester probe.
    TesterMessages are automatically handed over to him by the server (no processing is done)

    '''
    testId = None
    sourceId = None
    testDone = Event()
    @classmethod
    def getTest(cls):
        return testFactory(cls.testId[0].lower() )

    @classmethod
    def getCurrentTestId(cls):
        return cls.testId

    @classmethod
    def handleMessage(cls, message):
        testLogger.debug("TestResponder : Handling request for test : " + message.__class__.__name__)
        if (message.getTestId() != cls.testId):
            raise TestInProgress()

        if(isinstance(message, Over)):
            testLogger.debug("TestResponder : Over message received")
            report = cls.getTest().replyOver()
            Client.send(Result(cls.sourceId, cls.testId, Identification.PROBE_ID, report))
            cls.endTest()
        elif(isinstance(message, Abort)):
            testLogger.debug("TestResponder : Abort message received")
            cls.endTest()
        else:
            pass
        # todo : implementer

    @classmethod
    def endTest(cls):
        cls.testId = None
        cls.testDone.set()
        testLogger.info("TestResponder : Test is over")

    @classmethod
    def replyPrepare(cls):
        cls.getTest().replyPrepare()
        Client.send( Ready(cls.sourceId, cls.getCurrentTestId() ) )
        cls.getTest().replyTest()
        

    @classmethod
    def initTest(cls, testId, sourceId, options):
        testLogger.debug("TestResponder : received request to do test")
        # only if we are not already responding to a test!
        if (cls.testId == None):
            cls.testId = testId
            cls.getTest().options = options
            cls.sourceId = sourceId
            cls.replyPrepare()
            testLogger.info("TestResponder : responding new test with id : " + "(" + " ".join(cls.testId) + ")" + " from source : " + sourceId)
            cls.testDone.clear()
            
        else:
            raise TestInProgress()
