'''
Created on 7 juin 2013

@author: francois
'''
import urllib, pickle
from threading import Thread
from consts import Consts,Params
from queue import Queue
from messages import Message
from probes import ProbeStorage
from exceptions import NoSuchProbe

'''
    Client Thread : talks to the Server through http
    Server can be local (localhost) or remote
    Connection is established as a Probe is added to ProbeStorage through ProbeStorage.addProbe through http on the port given by Consts.PORT_NUMBER
'''
class Client(Thread):
    messagePile = Queue()

    def __init__(self):
        Thread.__init__(self)
        self.stop = False
        self.setName("Client")
    
    def quit(self):
        ProbeStorage.closeAllConnections()
        self.stop = True
    
    @classmethod
    def send(cls, message):
        assert isinstance(message, Message)
        cls.messagePile.put(message)
    
    @classmethod
    def broadcast(cls, message):
        for probeId in ProbeStorage.keys():
            msg = message.deepcopy()
            msg.setTarget(probeId)
            cls.messagePile.put(msg)
        
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
        try :
            conn = ProbeStorage.getProbeById(message.targetId).getConnection()
            conn.request("POST", "", params, headers)
        except NoSuchProbe:
            if Params.DEBUG:
                print("The probe you requested to send a message to : '" + message.targetId + "', is currently unkown to me.")
#         response = conn.getresponse()
#         
#         if response.status != 200 :
#             self.send(message)

