'''
Convenient Empty test that does nothing
Useful to test the probe test mechanism

@author: francois
'''
__all__ = ['TesterEmpty', 'TesteeEmpty']

from tests import Report
from consts import Identification
from probe.tests import TesteeTest, TesterTest


name = "Empty"

class TesterEmpty(TesterTest):

    def __init__(self, options):
        super().__init__(options)
        self.parseOptions()
        self.name = name

    def parseOptions(self):
        self.targets = self.opts

    def doResult(self, reports):
        self.result = "Empty test ok (nothing to test)"

class TesteeEmpty(TesteeTest):
    
    def __init__(self, options, testId):
        super().__init__(options, testId)
        self.parseOptions()
        self.name = name
        
    def parseOptions(self):
        self.targets = self.opts

    def replyOver(self):
        return Report(Identification.PROBE_ID)
