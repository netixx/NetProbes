'''
Created on 9 avr. 2014

@author: francois
'''
from threading import Thread
from managers.probes import ProbeStorage
from managers.tests import TestManager

class Watcher(Thread):

    def __init__(self, name, options, logger):
        Thread.__init__(self)
        self.setName(name)
        self.opts = options
        self.logger = logger

    def quit(self):
        pass

class WatcherServices(object):
    @classmethod
    def getAllProbes(cls):
        return ProbeStorage.getAllProbes()

    @classmethod
    def getIdAllProbes(cls):
        return ProbeStorage.getIdAllProbes()

    @classmethod
    def doTest(cls, testName, testOptions, resultCallback, errorCallback, formatResult = False):
        return TestManager.startTest(testName, testOptions, resultCallback, errorCallback, formatResult = formatResult)

class WatcherError(Exception):
    pass


class WatcherArgumentError(WatcherError):
    pass
