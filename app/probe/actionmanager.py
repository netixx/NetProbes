'''
Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
from queue import PriorityQueue
from actions import Action


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
            self.manageAction( ActionMan.getTask() )
        
    
    ''' Main function : Here is the code to handle the actions '''
    def manageAction(self, action):
        pass

        
        
            
            
    
    
    