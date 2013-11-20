'''
Created on 13 juin 2013

@author: francois
'''
from tests import Test, Report
from consts import Identification

class Empty(Test):

    def __init__(self, opts):
        super().__init__(opts)
    
    def parseOptions(self, options):
        self.options = options
        self.targets = options

    '''
        Generate the result of the test given the set of reports from the tested probes
        Should populate self.result
    '''
    def doResult(self, reports):
        self.result = "Empty test ok (nothing to test)"
    
    @staticmethod
    def replyOver():
        return Report(Identification.PROBE_ID)
