'''
Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
import actions as a
from probe.probes import Probe, ProbeStorage
from client import Client
from consts import Identification
from messages import Hello, Bye
from test import Test


manager = { "Add" : "manageAdd",
            "Remove" : "manageRemove",
            "Transfer" : "manageTransfer",
            "Do" : "manageDo",
            "Quit" : "manageQuit" }

class ActionMan(Thread):
    
    
    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    def quit(self):
        self.stop = True
    
    def run(self):
        while not self.stop:
            task = ActionMan.getTask()
            globals()[manager.get(task.__class__.__name__)](task)
    
    
    @staticmethod
    def manageAdd(action):
        assert isinstance(action, a.Add)
        ProbeStorage.addProbe( Probe(action.getIdSonde(), action.getIpSonde() ) );
        Client.send( Hello(action.getIdSonde(), Identification.PROBE_ID, ProbeStorage.numberOfConnections() ) );
        
    
    
    @staticmethod
    def manageRemove(action):
        assert isinstance(action, a.Do)
        ProbeStorage.delProbe( action.getIdSonde() );
    
    
    @staticmethod
    def manageTransfer(action):
        assert isinstance(action, a.Transfer)
        Client.send( action.message )
    
    
    @staticmethod
    def manageDo(action):
        assert isinstance(action, a.Do)
        ''' Manage tests here '''
        
    @staticmethod
    def manageQuit(action):
        assert isinstance(action, a.Do) 
        Client.broadcast( Bye(Identification.PROBE_ID) )
        ''' Other commands to close all connections, etc '''
        
        
        
            
            
    
    
    