'''
Created on 9 avr. 2014

@author: francois
'''
import importlib
WATCHER_PACKAGE = 'watcher'

def _watcherFactory(watcher):
    mod = importlib.import_module(WATCHER_PACKAGE + "." + watcher)
    return getattr(mod, watcher.capitalize())

class WatcherManager(object):
    watchers = []

    @classmethod
    def registerWatcher(cls, watcher, options):
        w = _watcherFactory(watcher.lower())(options)
        cls.watchers.append(w)

    @classmethod
    def startWatchers(cls):
        for w in cls.watchers:
            w.start()




