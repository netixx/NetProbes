'''
Customized exceptions for the probes

@author: francois
'''
__all__ = ['NoSuchProbe', 'ProbeConnection', 'ToManyTestsInProgress',
           'TestInProgress', 'ActionError', 'TestArgumentError',
           'TestError', 'TestAborted']


class NoSuchProbe(Exception):
    '''
        The probe asked for is unknown to this probe
    '''
    pass


class ProbeConnectionException(Exception):
    pass


class ToManyTestsInProgress(Exception):
    '''
        Maximum number of allowed test has been reached
    '''
    pass


class TestInProgress(Exception):
    '''
        You requested to do a test but another test is in progress
    '''
    pass


class ActionError(Exception):
    """Generic error during the processing of an action"""
    def __init__(self, message, action):
        self.action = action
        self.message = message

    def __str__(self):
        return "Error occurred while performing action %s : %s" % (self.action, self.message)


class TestArgumentError(Exception):
    '''
    Error while starting the test
    '''
    def __init__(self, usage):
        self.usage = usage
        
    def getUsage(self):
        return "Wrong argument : " + self.usage


class TestError(ActionError):

    def __init__(self, reason):
        self.action = "Test"
        self.message = reason

    def getReason(self):
        return self.message


class TestAborted(TestError):
    pass
