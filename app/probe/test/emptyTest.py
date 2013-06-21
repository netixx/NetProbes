'''
Created on 13 juin 2013

@author: francois
'''
from tests import Test, Report

class EmptyTest(Test):

    def __init__(self, options):
        super().__init__(self, options)
    
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
        return Report()
