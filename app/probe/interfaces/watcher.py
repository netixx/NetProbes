"""A watcher is a daemon running in a separate thread which is
in charge of monitoring aspects of the network

@author: francois
"""
from threading import Thread, Event

class Watcher(Thread):
    """A watcher is a thread"""
    def __init__(self, name, options, logger):
        Thread.__init__(self)
        self.setName(name)
        self.opts = options
        self.logger = logger
        self.initializeEvent = Event()
        self.workEvent = Event()
        self.name = 'watcher'

    def initialize(self):
        """Init phase"""
        pass


    def work(self):
        """Run phase"""
        pass

    def quit(self):
        """End this watcher's activities"""
        pass


class WatcherError(Exception):
    """Error which occurs in the watcher"""
    pass


class WatcherArgumentError(WatcherError):
    """Arguments given to this watcher cannot be understood"""
    pass
