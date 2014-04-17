'''
Created on 9 avr. 2014

@author: francois
'''
from threading import Thread


class Watcher(Thread):

    def __init__(self, name, options, logger):
        Thread.__init__(self)
        self.setName(name)
        self.opts = options
        self.logger = logger

    def quit(self):
        pass

class WatcherError(Exception):
    pass


class WatcherArgumentError(WatcherError):
    pass
