"""A watcher is a daemon running in a separate thread which is
in charge of monitoring aspects of the network

@author: francois
"""
from threading import Thread


class Watcher(Thread):
    """A watcher is a thread"""
    def __init__(self, name, options, logger):
        Thread.__init__(self)
        self.setName(name)
        self.opts = options
        self.logger = logger

    def quit(self):
        """End this watcher's activities"""
        pass


class WatcherError(Exception):
    """Error which occurs in the watcher"""
    pass


class WatcherArgumentError(WatcherError):
    """Arguments given to this watcher cannot be understood"""
    pass
