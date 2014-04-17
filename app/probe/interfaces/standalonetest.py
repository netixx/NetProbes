"""
Test that do no involve synchronisation between probes
No message is sent to anyone (except the one who asks for the test)

"""
__all__ = ['Report', 'Test']

import random
import logging

TEST_LOGGER = "tests"
testLogger = logging.getLogger(TEST_LOGGER)


class Report(object):
    """A report from a probe regarding a Test
    Send after over signal is received. Often encapsulated in a Result message

    """

    def __init__(self, probeId, isSuccess = True):
        self.isSuccess = isSuccess
        self.testId = None
        self.probeId = probeId

    def getProbeId(self):
        """Returns the ID of the probe which generated the report"""
        return self.probeId


class Test(object):
    """Single class for all the tests we can submit our network to
    Only one class is needed since we don't have a receiver side for this
    kind of test"""
    logger = testLogger

    def __init__(self, options):
        self.result = None
        self.rawResult = None
        self.errors = None
        self.ID = '%020x' % random.randrange(256 ** 15)
        self.opts = options
        self.name = self.__class__.__name__

    def getId(self):
        """Return the computed id of this test"""
        return self.ID

    def getName(self):
        """Return the name of the test"""
        return self.name

    def getOptions(self):
        """Returns the raw options of this test"""
        return self.opts

    def getResult(self):
        """Returns the formatted result of the test"""
        return self.result

    def getRawResult(self):
        """Returns the unformatted result of the test"""
        return self.rawResult

    def doPrepare(self):
        """Prepare for the test"""
        pass

    def doTest(self):
        """Does the actual test"""
        pass

    def doOver(self):
        """End the test"""
        pass

    def doAbort(self):
        """Abort the test"""
        pass

    def doResult(self):
        """Generate the result of the test given the set of reports from the tested probes
        Should populate self.result and self.rawResult

        """
        pass