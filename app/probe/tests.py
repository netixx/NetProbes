'''
The Test and Report class are root classes for all tests

'''

import random
import importlib
import logging
from managers.probes import ProbeStorage

LOGGER_NAME = "tests"
testLogger = logging.getLogger(LOGGER_NAME)


'''
A factory to get the class from the name of the test

'''
def testFactory(test):
    mod = importlib.import_module("test." + test)
    return getattr(mod, test.capitalize())

class Report(object):
    '''
    A report from a probe regarding a Test
    Send after over signal is received. Often encapsulated in a Result message

    '''
    def __init__(self, probeId, isSuccess=True):
        self.isSuccess = isSuccess
        self.probeId = probeId

    def getProbeId(self):
        return self.probeId

class Test(object):
    '''
    Super class for all the tests we can submit our network to

    '''
    logger = testLogger
    options = None
    def __init__(self, options):
        self.targets = []
        self.result = None
        self.errors = None
        self.ID = (self.__class__.__name__, '%030x' % random.randrange(256 ** 15))
        self.parseOptions(options)


    def getId(self):
        return self.ID

    def getProbeNumber(self):
        return len(self.targets)

    def getTargets(self):
        return self.targets

    ''' Methods for the probe which starts the test'''

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
    

    def getResult(self):
        '''
        returns the result of the test
        '''
        return self.result

    ''' Methods for the probe(s) which receive the test'''


    @classmethod
    def replyPrepare(cls):
        '''
        Actions that the probe must perform in order to be ready
        '''
        pass


    @classmethod
    def replyTest(cls):
        '''
        Actions that must be taken when the probe recieved the test
        '''
        pass

   
    @classmethod
    def replyOver(cls):
        '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
        '''
        return Report()

    def getOptions(self):
        return self.options

class TestServices(object):
    
    @staticmethod
    def getProbeIpById(probeId):
        return ProbeStorage.getProbeById(probeId).getIp()

    @staticmethod
    def getIdAllOtherProbes():
        return ProbeStorage.getIdAllOtherProbes()
