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
from queue import PriorityQueue
from calls.messages import Hello, Bye, AddToOverlay
from consts import Identification
from inout.client import Client
from managers.probes import ProbeStorage
import calls.actions as a
from .tests import TestResponder, TestManager
from interfaces.excs import TestError, ActionError, \
    NoSuchProbe, ProbeConnectionException, ToManyTestsInProgress

from ipaddress import ip_network

class ActionMan(Thread):

    '''Links Action classes to (static) methods'''
    mapping = { "Add" : "manageAdd",
                "Remove" : "manageRemove",
                "Transfer" : "manageTransfer",
                "Do" : "manageDo",
                "Quit" : "manageQuit",
                "Prepare" : "managePrepare",
                "UpdateProbes" : "manageUpdateProbes"
              }

    logger = logging.getLogger()
    # the list of actions to be done
    actionQueue = PriorityQueue()

    def __init__(self):
        #init the thread
        Thread.__init__(self)
        self.setName("ActionManager")
        self.stop = False
    
    @classmethod
    def addTask(cls, action):
        cls.logger.debug("Queued new Action %s", action.__class__.__name__)
        assert isinstance(action, a.Action)
        cls.actionQueue.put((action.priority, action))

    @classmethod
    def getTask(cls):
        cls.logger.ddebug("Polled new action from queue")
        result = cls.actionQueue.get(True)[1]
        return result

    @classmethod
    def taskDone(cls):
        cls.actionQueue.task_done()

    @classmethod
    def _terminate(cls):
        cls.actionQueue.put((100, None))
        cls.actionQueue.join()

    def run(self):
        while not self.stop:
            task = self.getTask()
            try:
                if task is None:
                    self.stop = True
                    return
                getattr(self.__class__, self.mapping.get(task.__class__.__name__))(task)
            except ActionError:
                # TODO: convert to warning ??
                self.logger.error("Action execution failed", exc_info = 1)
            except:
                self.logger.error("Unexpected error occurred while treating action", exc_info = 1)
            finally:
                self.taskDone()

    def quit(self):
        self.logger.info("Stopping ActionMan !")
        self.stop = True
        self._terminate()

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
        cls.logger.info("Added probe %s, id %s to known probes", action.getIpSonde(), action.getIdSonde())

    @classmethod
    def manageAddPrefix(cls, action):
        assert isinstance(action , a.AddPrefix)
        try:
            net = ip_network(action.getPrefix(), strict = False)
            hosts = net.hosts() if net.num_addresses > 1 else [net.network_address]
            for host in hosts:
                print(host)
                try:
                    h = str(host)
                    if not ProbeStorage.isKnownIp(h):
                        Client.send(AddToOverlay(Identification.PROBE_ID, h))
                except ProbeConnectionException as e:
                    cls.logger.info("Adding probe failed %s : %s", h, e)
                except Exception as e:
                    cls.logger.warning("Error while adding probe %s : %s", h, e)
        except ValueError:
            cls.logger.warning("Wrong prefix given %s", action.getPrefix())

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
            cls.logger.info("Removing %s from known probes", action.getIdSonde())
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
        cls.logger.info("Request for test %s", action.getTestName())
        try:
            testId = TestManager.startTest(action.getTestName(), action.getTestOptions(), action.getResultCallback(), action.getErrorCallback())
            action.setTestId(testId)
        except ToManyTestsInProgress as e:
            cls.logger.info("Test %s not started : %s", action.getTestName(), e)
            action.getErrorCallback()(action.getTestName(), e)
        except TestError as e:
            action.getErrorCallback()(action.getTestName(), e.getReason())
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
