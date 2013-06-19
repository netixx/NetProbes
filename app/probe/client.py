'''
Created on 7 juin 2013

@author: francois
'''
import urllib, pickle
from threading import Thread, Event
from consts import Consts,Params, debug
from queue import Queue
from messages import Message
from probes import ProbeStorage
from exceptions import NoSuchProbe
import copy


'''
    Client Thread : talks to the Server through http
    Server can be local (localhost) or remote
    Connection is established as a Probe is added to ProbeStorage through ProbeStorage.addProbe through http on the port given by Consts.PORT_NUMBER
'''
class Client(Thread):
    
    messagePile = Queue()
    stop = False
    
    def __init__(self):
        Thread.__init__(self)
        self.setName("Client")
        self.isUp = Event()
    
    
    @classmethod
    def quit(cls):
        debug("Client : Killing the Client")
        ProbeStorage.closeAllConnections()
        cls.stop = True
    
    @classmethod
    def send(cls, message):
        debug("Client : Giving a message " + message.__class__.__name__ + " to the client")
        assert isinstance(message, Message)
        cls.messagePile.put(message)
    
    @classmethod
    def broadcast(cls, message):
        debug("Client : Broadcasting the message : " + message.__class__.__name__)
        for probeId in ProbeStorage.connectedProbes.keys():
            msg = copy.deepcopy(message)
            msg.setTarget(probeId)
            cls.send(msg)
                
    def run(self):
        self.isUp.set()
        debug("Client : starting the client")
        while not Client.stop or not Client.messagePile.empty():
            
            if not Client.messagePile.empty():
                message = Client.messagePile.get()
                #try:
                self.sendMessage(message)
                #except:
                #    print("Error occured sending a message")
                
                #if conn.getresponse().status != 200 :
                #    self.messagePile.add( message )

    def sendMessage(self, message):
        debug("Client : Sending the message : " + message.__class__.__name__)
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
            debug("Client : Message : " + message.__class__.__name__ + " has been sent")
        except NoSuchProbe:
            debug("The probe you requested to send a message to : '" + message.targetId + "', is currently unkown to me.")
#         response = conn.getresponse()
#         
#         if response.status != 200 :
#             self.send(message)

