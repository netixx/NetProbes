'''
Created on 13 juin 2013

@author: francois
'''



'''
    Super class for all the tests we can submit our network to
'''
class Test(object):

    def __init__(self, options):
        self.parseOptions(options)
        self.result = None

    '''
        Parse the options for the current test
    '''
    def parseOption(self, options):
        self.options=option

    '''
        Tell the target probes to prepare for the test
    '''
    def doPrepare(self):
        pass
    
    '''
        Does the actual test
    '''
    def doTest(self):
        pass

    '''
        Tells the target probes that test is over
    '''
    def doOver(self):
        pass

    '''
        Generate the result of the test
        Should populate self.result
    '''
    def doResult(self):
        pass
    

    '''
        Start the testing process
    '''
    def start(self):
        self.doPrepare()
        self.doTest()
        self.doOver()
        self.doResult()

    '''
        returns the result of the test
    '''
    def getResult(self):
        return self.result



