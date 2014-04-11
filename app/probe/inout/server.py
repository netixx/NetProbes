'''
Server that listens to probe messages

@author: francois
'''
__all__ = ['Server']

from .client import Client
from calls.actions import Action
from calls.messages import Message, TesterMessage, TesteeAnswer, BroadCast, \
    TestMessage, Hello
import calls.messagetoaction as MTA
from consts import Params, Identification
from managers.probes import ProbeStorage
from managers.tests import TestManager, TestResponder
from threading import Thread, Event
import logging
from managers.actions import ActionMan

class Server(Thread):
    '''
    Server thread listens on the given port to a POST request containing
    a serialization of a Message object
    It then transforms this Message into a corresponding Action
    that is added to the Queue of actions that the server must execute

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
        if isinstance(message, TestMessage):
            cls.treatTestMessage(message)
        elif isinstance(message, BroadCast):
            cls.logger.debug("Handling Broadcast")
            ActionMan.addTask(MTA.toAction(message.getMessage()))
            Client.broadcast(message)
        else:
            ActionMan.addTask(MTA.toAction(message))

    @classmethod
    def treatTestMessage(cls, message):
        cls.logger.debug("Handling Tester or Testee message")
        assert isinstance(message, TestMessage)
        # if probe is in test mode, give the message right to the TestManager!
        if (isinstance(message, TesteeAnswer)):
            cls.logger.debug("Handling TesteeAnswer")
            TestManager.handleMessage(message)
        elif (isinstance(message, TesterMessage)):
            cls.logger.debug("Handling TesterMessage")
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
            from managers.actions import ActionMan
            return ActionMan.getStatus()
    
        def handleResponse(self, response, message):
            if (isinstance(message, Hello)):
                message.setRemoteIp(response.client_address[0])
            return "ok"

        def getLogger(self):
            return self.server.logger

