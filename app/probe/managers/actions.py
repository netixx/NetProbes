'''
Manages actions from the stack of actions to be performed
    This actually performs the Actions

The ActionMan is an independent thread waiting for one or more
action to be pushed to the stack.

Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
import calls.actions as a
from managers.probes import Probe, ProbeStorage
from calls.messages import Hello, Bye
from .tests import TestResponder, TestManager
from inout.server import Server
from inout.client import Client
from inout.commanderServer import CommanderServer
from . import tests
from exceptions import TestError, TestArgumentError, TestInProgress, ActionError, \
    NoSuchProbe
import logging
from consts import Identification

class ActionMan(Thread):

    '''Links Action classes to (static) methods'''
    manager = { "Add" : "manageAdd",
            "Remove" : "manageRemove",
            "Transfer" : "manageTransfer",
            "Do" : "manageDo",
            "Quit" : "manageQuit",
            "Prepare" : "managePrepare",
            "UpdateProbes" : "manageUpdateProbes" }
    
    logger = logging.getLogger()

    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    def quit(self):
        self.logger.info("Stopping ActionMan !")
        self.stop = True
    
    def run(self):
        while not self.stop:
            task = Server.getTask()
            try:
                getattr(ActionMan, ActionMan.manager.get(task.__class__.__name__))(task)
            except ActionError:
                # convert to warning ??
                self.logger.error("Action execution failed", exc_info = 1)
            except:
                self.logger.error("Unexpected error occurred while treating action", exc_info = 1)
            Server.taskDone()
    
    @staticmethod
    def manageAdd(action):
        assert isinstance(action, a.Add)
        ActionMan.logger.debug("Managing Add task")
        #add the probe to the local DHT
        ProbeStorage.addProbe(ProbeStorage.newProbe(action.getIdSonde(), action.getIpSonde()))

        if action.doHello:
            # tell the new probe about all other probe
            Client.send(Hello(action.getIdSonde(), list(ProbeStorage.getAllOtherProbes()), sourceId = Identification.PROBE_ID))

    @staticmethod
    def manageUpdateProbes(action):
        assert isinstance(action, a.UpdateProbes)
        for probe in action.getProbeList():
            # don't re-add ourself to the local DHT
            if probe.getId() != Identification.PROBE_ID:
                ProbeStorage.addProbe(ProbeStorage.newProbe(probe.getId(), probe.getIp()))

    @staticmethod
    def manageRemove(action):
        assert isinstance(action, a.Remove)
        ActionMan.logger.debug("Managing Remove task")
        try:
            ProbeStorage.delProbeById(action.getIdSonde());
        except NoSuchProbe:
            ActionMan.logger.warning("Probe not found in hashtable")
    
    @staticmethod
    def manageDo(action):
        assert isinstance(action, a.Do)
        ActionMan.logger.debug("Managing Do task")
        ActionMan.logger.info("Starting test " + action.getTest())
        try:
            try:
                # instantiate the right test
                test = tests.testFactory(action.getTest())
                try :
                    test = test(action.getOptions())
                    # This line blocks the ActionMan
                    TestManager.initTest(test)
                    ActionMan.logger.info("Test Over " + test.__class__.__name__)
                    result = test.getResult()
                    ActionMan.logger.info("Result of the test is a follows : \n" + result)
                    CommanderServer.addResult(result)
                except TestArgumentError as e:
                    CommanderServer.addError(e.getUsage())
                    ActionMan.logger.warning("Test called with wrong arguments or syntax : %s", action.getOptions())
            except ImportError as e:
                raise TestError("Could not load test class for test : %s", action.getTest())

        except TestError as e:
            CommanderServer.addError(e.getReason())
            raise e
        
    @staticmethod
    def managePrepare(action):
        assert(isinstance(action, a.Prepare))
        ActionMan.logger.info("Prepare for test (%s)" , " ".join(action.getTestId()))
        try:
            TestResponder.initTest(action.getTestId(), action.getSourceId(), action.getTestOptions())
            # block all other actions
            TestResponder.testDone.wait()
        except TestInProgress:
            ActionMan.logger.warning("Error : a test is in progress already")

    @staticmethod
    def manageQuit(action):
        assert isinstance(action, a.Quit)
        ActionMan.logger.debug("Managing Quit task")
        ActionMan.logger.info("Exiting the overlay")
        Client.broadcast( Bye("", Identification.PROBE_ID), toMyself = False )
        ''' Other commands to close all connections, etc '''
        Client.allMessagesSent()
        ProbeStorage.clearAllProbes()
        ActionMan.logger.info("All probes cleared, all connections closed.")
        # TODO: check duplicate action in server
        ProbeStorage.addSelfProbe()
        ActionMan.logger.info("Re-added the localhost probe, ready to proceed again")

    @staticmethod
    def getStatus():
        # TODO : implement
        return "ok"
