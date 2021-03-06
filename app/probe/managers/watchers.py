"""Module regrouping everything needed in a watcher
WatcherManager manages the currently running watcher by loading/unloading them
WatcherServices provides a API to watchers

@author: francois
"""
import importlib
import logging
import os

from interfaces.watcher import WatcherError, WatcherArgumentError

WATCHER_PACKAGE = 'watchers'
WATCHER_PREFIX = 'Watcher'
WATCHER_LOGGER = 'watchers'

logger = logging.getLogger(WATCHER_LOGGER)

from managers.probetests import TestManager as ProbeTestManager
from managers.standalonetests import TestManager as StandaloneTestManager
from managers.probes import ProbeStorage
from calls.messages import RunWatcher, InitializeWatcher

def _watcherFactory(watcher):
    mod = importlib.import_module(WATCHER_PACKAGE + "." + watcher)
    return getattr(mod, WATCHER_PREFIX + watcher.capitalize())


class WatcherManager(object):
    """Manager for Watchers
    registers, starts and stop watchers"""
    watchers = []

    @classmethod
    def setOutputDir(cls, outputDir):
        cls.out_dir = outputDir

    @classmethod
    def registerWatcher(cls, watcher, options, logger):
        """Add a watcher to the list of known watchers
        :param watcher : name of the watcher to add
        :param options : option array for this watcher
        :param logger : logger object for this watcher
        """
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

    @classmethod
    def handleMessage(cls, message):
        watcherId = message.watcherId
        for wa in cls.watchers:
            if wa.name == watcherId:
                if isinstance(message, RunWatcher):
                    wa.workEvent.set()
                elif isinstance(message, InitializeWatcher):
                    if message.getWatcherOptions() is not None:
                        wa.opts = message.getWatcherOptions()
                    wa.initializeEvent.set()
                break

class WatcherServices(object):

    @classmethod
    def writeOutput(cls, file, output, mode = 'a'):
        with open(os.path.join(WatcherManager.out_dir, file), mode) as f:
            f.write(output)

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

