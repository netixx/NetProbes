'''
Customized exceptions for the probes

@author: francois
'''
__all__ = ['NoSuchProbe', 'ProbeConnection', 'TestInProgress', 'TestArgumentError', 'TestError', 'TestAborted']


class NoSuchProbe(Exception):
    '''
        The probe asked for is unknown to this probe
    '''
    pass

class ProbeConnection(Exception):
    pass

class TestInProgress(Exception):
    '''
        You requested to do a test but another test is in progress
    '''
    pass


class TestArgumentError(Exception):
    '''
    Error while starting the test
    '''
    def __init__(self, usage):
        self.usage = usage
        
    def getUsage(self):
        return "Wrong argument : " + self.usage

class TestError(Exception):

    def __init__(self, reason):
        self.reason = reason

    def getReason(self):
        return self.reason



class TestAborted(TestError):
    pass
    
    
