'''
Created on 13 juin 2013

@author: Gaspard FEREY
'''

from threading import Thread
import calls.actions as a
from probes import Probe, ProbeStorage
from client import Client
from probe.consts import *
from calls.messages import Hello, Bye, Add
from tests import TestResponder, TestManager
from server import Server
import tests
from commanderServer import CommanderServer
from probe.exceptions import TestError, TestArgumentError, TestInProgress

class ActionMan(Thread):

    manager = { "Add" : "manageAdd",
            "Remove" : "manageRemove",
            "Transfer" : "manageTransfer",
            "Do" : "manageDo",
            "Quit" : "manageQuit",
            "Prepare" : "managePrepare",
            "UpdateProbe" : "manageUpdateProbe" }
    
    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    def quit(self):
        debug("Action Manager : Killing ActionMan !")
        self.stop = True
    
    def run(self):
        while not self.stop:
            task = Server.getTask()
            getattr(ActionMan, ActionMan.manager.get(task.__class__.__name__))(task)
            Server.taskDone()
    
    @staticmethod
    def manageAdd(action):
        assert isinstance(action, a.Add)
        debug("ActionMan : managing Add task")
        #add the probe to the local DHT
        ProbeStorage.addProbe(Probe(action.getIdSonde(), action.getIpSonde()))

        if action.doHello:
            # tell the new probe about all other probe
            Client.send(Hello(action.getIdSonde(), ProbeStorage.getAllProbes()))

    @staticmethod
    def manageUpdateProbe(action):
        assert isinstance(action, a.UpdateProbes)
        for probe in action.getProbeList():
            ProbeStorage.addProbe(probe)

    @staticmethod
    def manageRemove(action):
        assert isinstance(action, a.Remove)
        debug("ActionMan : managing Remove task")
        try:
            ProbeStorage.delProbe( action.getIdSonde() );
        except:
            debug("ActionMan : Probe not found")
    
    @staticmethod
    def manageDo(action):
        assert isinstance(action, a.Do)
        debug("ActionMan : managing Do task")
        # instantiate the right test
        debug("ActionMan : Starting test " + action.getTest())

        try:
            try:
                test = tests.testFactory(action.getTest())
                test = test(action.getOptions())
                # This line blocks the ActionMan
                TestManager.initTest(test)
                debug("ActionMan : Test Over " + test.__class__.__name__)
                result = test.getResult()
                debug("ActionMan : Result of the test is a follows : \n" + result)
                CommanderServer.addResult(result)
            except TestArgumentError as e:
                raise TestError(e.getUsage())

        except TestError as e:
            debug("ActionMan : Test failed because :" + e.getReason())
            CommanderServer.addResult(e.getReason())
        
        # @todo : send result to whoever!
    
    @staticmethod
    def managePrepare(action):
        assert(isinstance(action, a.Prepare))
        debug("ActionMan : manage prepare test " + "(" + " ".join(action.getTestId()) + ")")
        try:
            TestResponder.initTest(action.getTestId(), action.getSourceId(), action.getTestOptions())
            # block all other actions
            TestResponder.testDone.wait()
        except TestInProgress:
            debug("ActionMan : Error test in progress")
        except:
            debug("ActionMan : Unknown error")
    
    
    @staticmethod
    def manageQuit(action):
        assert isinstance(action, a.Quit)
        debug("ActionMan : managing Quit task")
        Client.broadcast( Bye("", Identification.PROBE_ID), toMyself = False )
        ''' Other commands to close all connections, etc '''
        Client.allMessagesSent()
        ProbeStorage.closeAllConnections()
        debug("ActionMan : All connections closed")
        ProbeStorage.addProbe(Probe(str(Identification.PROBE_ID), "localhost"))
        debug("ActionMan : readded the localhost probe")
