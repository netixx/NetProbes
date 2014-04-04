'''
The Test and Report class are root classes for all tests.
Writing a test is simple : two class are required :
one for the client/initiator side
the other for the servers/receiver side

The classes MUST be prefixed with Tester for the initiator side
and Testee for the receiver side otherwise they will not be able to be
loaded

'''
__all__ = ['Report', 'TesterTest', 'TesteeTest', 'TestServices',
           'TESTEE_MODE', 'TESTER_MODE']

import random, logging
from managers.probes import ProbeStorage

LOGGER_NAME = "tests"
testLogger = logging.getLogger(LOGGER_NAME)
TESTEE_MODE = "Testee"
TESTER_MODE = "Tester"

class Report(object):
    '''
    A report from a probe regarding a Test
    Send after over signal is received. Often encapsulated in a Result message

    '''
    def __init__(self, probeId, isSuccess = True):
        self.isSuccess = isSuccess
        # TODO: complete
        self.testId = None
        self.probeId = probeId

    def getProbeId(self):
        return self.probeId

class _Test(object):
    '''
    Super class for all the tests we can submit our network to

    '''
    logger = testLogger
    options = None

    def __init__(self):
        self.result = None
        self.errors = None
        self.ID = None
        self.name = self.__class__.__name__
        self.options = None


    def getId(self):
        return self.ID

    def getName(self):
        return self.name

    def getOptions(self):
        return self.options

    def getResult(self):
        '''
        returns the result of the test
        '''
        return self.result

class TesterTest(_Test):
    '''
    Methods for the probe which starts the test

    '''

    def __init__(self, options):
        _Test.__init__(self)
        self.ID = '%030x' % random.randrange(256 ** 15)
        self.parseOptions(options)
        self.targets = []
    
    def getProbeNumber(self):
        return len(self.targets)

    def getTargets(self):
        return self.targets

    def parseOptions(self, options):
        '''
        Parse the options for the current test
        should populate at least the targets list
        '''
        self.options = options

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

    def doResult(self, reports):
        '''
        Generate the result of the test given the set of reports from the tested probes
        Should populate self.result
        '''
        pass

class TesteeTest(_Test):
    '''
    Methods for the probe(s) which receive the test

    '''

    def __init__(self, options, testId):
        self.ID = testId
        _Test.__init__(self)
        self.parseOptions(options)

    def replyPrepare(self):
        '''
        Actions that the probe must perform in order to be ready
        '''
        pass

    def replyTest(self):
        '''
        Actions that must be taken when the probe recieved the test
        '''
        pass
   
    def replyOver(self):
        '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
        '''
        return Report()


class TestServices(object):
    '''
    Provides services for tests
    
    '''
    @staticmethod
    def getProbeIpById(probeId):
        '''Returns the Ip of a probe given it's Id'''
        return ProbeStorage.getProbeById(probeId).getIp()

    @staticmethod
    def getIdAllOtherProbes():
        '''Returns the Ids of all the other known probes'''
        return ProbeStorage.getIdAllOtherProbes()
