'''
Server that listens for commands sent by the commander package
Adds action directly to the server action queue
@see: commander.main

@author: francois

'''
__all__ = ['CommanderServer']

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


class Parameters(object):
    COMMANDER_PORT_NUMBER = 6000
    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    REPLY_MESSAGE_ENCODING = 'latin-1'
    HTTP_POST_REQUEST = "POST"
    HTTP_GET_REQUEST = "GET"
    URL_SRV_ID_QUERY = "/id"


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
        self.logger.info("Starting the Commander Server")
        self.listener.start()

    def quit(self):
        self.listener.close()

    @classmethod
    def addResult(cls, testName, result):
        cls.resultsQueue.put("%s : %s" % (testName, result))

    @classmethod
    def addError(cls, testName, error):
        cls.resultsQueue.put("E: %s : %s" % (testName, error))

    @classmethod
    def getResult(cls):
        return cls.resultsQueue.get()

    class Helper(object):
        def __init__(self, server):
            self.server = server

        def treatMessage(self, message):
            self.getLogger().ddebug("Handling constructed message")
            if (isinstance(message, Add)):
                msg = m.AddToOverlay(message.targetId, message.targetIp)
                Server.treatMessage(msg)
            elif (isinstance(message, Delete)):
                self.getLogger().info("Trying to delete probe with ID %s", message.targetId)
                byeMessage = m.Bye(message.targetId, message.targetId)
                Client.send(byeMessage)

            elif (isinstance(message, Do)):
                self.getLogger().info("Trying to do a test : %s", message.test)
                msg = m.Do(message.targetId, message.test, message.testOptions)
                if msg.targetId == Identification.PROBE_ID:
                    msg.resultCallback = CommanderServer.addResult
                    msg.errorCallback = CommanderServer.addError
                Server.treatMessage(msg)

        def handleProbeQuery(self):
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
            # blocant!
            message = self.server.getResult()
            self.getLogger().debug("Giving the results")
            return message

        def handleGet(self):
            return "Commander server running, state your command ..."


        def handleResponse(self, response, message):
            return "ok"

        def getLogger(self):
            return self.server.logger
