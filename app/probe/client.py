'''
Created on 7 juin 2013

@author: francois
'''
import threading, heapq, http
from probe.consts import *
from consts import Consts
from priorityQueue import PriorityQueue

class Client(threading.Thread):
    
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.messagePile = PriorityQueue()
        self.stop = False
        self.dicoIPID = {}
        self.dicoConnection = {}
    
    
    def addProbe(self, probeIP, probeID):
        self.dicoIPID[probeID] = probeIP
        self.dicoConnection[probeID] = http.client.HTTPConnection( probeIP, Consts.PORT_NUMBER )
        
    
    def quit(self):
        self.stop = True
    
    
    def send(self, message):
        self.messagePile.add(message)
    
    
    def run(self):
        while not self.stop:
            if len(self.messagePile) > 0:
                
                message = self.messagePile.pop()
                                
                if message.__class__.__name__ == "Add" :
                    bodyContent = "ADD " + message.probeID + " " + message.probeIP
                    for conn in self.dicoConnection:
                        conn.request( "POST", "", body=bodyContent )
                
                if message.__class__.__name__ == "Transfer":
                    bodyContent = "TRANSF " + message.content
                    conn = self.dicoConnection.get( message.targetID )
                    conn.request( "POST", "", body=bodyContent )
                
                #if conn.getresponse().status != 200 :
                #    heapq.heappush( self.messagePile, (message.priority, message) )
                    
                    
                    
                    
                    
                    
                    
