'''
Created on 7 juin 2013

@author: francois
'''
import urllib, pickle
from threading import Thread, Event
from probe.consts import Consts, debug, Identification
from queue import Queue
from calls.messages import Message, BroadCast
from probes import ProbeStorage
from probe.exceptions import NoSuchProbe


class Client(Thread):
    '''
    Client Thread : talks to the Server through http
    Server can be local (localhost) or remote
    Connection is established as a Probe is added to ProbeStorage through ProbeStorage.addProbe through http on the port given by Consts.PORT_NUMBER
    
    '''
    messageStack = Queue()
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
        cls.messageStack.put(message)
    
    @classmethod
    def broadcast(cls, message, toMyself = False):
        debug("Client : Broadcasting the message : " + message.__class__.__name__)
        #propagation phas
        if isinstance(message, BroadCast):
            prop = message.getNextTargets()
        else:
            prop = ProbeStorage.getIdAllOtherProbes()
            if toMyself:
                prop.append(Identification.PROBE_ID)
            
        if len(prop) > 0:
            splitSize = min(Consts.PROPAGATION_RATE, len(prop))
            j = splitSize
            step = len(prop) / splitSize
            for i in range(0, splitSize - 1):
                propIds = prop[j:j + step]
                j += step
                cls.send(BroadCast(message, propIds))
            # be sure to propagate to all probes
            cls.send(BroadCast(message, prop[j:]))
# 
#         with ProbeStorage.knownProbesLock:
#             for probeId in ProbeStorage.getKeys():
#                 if probeId != Identification.PROBE_ID or toMyself :
#                     msg = copy.deepcopy(message)
#                     msg.setTarget(probeId)
#                     cls.send(msg)
                
    def run(self):
        self.isUp.set()
        debug("Client : starting the client")
        while not Client.stop or not Client.messageStack.empty():
            message = Client.messageStack.get()
            try:
                self.sendMessage(message)
            finally:
                Client.messageStack.task_done()
                #except:
                #    print("Error occured sending a message")
                
                #if conn.getresponse().status != 200 :
                #    self.messageStack.add( message )

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
            target = ProbeStorage.getProbeById(message.targetId)
            disconnectOnCompletion = False
            if not target.connected :
                target.connect()
                disconnectOnCompletion = True
            conn = target.getConnection()
            conn.request("POST", "", params, headers)
            debug("Client : Message : " + message.__class__.__name__ + " has been sent")
            response = conn.getresponse()
            if response.status != 200 :
                debug("Client : Wrong status ! Trying to resend")
                self.send(message)
            if disconnectOnCompletion:
                # TODO: optimise if target is still in the stack
                target.disconnect()
        except NoSuchProbe:
            debug("The probe you requested to send a message to : '" + message.targetId + "', is currently unkown to me.")
       

    @classmethod
    def allMessagesSent(cls):
        cls.messageStack.join()
