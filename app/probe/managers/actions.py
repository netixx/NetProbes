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
from exceptions import TestError, TestArgumentError, TestInProgress
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
            getattr(ActionMan, ActionMan.manager.get(task.__class__.__name__))(task)
            Server.taskDone()
    
    @staticmethod
    def manageAdd(action):
        assert isinstance(action, a.Add)
        ActionMan.logger.info("Managing Add task")
        #add the probe to the local DHT
        ProbeStorage.addProbe(Probe(action.getIdSonde(), action.getIpSonde()))

        if action.doHello:
            # tell the new probe about all other probe
            Client.send(Hello(action.getIdSonde(), list(ProbeStorage.getAllOtherProbes()), sourceId = Identification.PROBE_ID))

    @staticmethod
    def manageUpdateProbes(action):
        assert isinstance(action, a.UpdateProbes)
        for probe in action.getProbeList():
            if probe.getId() != Identification.PROBE_ID:
                ProbeStorage.addProbe(Probe(probe.getId(), probe.getIp()))

    @staticmethod
    def manageRemove(action):
        assert isinstance(action, a.Remove)
        ActionMan.logger.info("Managing Remove task")
        try:
            ProbeStorage.delProbe( action.getIdSonde() );
        except:
            ActionMan.logger.warning("Probe not found in hashtable")
    
    @staticmethod
    def manageDo(action):
        assert isinstance(action, a.Do)
        ActionMan.logger.info("Managing Do task")
        # instantiate the right test
        ActionMan.logger.info("Starting test " + action.getTest())

        try:
            try:
                try :
                    test = tests.testFactory(action.getTest())
                except ImportError as e:
                    raise TestError("Test class not found")
                test = test(action.getOptions())
                # This line blocks the ActionMan
                TestManager.initTest(test)
                ActionMan.logger.info("Test Over " + test.__class__.__name__)
                result = test.getResult()
                ActionMan.logger.info("Result of the test is a follows : \n" + result)
                CommanderServer.addResult(result)
            except TestArgumentError as e:
                raise TestError(e.getUsage())

        except TestError as e:
            ActionMan.logger.warning("Test failed because :" + e.getReason(), exc_inf = 1)
            CommanderServer.addResult(e.getReason())
        
        # @todo : send result to whoever!
    
    @staticmethod
    def managePrepare(action):
        assert(isinstance(action, a.Prepare))
        ActionMan.logger.info("Manage prepare test " + "(" + " ".join(action.getTestId()) + ")")
        try:
            TestResponder.initTest(action.getTestId(), action.getSourceId(), action.getTestOptions())
            # block all other actions
            TestResponder.testDone.wait()
        except TestInProgress:
            ActionMan.logger.warning("Error : a test is in progress already")
        except:
            ActionMan.logger.error("Unknown error during prepare", exc_info = 1)
    
    
    @staticmethod
    def manageQuit(action):
        assert isinstance(action, a.Quit)
        ActionMan.logger.info("Managing Quit task")
        Client.broadcast( Bye("", Identification.PROBE_ID), toMyself = False )
        ''' Other commands to close all connections, etc '''
        Client.allMessagesSent()
        ProbeStorage.closeAllConnections()
        ActionMan.logger.info("All connections closed")
        ProbeStorage.addProbe(Probe(str(Identification.PROBE_ID), "localhost"))
        ActionMan.logger.info("Re-added the localhost probe, ready to proceed again")
