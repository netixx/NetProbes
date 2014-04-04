'''
Convenient Empty test that does nothing
Useful to test the probe test mechanism

@author: francois
'''
__all__ = ['TesterEmpty', 'TesteeEmpty']

from tests import Report
from consts import Identification
from probe.tests import TesteeTest, TesterTest

class TesterEmpty(TesterTest):
    def doResult(self, reports):
        self.result = "Empty test ok (nothing to test)"

class TesteeEmpty(TesteeTest):
    def replyOver(self):
        return Report(Identification.PROBE_ID)
