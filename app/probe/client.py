'''
Created on 7 juin 2013

@author: francois
'''
import threading, http.client
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
    
    ''' Opens a connection to the given probe '''
    def connection(self, probeID):
        return http.client.HTTPConnection( self.dicoIPID[probeID], Consts.PORT_NUMBER )
    
    
    def sendMessage(self, message):
        if message.__class__.__name__ is "Add" :
            print("test")
            bodyContent = "ADD " + message.probeID + " " + message.probeIP
            for probeID in self.dicoIPID:
                conn = self.connection(probeID)
                print("POST -> " + bodyContent )
                conn.request( "POST", "", body=bodyContent )
                
        if message.__class__.__name__ is "Transfer":
            bodyContent = "TRANSF " + message.content
            conn = self.connection( message.targetID )
            conn.request( "POST", "", body=bodyContent )
        
    
    
    def run(self):
        while not self.stop:
            
            if not self.messagePile.isEmpty():
                message = self.messagePile.pop()
                
                try:
                    self.sendMessage(message)
                except:
                    print("Error occured sending a message")
                
                #if conn.getresponse().status != 200 :
                #    self.messagePile.add( message )
                    
