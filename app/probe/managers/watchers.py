'''
Created on 9 avr. 2014

@author: francois
'''
import importlib, logging
from interfaces.watcher import WatcherError, WatcherArgumentError
WATCHER_PACKAGE = 'watchers'
WATCHER_PREFIX = 'Watcher'
logger = logging.getLogger()

def _watcherFactory(watcher):
    mod = importlib.import_module(WATCHER_PACKAGE + "." + watcher)
    return getattr(mod, WATCHER_PREFIX + watcher.capitalize())

class WatcherManager(object):
    watchers = []

    @classmethod
    def registerWatcher(cls, watcher, options):
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




