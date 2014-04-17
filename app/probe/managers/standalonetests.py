"""Manager for the standalone tests
They don't require synchronisation so the handling is much easier
Architecture is the same : a TestManager starts on _TestManager thread
for each test
"""
__all__ = ['TestManager']

import importlib
import logging
from threading import Thread, RLock

from interfaces.excs import TestError, TestAborted
from interfaces.standalonetest import TEST_LOGGER


testLogger = logging.getLogger(TEST_LOGGER)


def _testFactory(test):
    """
    A factory to get the class from the name of the test
    :param test : test to instantiate
    """
    mod = importlib.import_module("tests.standalone." + test)
    return getattr(mod, test.capitalize())


class _TestManager(Thread):
    """A tread to manage a test"""
    NAME_TPL = "TestManager_%s-%s"

    def __init__(self, test, formatResult, resultCallback, errorCallback):
        super().__init__()
        self.setName(self.NAME_TPL % (test.getName(), test.getId()))
        self.test = test
        self.testError = None
        self.resultCallback = resultCallback
        self.errorCallback = errorCallback
        self.formatResult = formatResult
        self.prepared = False
        self.tested = False
        self.overed = False


    def run(self):
        """Starts the process of testing"""
        testLogger.info("Starting test %s-%s", self.test.getName(), self.test.getId())
        try:
            self.prepare()
            self.prepared = True
            self.performTest()
            self.tested = True
            self.over()
            self.overed = True
            self.result()
        except TestError as e:
            self.testError = e
        finally:
            self.finish()


    def prepare(self):
        """Prepare for the test"""
        self.test.doPrepare()
        testLogger.info("Prepare over, executing test")

    def performTest(self):
        """Do the actual test"""
        self.test.doTest()
        testLogger.info("Actual test is done")


    def over(self):
        """End the test"""
        self.test.doOver()
        testLogger.info("Over done, processing results")

    def abort(self):
        """End the test early"""
        if not self.overed:
            self.test.doOver()
        self.testError = TestAborted("Test aborted early.")
        testLogger.info("Test cancelled")

    def result(self):
        """Compute results for this test"""
        self.test.doResult()
        testLogger.info("Results processing over, test is done")

    def finish(self):
        """Clean everything and write results using callbacks"""
        TestManager.cleanTest(self.test.getId())
        if self.testError is not None:
            if self.formatResult:
                self.errorCallback(self.test.getName(), self.testError.getReason())
            else:
                self.errorCallback(self.test.getId(), self.testError)
            testLogger.error("An error occurred during test %s", self.testError.getReason())
        else:
            if self.formatResult:
                self.resultCallback(self.test.getName(), self.test.getResult())
            else:
                self.resultCallback(self.test.getId(), self.test.getRawResult())


from consts import Params as p
from interfaces.excs import ToManyTestsInProgress, TestArgumentError


class TestManager(object):
    """In charge of running a test
    Started by the probes who receives the request to do a
    Standalone test

    Starts a new _TestManager thread for each new request to
    start a test. It is possible to control the maximum number
    of concurrent tests by setting the Params.MAX_STANDALONE_TEST
    variable.
    """
    __testManLock = RLock()
    testManagers = {}

    @classmethod
    def startTest(cls, testName, testOptions, resultCallback, errorCallback, formatResult = True):
        """Method to call in order to start a test.
        It places a new instance of the TestManager into the static dict for access purposes
        :param testName : (class) name of the test to perform
        :param testOptions : option (in string format) for this test
        :param resultCallback : method to call to give the results
        :param errorCallback : method to call to give the errors
        :param formatResult : should the results of this test be formatted ?

        """
        try:
            with cls.__testManLock:
                if len(cls.testManagers) >= p.MAX_STANDALONETESTS:
                    raise ToManyTestsInProgress("To much tests are currently running : %s on %s allowed" % (
                        len(cls.testManagers), p.MAX_STANDALONETESTS))
                try:
                    test = _testFactory(testName)(testOptions)
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
        except ImportError:
            raise TestError("Could not load test class for test : %s" % testName)
        except Exception as e:
            raise TestError("Unexpected error occurred while loading test %s" % e)

    @classmethod
    def stopTest(cls, testId):
        """Stop a test
        :param testId : id of the test to stop
        """
        try:
            cls.testManagers[testId].abort()
        except KeyError:
            testLogger.info("Test %s already finished" % testId)

    @classmethod
    def stopTests(cls):
        """Stop all test and wait for termination"""
        for tm in cls.testManagers.values():
            tm.abort()
        for tm in list(cls.testManagers.values()):
            tm.join()

    @classmethod
    def cleanTest(cls, testId):
        """Remove test from managers
        :param testId : id of the test to remove"""
        try:
            cls.testManagers.pop(testId)
        except KeyError:
            pass
