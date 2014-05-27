"""
Manages actions from the stack of actions to be performed
This actually performs the Action

The ActionMan is an independent thread waiting for actions
 to be pushed to the stack.

@author: Gaspard FEREY
"""
__all__ = ['ActionMan']

from threading import Thread
import logging
from queue import PriorityQueue
from ipaddress import ip_network

from calls.messages import Hello, Bye, AddToOverlay, Add
from consts import Identification
from inout.client import Client
from managers.probes import ProbeStorage
import calls.actions as a
from .probetests import TestResponder, TestManager
from interfaces.excs import TestError, ActionError, \
    NoSuchProbe, ToManyTestsInProgress, ProbeConnectionException
from .scheduler import Scheduler


class ActionMan(Thread):
    """Links Action classes to (class) methods"""
    MAP_PREFIX = 'manage'

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
        """Adds a task to the queue of tasks to perform
        :param action: Action instance to add

        """
        cls.logger.debug("Queued new Action %s", action.__class__.__name__)
        assert isinstance(action, a.Action)
        cls.actionQueue.put((action.priority, action))

    @classmethod
    def getTask(cls):
        """Gets a task from the queue, blocking until a task is available"""
        cls.logger.ddebug("Polled new action from queue")
        result = cls.actionQueue.get(True)[1]
        return result

    @classmethod
    def taskDone(cls):
        """Indicate to the queue that the task is over"""
        cls.actionQueue.task_done()

    @classmethod
    def _terminate(cls):
        cls.actionQueue.put((100000, None))
        cls.actionQueue.join()

    def run(self):
        """Start treating tasks"""
        while not self.stop:
            try:
                task = self.getTask()
                if task is None:
                    self.stop = True
                    return
                getattr(self.__class__, self.MAP_PREFIX + task.__class__.__name__)(task)
            except ActionError:
                # TODO: convert to warning ??
                self.logger.error("Action execution failed", exc_info = 1)
            except:
                self.logger.error("Unexpected error occurred while treating action", exc_info = 1)
            finally:
                self.taskDone()

    def quit(self):
        """Terminate the thread : read all remaining Action and end the queue"""
        self.logger.info("Stopping ActionMan !")
        self._terminate()

    @classmethod
    def manageAdd(cls, action):
        """Add a probe to the DHT
        :param action: Add action containing the probe to add
        """
        assert isinstance(action, a.Add)
        cls.logger.debug("Managing Add task")
        #add the probe to the local DHT
        ProbeStorage.addProbe(ProbeStorage.newProbe(action.getIdSonde(), action.getIpSonde()))
        if action.hello is not None:
            # tell the new probe about all other probe
            Client.send(action.hello)
        cls.logger.info("Added probe %s, id %s to known probes", action.getIpSonde(), action.getIdSonde())


    @classmethod
    def manageAddToOverlay(cls, action):
        assert isinstance(action, a.AddToOverlay)
        cls.logger.ddebug("Add probe to overlay")
        try:
            probeId = Client.getRemoteId(action.probeIp)
            cls.logger.info("Adding probe %s at %s to overlay", probeId, action.probeIp)
            addMessage = Add(Identification.PROBE_ID, probeId, action.probeIp)
            #use action directly because of timing issues
            selfAddAction = a.Add(action.probeIp, probeId, Hello(probeId,
                                                                 list(ProbeStorage.getAllOtherProbes()),
                                                                 Identification.PROBE_ID,
                                                                 echo = Identification.PROBE_ID if action.mergeOverlays else None)
            )
            # selfAddMessage = copy.deepcopy(addMessage)
            # selfAddAction.hello = Hello(probeId,
            #                              list(ProbeStorage.getAllOtherProbes()),
            #                              Identification.PROBE_ID,
            #                              echo = Identification.PROBE_ID if action.mergeOverlays else None)

            # Do broadcast before adding the probe so that it doesn't receive unnecessary message
            # addMessage = m.Add(Identification.PROBE_ID, probeId, message.targetIp, hello=True)
            # print(ProbeStorage.getIdAllOtherProbes())
            Client.broadcast(addMessage)
            #treat message after so that the new guy does not receive bogus add message
            #treat the add for this addToOverlay before any other AddToOverlay
            # import calls.messagetoaction as MTA
            cls.addTask(selfAddAction)
            #try to fix adding host too quickly
            Scheduler.addToOverlay()
            cls.logger.debug("Probe %s added to overlay", probeId)
        except ProbeConnectionException as e:
            cls.logger.warning("Adding probe failed %s : %s", action.probeIp, e)


    @classmethod
    def manageAddPrefix(cls, action):
        """Add a prefix to the DHT. A prefix is a set of addresses
        :param action: AddPrefix action
        """
        assert isinstance(action, a.AddPrefix)
        try:
            net = ip_network(action.getPrefix(), strict = False)
            hosts = net.hosts() if net.num_addresses > 1 else [net.network_address]
            for host in hosts:
                try:
                    h = str(host)
                    if not ProbeStorage.isKnownIp(h):
                        Client.send(AddToOverlay(Identification.PROBE_ID, h))
                except Exception as e:
                    cls.logger.warning("Error while adding probe %s : %s", h, e)
        except ValueError:
            cls.logger.warning("Wrong prefix given %s", action.getPrefix())

    @classmethod
    def manageUpdateProbes(cls, action):
        """Update your list of probes with this set of probes
        :param action: UpdateProbes action instance
        """
        assert isinstance(action, a.UpdateProbes)
        cls.logger.info("Joined overlay size %s", len(action.getProbeList()))
        if action.echo is not None:
            Client.send(Hello(action.echo, list(ProbeStorage.getAllOtherProbes()), Identification.PROBE_ID))
            cls.logger.info("Sent echo to %s", action.echo)
        for probe in action.getProbeList():
            # don't re-add ourselves to the local DHT
            if probe.getId() != Identification.PROBE_ID:
                ProbeStorage.addProbe(ProbeStorage.newProbe(probe.getId(), probe.getIp()))

    @classmethod
    def manageRemove(cls, action):
        """Remove a probe from the currently known probes
        :param action: Remove action describing the probe to remove"""
        assert isinstance(action, a.Remove)
        cls.logger.debug("Managing Remove task")
        try:
            cls.logger.info("Removing %s from known probes", action.getIdSonde())
            # remove probe from DHT
            ProbeStorage.delProbeById(action.getIdSonde())
        except NoSuchProbe:
            cls.logger.warning("Probe not found in hash table")

    @classmethod
    def manageDo(cls, action):
        """Initiate a new test
        A new thread is created for this test by the TestManager so
        this method does not block the ActionManager
        :param action: Do action describing the test to perform
        """
        assert isinstance(action, a.Do)
        cls.logger.debug("Managing Do task")
        cls.logger.info("Request for test %s", action.getTestName())
        try:
            testId = TestManager.startTest(action.getTestName(), action.getTestOptions(), action.getResultCallback(),
                                           action.getErrorCallback())
            action.setTestId(testId)
        except ToManyTestsInProgress as e:
            cls.logger.info("Test %s not started : %s", action.getTestName(), e)
            action.getErrorCallback()(action.getTestName(), e)
        except TestError as e:
            action.getErrorCallback()(action.getTestName(), e.getReason())
            raise e

    @classmethod
    def managePrepare(cls, action):
        """Respond to a new test
        A new thread is created by the TestResponder,
        a probe can respond to multiple tests at once
        :param action: Prepare action describing the test to respond to
        """
        assert (isinstance(action, a.Prepare))
        cls.logger.info("Prepare for test (%s-%s)", action.getTestName(), action.getTestId())
        try:
            TestResponder.startTest(action.getTestId(), action.getTestName(), action.getSourceId(),
                                    action.getTestOptions())
        except TestError:
            cls.logger.error("Error while preparing for test %s-%s", action.getTestName(), action.getTestId(),
                             exc_info = 1)

    @classmethod
    def manageBroadcast(cls, action):
        assert isinstance(action, a.Broadcast)
        Client.send(action.broadcast)

    @classmethod
    def manageQuit(cls, action):
        """Quit the overlay nicely
        Tells everyone about this
        :param action: Quit action
        """
        assert isinstance(action, a.Quit)
        cls.logger.debug("Managing Quit task")
        cls.logger.info("Exiting the overlay")
        try:
            Client.broadcast(Bye("", Identification.PROBE_ID), toMyself = False)
        except ProbeConnectionException as e:
            cls.logger.warning("Could not sent Bye message %s", e)
        # Other commands to close all connections, etc
        Client.allMessagesSent()
        ProbeStorage.clearAllProbes()
        cls.logger.info("All probes cleared, all connections closed.")
        ProbeStorage.addSelfProbe()
        cls.logger.info("Re-added the localhost probe, ready to proceed again")

    @classmethod
    def getStatus(cls):
        """Return the current status of the probe"""
        # TODO: implement
        return "ok"
