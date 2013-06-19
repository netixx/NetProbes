'''
Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
import actions as a
from probes import Probe, ProbeStorage
from client import Client
from consts import *
from messages import Hello, Bye
from test import Test
from server import Server



class ActionMan(Thread):

    manager = { "Add" : "manageAdd",
            "Remove" : "manageRemove",
            "Transfer" : "manageTransfer",
            "Do" : "manageDo",
            "Quit" : "manageQuit" }
    
    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    def quit(self):
        debug("Action Manager : Killing ActionMan !")
        self.stop = True
    
    def run(self):
        while not self.stop:
            task = Server.getTask()
            getattr(ActionMan, ActionMan.manager.get(task.__class__.__name__))(task)
            Server.taskDone()
    
    
    @staticmethod
    def manageAdd(action):
        assert isinstance(action, a.Add)
        debug("ActionMan : managing Add task")
        
        ProbeStorage.addProbe(Probe(action.getIdSonde(), action.getIpSonde()));
        
        if action.getHello():
            Client.send( Hello(action.getIdSonde(), Identification.PROBE_ID ) );
        
    
    
    @staticmethod
    def manageRemove(action):
        assert isinstance(action, a.Remove)
        debug("ActionMan : managing Remove task")
        ProbeStorage.delProbe( action.getIdSonde() );
    
    
    @staticmethod
    def manageDo(action):
        assert isinstance(action, a.Do)
        debug("ActionMan : managing Do task")
        
        ''' Manage tests here '''
        
    
    @staticmethod
    def manageQuit(action):
        assert isinstance(action, a.Quit)
        debug("ActionMan : managing Quit task")
        Client.broadcast( Bye("", Identification.PROBE_ID) )
        ''' Other commands to close all connections, etc '''
        Client.allMessagesSent()
        ProbeStorage.closeAllConnections()
        debug("ActionMan : All connections closed")
        Server.allTaskDone()
        ProbeStorage.addProbe(Probe(str(Identification.PROBE_ID), "localhost"))
        debug("ActionMan : readded the localhost probe")
