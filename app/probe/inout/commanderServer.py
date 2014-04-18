"""
Server that listens for commands sent by the commander package
Adds action directly to the server action queue

@author: francois

"""
__all__ = ['CommanderServer', 'Parameters']

import logging
from queue import Queue
from threading import Thread

from common.commanderMessages import Add, Delete, Do
import common.probedisp as pd
import calls.messages as m
from managers.probes import ProbeStorage
from consts import Identification
from .client import Client
from .server import Server
import common.consts as cconsts


class CommanderServer(Thread):
    """Results are pushed to the results queue.
    When the become available, the Listener pushes the
    results to the commander instance

    """
    resultsQueue = Queue()
    logger = logging.getLogger()

    def __init__(self):
        Thread.__init__(self)
        self.helper = self.Helper(self)
        self.setName("CommanderServer")
        self.listener = cconsts.Params.PROTOCOL.Listener(self.helper)

    def run(self):
        """Start listening"""
        self.logger.info("Starting the Commander Server")
        self.listener.start()

    def quit(self):
        """Stop listening"""
        self.logger.info("Closing Commander Server")
        self.listener.close()

    @classmethod
    def addResult(cls, testName, result):
        """Add a result or message
        :param testName: name of the test to which the result belong to
        :param result: result of the test
        """
        cls.resultsQueue.put("%s :\n%s\n" % (testName, result))

    @classmethod
    def addError(cls, testName, error):
        """Add an error, differs from addResult by prepending "Err: "
        :param testName: name of the to which the error belongs to
        :param error: the error for the test
        """
        cls.resultsQueue.put("Err: %s :\n%s\n" % (testName, error))

    @classmethod
    def getResult(cls):
        """Blocking method returning the first result in the queue"""
        return cls.resultsQueue.get()

    class Helper(object):
        """Helper object to pass to the cParams.PROTOCOL.Listener object
        TODO: consider refactoring"""
        def __init__(self, server):
            self.server = server

        def treatMessage(self, message):
            """Treat the message, doing action which are required
            :param message: The Message instance which was received by the protocol
            """
            self.getLogger().ddebug("Handling constructed message")
            if isinstance(message, Add):
                msg = m.AddToOverlay(message.targetId, message.targetIp)
                Server.treatMessage(msg)
            elif isinstance(message, Delete):
                self.getLogger().info("Trying to delete probe with ID %s", message.targetId)
                byeMessage = m.Bye(message.targetId, message.targetId)
                Client.send(byeMessage)

            elif isinstance(message, Do):
                self.getLogger().info("Trying to do a test : %s", message.test)
                msg = m.Do(message.targetId, message.test, message.testOptions)
                if msg.targetId == Identification.PROBE_ID:
                    msg.resultCallback = CommanderServer.addResult
                    msg.errorCallback = CommanderServer.addError
                Server.treatMessage(msg)

        @classmethod
        def handleProbeQuery(cls):
            """Handle request to give the probes"""
            probes = ProbeStorage.getAllProbes()
            dprobes = []
            for probe in probes:
                status = []
                if probe.getId() == Identification.PROBE_ID:
                    status.append(pd.ProbeStatus.LOCAL)
                status.append(pd.ProbeStatus.ADDED)
                if probe.connected:
                    status.append(pd.ProbeStatus.CONNECTED)
                dprobes.append(pd.Probe(probe.getId(),
                                        probe.getIp(),
                                        pd.statusFactory(status)))

            return cconsts.Params.CODEC.encode(dprobes)

        def handleResultQuery(self):
            """Handle query for the result of a test"""
            # blocking!
            message = self.server.getResult()
            self.getLogger().debug("Giving the results")
            return message

        def handleGet(self):
            """Handle a simple get query (does nothing but reply)"""
            return "Commander server running, state your command ..."


        def handleResponse(self, response, message):
            """Handle response to a query to validate that it was received
            :param response: the response object
            :param message: the message that was received
            TODO: remove response
            """
            return "ok"

        def getLogger(self):
            """Return the CommanderServer logger object"""
            return self.server.logger

        def getId(self):
            """Returns the ID of this probe"""
            return Identification.PROBE_ID