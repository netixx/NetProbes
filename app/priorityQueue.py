'''
Created on 10 juin 2013

@author: Gaspard FEREY
'''

import heapq

''' A queue that stack objects according to their "priority" field '''
class PriorityQueue(object):
    '''
    classdocs
    '''
    content = []
    
    def __init__(self):
        '''
        Constructor
        '''
    
    def add(self, entry):
        heapq.heappush(self.content, (entry.priority, entry))
        
    def pop(self):
        return heapq.heappop(self.content)[1]
    
    def readFirst(self):
        return self.content[0][1]
    
    def length(self):
        return len(self.content)
    
    def isEmpty(self):
        return len(self.content) == 0