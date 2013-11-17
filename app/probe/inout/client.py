'''
Sends Message instances to other probes
    Thread that waits for a message to be added to the messageStack

Created on 7 juin 2013

@author: francois
'''
import urllib, pickle
from threading import Thread, Event
from consts import Consts, Identification
from queue import Queue
from calls.messages import Message, BroadCast
from managers.probes import ProbeStorage
from exceptions import NoSuchProbe
import logging

class Client(Thread):
    '''
    Client Thread : talks to the Server through http
    Server can be local (localhost) or remote
    
    '''
    messageStack = Queue()
    stop = False
    logger = logging.getLogger()
    
    def __init__(self):
        Thread.__init__(self)
        self.setName("Client")
        self.isUp = Event()
    
    
    @classmethod
    def quit(cls):
        cls.logger.info("Stopping the Client")
        ProbeStorage.closeAllConnections()
        cls.stop = True
    
    @classmethod
    def send(cls, message):
        cls.logger.debug("Adding a message " + message.__class__.__name__ + " to the client stack")
        assert isinstance(message, Message)
        cls.messageStack.put(message)
    
    @classmethod
    def broadcast(cls, message, toMyself = False):
        cls.logger.debug("Broadcasting the message : " + message.__class__.__name__)
        #propagation phas
        if isinstance(message, BroadCast):
            prop = message.getNextTargets()
        else:
            prop = ProbeStorage.getIdAllOtherProbes()
            if toMyself:
                prop.append(Identification.PROBE_ID)
            
        if len(prop) > 0:
            splitSize = min(Consts.PROPAGATION_RATE, len(prop))
            j = 0
            step = len(prop) / splitSize
            while j < len(prop):
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
        self.logger.info("Starting the client")
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
        self.logger.debug("Sending the message : " + message.__class__.__name__)
        #serialize our message
        serializedMessage = pickle.dumps( message, 3)
        #put it in a dictionnary
        params = {Consts.POST_MESSAGE_KEYWORD : serializedMessage}
        #transform dictionnary into string
        params = urllib.parse.urlencode(params, doseq = True, encoding=Consts.POST_MESSAGE_ENCODING)
        #set the header as header for POST
        headers = {"Content-type": "application/x-www-form-urlencoded;charset=%s" % Consts.POST_MESSAGE_ENCODING, "Accept": "text/plain"}
        try :
            target = ProbeStorage.getProbeById(message.targetId)
            disconnectOnCompletion = False
            if not target.connected :
                target.connect()
                disconnectOnCompletion = True
            conn = target.getConnection()
            conn.request("POST", "", params, headers)
            self.logger.info("Message : " + message.__class__.__name__ + " has been sent")
            response = conn.getresponse()
            if response.status != 200 :
                self.logger.warning("Wrong status received! Trying to resend message.")
                self.send(message)
            if disconnectOnCompletion:
                # TODO: optimise if target is still in the stack
                target.disconnect()
        except NoSuchProbe:
            self.logger.error("The probe you requested to send a message to : '%s', is currently unknown to me.", message.targetId)
       

    @classmethod
    def allMessagesSent(cls):
        cls.messageStack.join()
