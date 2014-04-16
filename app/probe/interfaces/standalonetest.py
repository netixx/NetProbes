'''
Test that do no involve synchronisation between probes
No message is sent to anyone (except the one who asks for the test)

'''
__all__ = ['Report', 'Test']

import random, logging, shlex
from subprocess import Popen, PIPE
from managers.probes import ProbeStorage

TEST_LOGGER = "tests"
testLogger = logging.getLogger(TEST_LOGGER)

class Report(object):
    '''
    A report from a probe regarding a Test
    Send after over signal is received. Often encapsulated in a Result message

    '''
    def __init__(self, probeId, isSuccess = True):
        self.isSuccess = isSuccess
        self.testId = None
        self.probeId = probeId

    def getProbeId(self):
        return self.probeId

class Test(object):
    '''
    Super class for all the tests we can submit our network to

    '''
    logger = testLogger

    def __init__(self, options):
        self.result = None
        self.rawResult = None
        self.errors = None
        self.ID = '%020x' % random.randrange(256 ** 15)
        self.opts = options
        self.name = self.__class__.__name__

    def getId(self):
        return self.ID

    def getName(self):
        return self.name

    def getOptions(self):
        return self.opts

    def getResult(self):
        '''
        returns the result of the test
        '''
        return self.result

    def getRawResult(self):
        return self.rawResult

    def doPrepare(self):
        '''
        Prepare yourself for the test
        '''
        pass

    def doTest(self):
        '''
        Does the actual test
        '''
        pass

    def doOver(self):
        '''
        Prepare yourself for finish
        '''
        pass

    def doAbort(self):
        '''
        Abort the test
        '''
        pass

    def doResult(self):
        '''
        Generate the result of the test given the set of reports from the tested probes
        Should populate self.result and self.rawResult
        '''
        pass