'''
Customized exceptions for the probes

@author: francois
'''


class NoSuchProbe(Exception):
    '''
        The probe asked for is unknown
    '''
    pass

class TestInProgress(Exception):
    '''
        You requested to do a test but another test is in progress
    '''
    pass
