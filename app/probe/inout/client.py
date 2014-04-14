'''
Sends Message instances to other probes
    Thread that waits for a message to be added to the messageStack
    and sends message as soon as one is added

It also implements a mechanism to broadcast a message to all probes

@author: francois

'''
__all__ = ['Client']

from queue import Queue
from threading import Thread, Event
import logging

from calls.messages import Message, BroadCast
from consts import Consts, Identification, Params
from managers.probes import ProbeStorage
from interfaces.excs import NoSuchProbe

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
        self.sender = Params.PROTOCOL.Sender(self.logger)

    def run(self):
        self.isUp.set()
        self.logger.info("Starting the Client")
        while not Client.stop or not Client.messageStack.empty():
            message = Client.messageStack.get()
            try:
#                 if isinstance(message, StatusMessage):
#                     self.sendStatusMessage(message)
#                 else:
                self.sendMessage(message)
            finally:
                Client.messageStack.task_done()


    @classmethod
    def quit(cls):
        cls.logger.info("Stopping the Client")
        cls.stop = True
        ProbeStorage.closeAllConnections()
    
    @classmethod
    def send(cls, message):
        '''
        Send message to target probe
        message : message to send (contains the targetId)
        
        '''
        cls.logger.debug("Adding a message %s to the client stack", message.__class__.__name__)
        assert isinstance(message, Message)
        cls.messageStack.put(message)
        cls.logger.debug("Message %s added to the stack", message.__class__.__name__)
    
    @classmethod
    def broadcast(cls, message, toMyself = False):
        '''
        If called with a Broadcast message, the method will send
        messages to all targets listed in the broadcast
        If called with a Message instance, the method will send a message
        to all known probes

        '''
        cls.logger.debug("Broadcasting the message : %s", message.__class__.__name__)
        # propagation phase
        if isinstance(message, BroadCast):
            prop = message.getNextTargets()
        else:
            prop = ProbeStorage.getIdAllOtherProbes()
            if toMyself:
                # make sure we are the first on our list
                prop.insert(0, Identification.PROBE_ID)

        if len(prop) == 1:
            message.targetId = prop[0]
            cls.send(message)
        elif len(prop) > 1:
            if len(prop) < Consts.PROPAGATION_RATE:
                cls.send(BroadCast(prop[0], message, prop[1:]))
            
            pRate = Consts.PROPAGATION_RATE
            # take targets for first hop out of the list
            sendTo = prop[0:pRate]
            i = 1
            while (i + 1) * pRate < len(prop):
                propIds = prop[i * pRate:(i + 1) * pRate]
                cls.send(BroadCast(sendTo[i], message, propIds))
                i = i + 1
            # be sure to propagate to all probes
            cls.send(BroadCast(sendTo[i], message, prop[i * pRate:]))

    @classmethod
    def allMessagesSent(cls):
        cls.messageStack.join()
        
    '''Inner functions'''
        
    def sendMessage(self, message):
        try :
            self.logger.debug("Sending the message : %s to %s with ip %s",
                      message.__class__.__name__ ,
                      message.getTarget(),
                      ProbeStorage.getProbeById(message.getTarget()).getIp())
        except NoSuchProbe:
            self.logger.debug("Probe unknown")
        self.sender.send(message)

#     def sendStatusMessage(self, statusMessage):
#         try :
#             target = ProbeStorage.getProbeById(statusMessage.targetId)
#             response = self._sendMessage(target, Consts.HTTP_GET_REQUEST, Urls.SRV_STATUS_QUERY)
#
#             contentLength = response.headers.get("content-length")
#             # read content
#             args = self.rfile.read(int(contentLength))
#             # convert from bytes to string
#             args = str(args, Consts.POST_MESSAGE_ENCODING)
#             # parse our string to a dictionary
#             args = urllib.parse.parse_qs(args, keep_blank_values = True, strict_parsing = True, encoding = Consts.POST_MESSAGE_ENCODING)
#             # get our object as string and transform it to bytes
#             probeStatus = bytes(args.get(Consts.POST_MESSAGE_KEYWORD)[0], Consts.POST_MESSAGE_ENCODING)
#             # transform our bytes into an object
#             probeStatus = Params.CODEC.decode(probeStatus)
#             return probeStatus
#         except NoSuchProbe:
#             pass
