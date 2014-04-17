'''
Server that listens to probe messages

@author: francois
'''
__all__ = ['Server']

import copy
from threading import Thread, Event
import logging

from .client import Client
from calls.messages import Message, TesterMessage, TesteeAnswer, BroadCast, \
    TestMessage, Hello, Add, AddToOverlay
import calls.messagetoaction as MTA
from consts import Params, Identification
from managers.probes import ProbeStorage
from managers.probetests import TestManager, TestResponder
from managers.actions import ActionMan
from interfaces.excs import ActionError


class Server(Thread):
    '''
    Server thread listens on the given port to a POST request containing
    a serialization of a Message object
    It then transforms this Message into a corresponding Action
    that is added to the Queue of actions that the ActionManager must execute

    It also listens to get request an replies its id to whoever asks it!
    
    '''

    logger = logging.getLogger()
    
    def __init__(self):
        self.helper = self.Helper(self)
        self.listener = Params.PROTOCOL.Listener(self.helper)
        #init the thread
        Thread.__init__(self)
        self.setName("Server")
        self.isUp = Event()
        ProbeStorage.addSelfProbe()
    
    def run(self):
        self.logger.info("Starting Server")
        self.listener.start()
        self.isUp.set()

    def quit(self):
        self.logger.info("Closing Server")
        self.listener.close()

    @classmethod
    def treatMessage(cls, message):
        '''Handles the receptions of a Message (called by the listener)
        For regular actions, addTask is called after translation of the message
        For TesterMessages and TesteeMessages, treatTestMessage is called

        '''
        cls.logger.debug("Treating message %s", message.__class__.__name__)
        assert isinstance(message, Message)
        # forwarding mechanism
#         if message.targetId != Identification.PROBE_ID:
#             cls.logger.info("Forwarding message %s to id %s", message.__class__.__name__, message.targetId)
#             Client.send(message)
#             return
        if isinstance(message, TestMessage):
            cls.treatTestMessage(message)
        elif isinstance(message, BroadCast):
            cls.logger.ddebug("Handling Broadcast")
            try:
                ActionMan.addTask(MTA.toAction(message.getMessage()))
            except ActionError:
                pass
            Client.broadcast(message)
        elif isinstance(message, AddToOverlay):
            cls.logger.debug("Add probe to overlay")
            probeId = Params.PROTOCOL.getRemoteId(message.getProbeIp())

            addMessage = Add(Identification.PROBE_ID, probeId, message.getProbeIp())
            selfAddMessage = copy.deepcopy(addMessage)
            selfAddMessage.doHello = True
            # Do broadcast before adding the probe so that it doesn't receive unnecessary message
            # addMessage = m.Add(Identification.PROBE_ID, probeId, message.targetIp, hello=True)
            Client.broadcast(addMessage)
            cls.treatMessage(selfAddMessage)
        else:
            ActionMan.addTask(MTA.toAction(message))

    @classmethod
    def treatTestMessage(cls, message):
        cls.logger.ddebug("Handling Tester or Testee message")
        assert isinstance(message, TestMessage)
        # if probe is in test mode, give the message right to the TestManager!
        if (isinstance(message, TesteeAnswer)):
            cls.logger.ddebug("Handling TesteeAnswer")
            TestManager.handleMessage(message)
        elif (isinstance(message, TesterMessage)):
            cls.logger.ddebug("Handling TesterMessage")
            TestResponder.handleMessage(message)
        else:
            ActionMan.addTask(MTA.toAction(message))
    
    class Helper(object):
        def __init__(self, server):
            self.server = server

        def treatMessage(self, message):
            self.server.treatMessage(message)
        
        def getId(self):
            return Identification.PROBE_ID
    
        def getStatus(self):
            return ActionMan.getStatus()
    
        def handleResponse(self, response, message):
            if (isinstance(message, Hello)):
                message.setRemoteIp(response.client_address[0])
            return "ok"

        def getLogger(self):
            return self.server.logger

