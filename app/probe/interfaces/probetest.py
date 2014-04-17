"""
Probe tests are tests that require synchronisation between participating
probes (like opening a TCP connection).
The Test and Report class are root classes for all tests.
Writing a test is simple : two class are required :
- one for the client/initiator side
- the other for the servers/receiver side

The classes MUST be prefixed with Tester for the initiator side
and Testee for the receiver side otherwise they will not be able to be
loaded

"""
__all__ = ['Report', 'TesterTest', 'TesteeTest', 'TestServices',
           'TESTEE_MODE', 'TESTER_MODE']

import random
import logging

TEST_LOGGER = "tests"
testLogger = logging.getLogger(TEST_LOGGER)

TESTEE_MODE = "Testee"
TESTER_MODE = "Tester"
"""Timeouts, in seconds"""
DEFAULT_PREPARE_TIMEOUT = 100
DEFAULT_DO_TIMEOUT = 100
DEFAULT_RESULT_TIMEOUT = 100
DEFAULT_OVER_TIMEOUT = 100


class Report(object):
    """
    A report from a probe regarding a Test. Send after over
    signal is received. Often encapsulated in a Result message

    """

    def __init__(self, probeId, isSuccess = True):
        self.isSuccess = isSuccess
        self.testId = None
        self.probeId = probeId

    def getProbeId(self):
        """Returns the probe who generated this report"""
        return self.probeId


class _Test(object):
    """
    Super class for all the tests we can submit our network to

    """
    logger = testLogger

    def __init__(self, testId, options):
        self.result = None
        self.errors = None
        self.ID = testId
        self.opts = options

    def getId(self):
        """Return the computed (Tester) or given (Testee) test id"""
        return self.ID

    def getName(self):
        """Return the name of the test"""
        return self.name

    def getOptions(self):
        """Return the (raw) options for this test"""
        return self.opts

    def getResult(self):
        """returns the result of the test"""
        return self.result


class TesterTest(_Test):
    """Methods for the probe which starts the test"""
    prepareTimeout = DEFAULT_PREPARE_TIMEOUT
    doTimeout = DEFAULT_DO_TIMEOUT
    resultTimeout = DEFAULT_RESULT_TIMEOUT

    def __init__(self, options):
        _Test.__init__(self, '%020x' % random.randrange(256 ** 15), options)
        self.targets = []
        self.rawResult = None

    def getProbeNumber(self):
        """Return the number of targets for this test
        Also corresponds to the number of Ready messages to wait for
        for this test"""
        return len(self.targets)

    def getTargets(self):
        """Returns an array of target IDs for this test"""
        return self.targets

    def doPrepare(self):
        """Prepare for the test"""
        pass

    def doTest(self):
        """Does the actual test"""
        pass

    def doOver(self):
        """Wrap up the test"""
        pass

    def doAbort(self):
        """Abort the test, should be similar to doOver()"""
        pass

    def doResult(self, reports):
        """Generate the result of the test given the set of reports from the tested probes
        Should populate self.result and self.rawResult
        :param reports: list of reports from the target probes
        """
        pass

    def getRawResult(self):
        """Return result in bare form (not string) if necessary"""
        return self.rawResult


class TesteeTest(_Test):
    """Methods for the probe(s) which receive the test"""

    overTimeout = DEFAULT_OVER_TIMEOUT

    def __init__(self, options, testId):
        _Test.__init__(self, testId, options)

    def replyPrepare(self):
        """Actions that the probe must perform in order to be ready for the test"""
        pass

    def replyTest(self):
        """Actions that must be taken when the probe receives the test"""
        pass

    def replyOver(self):
        """Actions that the probe must perform when the test is over
        generates the report and returns it!!!"""
        return Report('00')
