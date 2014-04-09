'''
Manages actions from the stack of actions to be performed
    This actually performs the Actions

The ActionMan is an independent thread waiting for actions
 to be pushed to the stack.

@author: Gaspard FEREY
'''
__all__ = ['ActionMan']

from threading import Thread
import logging
from calls.messages import Hello, Bye
from consts import Identification
from inout.client import Client
from inout.commanderServer import CommanderServer
from inout.server import Server
from managers.probes import ProbeStorage
from exceptions import TestError, TestArgumentError, TestInProgress, ActionError, \
    NoSuchProbe
import calls.actions as a
from .tests import TestResponder, TestManager

class ActionMan(Thread):

    '''Links Action classes to (static) methods'''
    manager = { "Add" : "manageAdd",
                "Remove" : "manageRemove",
                "Transfer" : "manageTransfer",
                "Do" : "manageDo",
                "Quit" : "manageQuit",
                "Prepare" : "managePrepare",
                "UpdateProbes" : "manageUpdateProbes"
              }
    
    logger = logging.getLogger()

    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    def run(self):
        while not self.stop:
            task = Server.getTask()
            try:
                getattr(self.__class__, self.manager.get(task.__class__.__name__))(task)
            except ActionError:
                # TODO: convert to warning ??
                self.logger.error("Action execution failed", exc_info = 1)
            except:
                self.logger.error("Unexpected error occurred while treating action", exc_info = 1)
            Server.taskDone()

    def quit(self):
        self.logger.info("Stopping ActionMan !")
        self.stop = True
    
    @classmethod
    def manageAdd(cls, action):
        '''Add a probe to the DHT'''
        assert isinstance(action, a.Add)
        cls.logger.debug("Managing Add task")
        #add the probe to the local DHT
        ProbeStorage.addProbe(ProbeStorage.newProbe(action.getIdSonde(), action.getIpSonde()))
        if action.doHello:
            # tell the new probe about all other probe
            Client.send(Hello(action.getIdSonde(), list(ProbeStorage.getAllOtherProbes()), sourceId = Identification.PROBE_ID))

    @classmethod
    def manageUpdateProbes(cls, action):
        assert isinstance(action, a.UpdateProbes)
        for probe in action.getProbeList():
            # don't re-add ourself to the local DHT
            if probe.getId() != Identification.PROBE_ID:
                ProbeStorage.addProbe(ProbeStorage.newProbe(probe.getId(), probe.getIp()))

    @classmethod
    def manageRemove(cls, action):
        assert isinstance(action, a.Remove)
        cls.logger.debug("Managing Remove task")
        try:
            # remove probe from DHT
            ProbeStorage.delProbeById(action.getIdSonde());
        except NoSuchProbe:
            cls.logger.warning("Probe not found in hashtable")
    
    @classmethod
    def manageDo(cls, action):
        '''
        Initiate a new test
        A new thread is created for this test by the TestManager so
        this method does not block the ActionManager

        '''
        assert isinstance(action, a.Do)
        cls.logger.debug("Managing Do task")
        cls.logger.info("Starting test %s", action.getTestName())
        try:
            testId = TestManager.startTest(action.getTestName(), action.getTestOptions())
            # TODO: manage results here
        except TestArgumentError as e:
            CommanderServer.addError(e.getUsage())
            cls.logger.warning("Test called with wrong arguments or syntax : %s", action.getOptions())
        except TestError as e:
            CommanderServer.addError(e.getReason())
            raise e
        
    @classmethod
    def managePrepare(cls, action):
        '''
        Respond to a new test
        A new thread is created by the TestResponder,
        a probe can respond to multiple tests at once

        '''
        assert(isinstance(action, a.Prepare))
        cls.logger.info("Prepare for test (%s-%s)" , action.getTestName(), action.getTestId())
        try:
            TestResponder.startTest(action.getTestId(), action.getTestName(), action.getSourceId(), action.getTestOptions())
        except TestError:
            cls.logger.error("Error while preparing for test %s-%s", action.getTestName(), action.getTestId(), exc_info = 1)

    @classmethod
    def manageQuit(cls, action):
        assert isinstance(action, a.Quit)
        cls.logger.debug("Managing Quit task")
        cls.logger.info("Exiting the overlay")
        Client.broadcast( Bye("", Identification.PROBE_ID), toMyself = False )
        ''' Other commands to close all connections, etc '''
        Client.allMessagesSent()
        ProbeStorage.clearAllProbes()
        cls.logger.info("All probes cleared, all connections closed.")
        # TODO: check duplicate action in server
        ProbeStorage.addSelfProbe()
        cls.logger.info("Re-added the localhost probe, ready to proceed again")

    @classmethod
    def getStatus(cls):
        # TODO: implement
        return "ok"
