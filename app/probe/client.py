'''
Created on 7 juin 2013

@author: francois
'''
import http.client, urllib, pickle
from threading import Thread
from consts import Consts
from queue import Queue
from messages import Message
from probes import ProbeStorage

class Client(Thread):
    messagePile = Queue()

    def __init__(self):
        Thread.__init__(self)
        self.stop = False
        self.setName("Client")
    
    def quit(self):
        for probeId in ProbeStorage.dicoConnection.keys():
            ProbeStorage.delProbe(probeId)
        self.stop = True
    
    @staticmethod
    def send(message):
        assert isinstance(message, Message)
        Client.messagePile.put(message)
    
    def run(self):
        while not self.stop:
            
            if not Client.messagePile.empty():
                message = Client.messagePile.get()
                
                #try:
                self.sendMessage(message)
                #except:
                #    print("Error occured sending a message")
                
                #if conn.getresponse().status != 200 :
                #    self.messagePile.add( message )

    def sendMessage(self, message):
        #serialize our message
        serializedMessage = pickle.dumps( message, 3)
        #put it in a dictionnary
        params = {Consts.POST_MESSAGE_KEYWORD : serializedMessage}
        #transform dictionnary into string
        params = urllib.parse.urlencode(params, doseq = True, encoding=Consts.POST_MESSAGE_ENCODING)
        #set the header as header for POST
        headers = {"Content-type": "application/x-www-form-urlencoded;charset="+ Consts.POST_MESSAGE_ENCODING, "Accept": "text/plain"}
        conn = ProbeStorage.dicoConnection[message.targetId]
        conn.request("POST", "", params, headers)
#         response = conn.getresponse()
#         
#         if response.status != 200 :
#             self.send(message)

