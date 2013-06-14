'''
Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
import actions as a
from probe.probes import *
from client import Client
from consts import Identification
from messages import Hello
from test import Test


manager = {"Add" : "manageAdd",
            "Transfer" : "manageTransfer",
            "Do" : "manageDo"}

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
        ProbeStorage.add( Probe(action.getIdSonde(), action.getIpSonde() ) );
        Client.send( Hello(action.getIdSonde(), Identification.PROBE_ID, ProbeStorage.numberOfConnections ) );
        
    
    
    @staticmethod
    def manageRemove(action):
        assert isinstance(action, a.Do)
    
    
    @staticmethod
    def manageBye(action):
        assert isinstance(action, a.Add)
        pass
    
    @staticmethod
    def manageTransfer(action):
        assert isinstance(action, a.Transfer)
        Client.send( action.message )
    
    
    @staticmethod
    def manageDo(action):
        assert isinstance(action, a.Do)
        pass
        
    @staticmethod
    def manageQuit(action):
        assert isinstance(action, a.Do) 
        

        
        
        
            
            
    
    
    