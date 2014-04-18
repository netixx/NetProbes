"""
Server that listens to probe messages sent according to the chosen Params.PROTOTOL.
The network side of the server (listening to requests...) is given to this protocol.
Interacts with managers.action.ActionMan by supplying action to be executed.
It makes the link between messages sent across the network and actions that must
be performed for this probe.

@author: francois
"""
__all__ = ['Server']

import copy
from threading import Thread, Event, RLock
import logging

from .client import Client
from calls.messages import Message, TesterMessage, TesteeAnswer, BroadCast, \
    TestMessage, Hello, Add, AddToOverlay
import calls.messagetoaction as MTA
from consts import Params, Identification
from managers.probes import ProbeStorage
from managers.probetests import TestManager, TestResponder
from managers.actions import ActionMan
from interfaces.excs import ActionError, ProbeConnectionException


class Server(Thread):
    """
    It then transforms a Message, read by the specified PROTOCOL into a corresponding
    Action (via messagetoaction).
    It adds those Action to the ActionMan who then treats them accordingly

    There are also method which are used to help initialisation like replying to requests
    for ID. It uses a helper object which is given to the PROTOCOL on initialisation of the
    listener. This Helper acts as an interface on the probe/server/action manager properties.

    """

    logger = logging.getLogger()
    _addLock = RLock()
    def __init__(self):
        self.helper = self.Helper(self)
        self.listener = Params.PROTOCOL.Listener(self.helper)
        #init the thread
        Thread.__init__(self)
        self.setName("Server")
        self.isUp = Event()
        ProbeStorage.addSelfProbe()

    def run(self):
        """Start treating messages"""
        self.logger.info("Starting Server")
        self.listener.start()
        self.isUp.set()

    def quit(self):
        """Stop treating messages"""
        self.logger.info("Closing Server")
        self.listener.close()

    @classmethod
    def treatMessage(cls, message):
        """Handles the receptions of a Message (called by the listener)
        For regular Actions, addTask is called after translation of the message
        For TesterMessages and TesteeMessages, treatTestMessage is called
        :param message: The Message instance to treat

        """
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
            # be sure to propagate broadcast if a reasonable error occurs
            Client.broadcast(message)
        elif isinstance(message, AddToOverlay):
            cls.logger.debug("Add probe to overlay")
            try:
                with cls._addLock:
                    probeId = Params.PROTOCOL.getRemoteId(message.getProbeIp())

                    addMessage = Add(Identification.PROBE_ID, probeId, message.getProbeIp())
                    selfAddMessage = copy.deepcopy(addMessage)
                    selfAddMessage.doHello = True
                    # Do broadcast before adding the probe so that it doesn't receive unnecessary message
                    # addMessage = m.Add(Identification.PROBE_ID, probeId, message.targetIp, hello=True)
                    Client.broadcast(addMessage)
                    cls.treatMessage(selfAddMessage)
            except ProbeConnectionException as e:
                cls.logger.info("Adding probe failed %s : %s", message.getProbeIp(), e)
        else:
            # handles everything else, including Do messages
            ActionMan.addTask(MTA.toAction(message))

    @classmethod
    def treatTestMessage(cls, message):
        """Treats a test message which can be Testee or Tester kind
        Testee are given to TesteeManager
        Tester are given to testResponder
        :param message: testMessage to treat

        """
        cls.logger.ddebug("Handling Tester or Testee message")
        assert isinstance(message, TestMessage)
        # if probe is in test mode, give the message right to the TestManager!
        if isinstance(message, TesteeAnswer):
            cls.logger.ddebug("Handling TesteeAnswer")
            TestManager.handleMessage(message)
        elif isinstance(message, TesterMessage):
            cls.logger.ddebug("Handling TesterMessage")
            TestResponder.handleMessage(message)
        elif isinstance(message, TestMessage):
            #Prepare are test messages
            ActionMan.addTask(MTA.toAction(message))

    class Helper(object):
        """Helper object to enable interaction with Server from the protocol"""
        def __init__(self, server):
            self.server = server

        def treatMessage(self, message):
            """Treat given message, call Server.treatMessage
            :param message: Message instance to treat

            """
            self.server.treatMessage(message)

        @staticmethod
        def getId():
            """Return the ID of this probe"""
            return Identification.PROBE_ID

        def getStatus(self):
            """Return current probe status"""
            return ActionMan.getStatus()

        def handleResponse(self, response, message):
            """Responds to the request (ack)
            :param response: response object
            :param message: message to respond to
            """
            if isinstance(message, Hello):
                message.setRemoteIp(response.client_address[0])
            return "ok"

        def getLogger(self):
            """Return the server's logger"""
            return self.server.logger

