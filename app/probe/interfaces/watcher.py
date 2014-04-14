'''
Created on 9 avr. 2014

@author: francois
'''
from threading import Thread

class Watcher(Thread):

    def __init__(self, name, options):
        Thread.__init__(self)
        self.setName(name)
        self.opts = options




class WatcherServices(object):
    pass
