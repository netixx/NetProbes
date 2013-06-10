'''
Created on 7 juin 2013

@author: francois
'''
import threading, http.client, urllib, pickle, queue
from consts import Consts



class Client(threading.Thread):
    
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.messagePile = queue.LifoQueue()
        self.stop = False
        self.dicoIPID = {}
        self.dicoConnection = {}
    
    
    def addProbe(self, probeIP, probeID):
        self.dicoIPID[probeID] = probeIP
        self.dicoConnection[probeID] = http.client.HTTPConnection( probeIP, Consts.PORT_NUMBER )
        self.dicoConnection[probeID].connect()
        
    
    def delProbe(self, probeID):
        self.dicoIPID.pop(probeID)
        self.dicoConnection[probeID].close()
        self.dicoConnection.pop(probeID)
    
    def quit(self):
        for probeId in self.dicoConnection.keys():
            self.delProbe(probeId)
        self.stop = True
    
    
    def send(self, message):
        self.messagePile.put(message)
    
    
    def sendMessage(self, message):
        params = urllib.parse.urlencode({'@message': pickle.dumps( message, -1) } )
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        
        conn = self.dicoConnection[message.targetId]
        conn.request("POST", "", params, headers)

#         response = conn.getresponse()
#         
#         if response.status != 200 :
#             self.send(message)

    
    def run(self):
        while not self.stop:
            
            if not self.messagePile.empty():
                message = self.messagePile.get()
                
                #try:
                self.sendMessage(message)
                #except:
                #    print("Error occured sending a message")
                
                #if conn.getresponse().status != 200 :
                #    self.messagePile.add( message )
                    