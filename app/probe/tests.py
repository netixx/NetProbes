import random
import importlib

def testFactory(test):
    mod = importlib.import_module("tests." + test)
    return getattr(mod, test.capitalize())

'''
    A report from a probe regarding a Test
    Send after over signal is received
'''
class Report(object):
    pass


'''
    Super class for all the tests we can submit our network to
'''
class Test(object):

    def __init__(self, options):
        self.targets = []
        self.result = None
        self.ID = (self.__class__.__name__, "'%030x' % random.randrange(256**15)")
        self.parseOptions(options)
        
    def getId(self):
        return self.ID

    def getProbeNumber(self):
        return len(self.targets)

    def getTargets(self):
        return self.targets

    ''' Methods for the probe which starts the test'''
    '''
        Parse the options for the current test
        should populate at least the targets list
    '''
    def parseOption(self, options):
        self.options = options

    '''
        Prepare yourself for the test
    '''
    def doPrepare(self):
        pass
    
    '''
        Does the actual test
    '''
    def doTest(self):
        pass

    '''
        Prepare yourself for finish
    '''
    def doOver(self):
        pass

    '''
        Generate the result of the test given the set of reports from the tested probes
        Should populate self.result
    '''
    def doResult(self, reports):
        pass
    
    '''
        returns the result of the test
    '''
    def getResult(self):
        return self.result

    ''' Methods for the probe(s) which receive the test'''

    '''
        Actions that the probe must perform in order to be ready
    '''
    @staticmethod
    def replyPrepare():
        pass

    '''
        Actions that must be taken when the probe recieved the test
    '''
    @staticmethod
    def replyTest():
        pass

    '''
        Actions that the probe must perform when the test is over
        generates the report and returns it!!!
    '''
    @staticmethod
    def replyOver():
        return Report()

    ''' report for this test (override)'''
    class TestReport(Report):
        pass


from threading import RLock,Event
from client import Client
from messages import *
import consts
'''
    In charge of running a test
'''
class TestManager(object):
    
    testManager = None
    '''
        test :the test to run
    '''
    def __init__(self, test):
        assert(isinstance(test, Test))
        self.test = test
        self.readies = 0
        self.readyLock = RLock()
        self.isReadyForTest = Event()

        self.reportsLock = RLock()
        self.reports = {}
        self.areReportsCollected = Event()

    def prepare(self):
        # @todo : echanger doPrepare et messages ????
        #prepare everyone
        self.test.doPrepare()
        for target in self.test.getTargets():
            # prepare for the test width given id
            Client.send(Prepare(target, self.test.getId()))

        #wait for everyone to be ready
        self.isReadyForTest.wait()
        self.isReadyForTest.clear()
      
    def test(self):
        self.test.doTest()

    def over(self):
        # @todo : cf supra
        self.test.doOver()
        for target in self.test.getTargets():
            # this test is over!
            Client.send(Over(target, self.test.getId()))

        self.areReportsCollected.wait()
        self.areReportsCollected.clear()

    def result(self):
        self.test.doResult(self.reports)

    '''
        starts the process of testing
    '''
    def start(self):
        self.prepare()
        self.test()
        self.over()
        self.result()

    def getCurrentTestId(self):
        return self.test.getId()

    '''Tools methods'''
    def addReady(self):
        with self.readyLock:
            self.readies += 1
            if (self.readies == self.test.getProbeNumber()):
                self.isReadyForTest.set()
                self.readies = 0

    def addReport(self, probeId, report):
        with self.reportsLock:
            self.reports[probeId] = report
            if(len(self.reports) == self.test.getProbeNumber()):
                self.areReportsCollected.set()


    @classmethod
    def handleMessage(cls, message):
        consts.debug("TestManager : Handling test message : " + message.__class__.__name__)
        if(isinstance(message, Result)):
            cls.testManager.addReport(message.getSourceId(), message.getReport())
        elif (isinstance(message, Ready)):
            cls.testManager.addReady()
        else :
            pass
        # todo : implementer

    @classmethod
    def initTest(cls, test):
        cls.testManager = TestManager(test)
        cls.testManager.start()


from exceptions import TestInProgress
#Thread ??
class TestResponder(object):
    testId = None
    sourceId = None
    testDone = Event()
    @classmethod
    def getTest(cls):
        return testFactory(cls.testId[0])

    @classmethod
    def getCurrentTestId(cls):
        return cls.testId

    @classmethod
    def handleMessage(cls, message):
        consts.debug("TestManager : Handling test message : " + message.__class__.__name__)
        if (message.getTestId() != cls.testId):
            raise TestInProgress()

        if(isinstance(message, Over)):
            report = cls.getTest().replyOver()
            Client.send(Result(cls.sourceId, cls.testId, report))
            cls.endTest()
        elif(isinstance(message, Abort)):
            cls.endTest()
        else:
            pass
        # todo : implementer

    @classmethod
    def endTest(cls):
        cls.testId = None
        cls.testDone.set()


    @classmethod
    def initTest(cls, testId, sourceId):
        # only if we are not already responding to a test!
        if (cls.testId == None):
            cls.testId = testId
            cls.sourceId = sourceId
            cls.testDone.clear()
        else:
            raise TestInProgress()
