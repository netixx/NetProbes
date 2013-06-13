'''
Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
from queue import PriorityQueue
from actions import Action


class ActionMan(Thread):
    
    #the list of actions to be done
    actionQueue = PriorityQueue()
    
    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    
    @classmethod
    def addTask(cls, action):
        assert isinstance(action, Action)
        cls.actionQueue.put((action.priority, action))
    
    @classmethod
    def getTask(cls):
        result = cls.actionQueue.get(True)[1]
        cls.actionQueue.task_done()
        return result
    
    def quit(self):
        self.stop = True
    
    def run(self):
        while not self.stop:
            self.manageAction( ActionMan.getTask() )
        
    
    ''' Main function : Here is the code to handle the actions '''
    def manageAction(self, action):
        pass

        
        
            
            
    
    
    