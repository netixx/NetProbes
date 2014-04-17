'''
Created on 9 avr. 2014

@author: francois
'''
import importlib
import logging

from interfaces.watcher import WatcherError, WatcherArgumentError

WATCHER_PACKAGE = 'watchers'
WATCHER_PREFIX = 'Watcher'
WATCHER_LOGGER = 'watchers'
logger = logging.getLogger(WATCHER_LOGGER)

from managers.probetests import TestManager as ProbeTestManager
from managers.standalonetests import TestManager as StandaloneTestManager
from managers.probes import ProbeStorage


def _watcherFactory(watcher):
    mod = importlib.import_module(WATCHER_PACKAGE + "." + watcher)
    return getattr(mod, WATCHER_PREFIX + watcher.capitalize())


class WatcherManager(object):
    watchers = []

    @classmethod
    def registerWatcher(cls, watcher, options, logger):
        try:
            w = _watcherFactory(watcher.lower())(options, logger)
            cls.watchers.append(w)
        except ImportError:
            raise WatcherError("Unable to import watcher '%s'" % watcher)
        except WatcherArgumentError as e:
            raise WatcherError("Wrong arguments for watcher %s %s : usage %s" % (watcher, options, e))

    @classmethod
    def startWatchers(cls):
        logger.info("Starting watchers")
        for w in cls.watchers:
            logger.info("Starting watcher %s", w.__class__.__name__)
            w.start()

    @classmethod
    def stopWatchers(cls):
        logger.info("Stopping watchers")
        for w in cls.watchers:
            logger.info("Stopping watcher %s", w.__class__.__name__)
            w.quit()


class WatcherServices(object):
    @classmethod
    def getAllOtherProbes(cls):
        return ProbeStorage.getAllOtherProbes()

    @classmethod
    def getIdAllOtherProbes(cls):
        return ProbeStorage.getIdAllOtherProbes()

    @classmethod
    def getIpAllOtherProbes(cls):
        return ProbeStorage.getIpAllOtherProbes()

    @classmethod
    def getAllProbes(cls):
        return ProbeStorage.getAllProbes()

    @classmethod
    def getIdAllProbes(cls):
        return ProbeStorage.getIdAllProbes()

    @classmethod
    def doTest(cls, testName, testOptions, resultCallback, errorCallback, formatResult = False):
        return ProbeTestManager.startTest(testName, testOptions, resultCallback, errorCallback,
                                          formatResult = formatResult)

    @classmethod
    def doStandaloneTest(cls, testName, testOptions, resultCallback, errorCallback, formatResult = False):
        return StandaloneTestManager.startTest(testName, testOptions, resultCallback, errorCallback,
                                               formatResult = formatResult)

    @classmethod
    def abortProbeTest(cls, testId):
        ProbeTestManager.stopTest(testId)

    @classmethod
    def abortStandaloneTest(cls, testId):
        StandaloneTestManager.stopTest(testId)

