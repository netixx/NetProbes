'''
Server that listens for commands sent by the commander package
Adds action directly to the server action queue
@see: commander.main

@author: francois
'''
__all__ = ['CommanderServer']

import copy, logging, http.client, pickle, datetime, urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from queue import Queue
from socketserver import ThreadingMixIn
from threading import Thread

from common.commanderMessages import Add, Delete, Do
import common.probedisp as pd
import common.consts as cconsts
import calls.actions as a
import calls.messages as m
from managers.probes import ProbeStorage
from consts import Consts, Identification, Urls
from .client import Client
from .server import Server

class CommanderServer(Thread):
    """Results are pushed to the results queue.
    When the become available, the Listener pushes the
    results to the commander instance

    """
    resultsQueue = Queue()
    logger = logging.getLogger()

    def __init__(self):
        Thread.__init__(self)
        self.setName("CommanderServer")
        self.listener = CommanderServer.Listener()

    def run(self):
        self.logger.info("Starting the Commander Server")
        self.listener.start()

    @classmethod
    def addResult(cls, result):
        cls.resultsQueue.put(result)

    @classmethod
    def addError(cls, error):
        cls.resultsQueue.put("E: " + error)

    @classmethod
    def getResult(cls):
        return cls.resultsQueue.get()

    class Listener(ThreadingMixIn, HTTPServer, Thread):

        def __init__(self):
            HTTPServer.__init__(self, ("", Consts.COMMANDER_PORT_NUMBER), __class__.RequestHandler)
            Thread.__init__(self)
            self.setName("CommanderServer")

        def run(self):
            self.serve_forever();

        def close(self):
            self.server_close();

        class RequestHandler(SimpleHTTPRequestHandler):

            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

            def log_message(self, format, *args):
                CommanderServer.logger.debug("Process message : %s -- [%s] %s" % (self.address_string(),
                                                                                    self.log_date_time_string(),
                                                                                    format % args))

            def do_POST(self):
                CommanderServer.logger.debug("Handling a command")
                contentLength = self.headers.get("content-length")
                # read content
                args = self.rfile.read(int(contentLength))
                # convert from bytes to string
                args = str(args, Consts.POST_MESSAGE_ENCODING)
                # parse our string to a dictionary
                args = urllib.parse.parse_qs(args, keep_blank_values=True, strict_parsing=True, encoding=Consts.POST_MESSAGE_ENCODING)
                # get our object as string and transform it to bytes
                message = bytes(args.get(Consts.POST_MESSAGE_KEYWORD)[0], Consts.POST_MESSAGE_ENCODING)
                # transform our bytes into an object
                message = pickle.loads(message)
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len("ok"))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write("ok".encode())
                self.handleMessage(message)

            def do_GET(self):
                CommanderServer.logger.debug("Handling get Request")
                getPath = urllib.parse.urlparse(self.path).path
                if (getPath == cconsts.CmdSrvUrls.CMDSRV_PROBES_QUERY):
                    CommanderServer.logger.debug("Giving the list of probes")
                    probes = ProbeStorage.getAllProbes()
                    dprobes = []
                    for probe in probes:
                        status= []
                        if probe.getId() == Identification.PROBE_ID:
                            status.append(pd.ProbeStatus.LOCAL)
                        status.append(pd.ProbeStatus.ADDED)
                        if probe.connected :
                            status.append(pd.ProbeStatus.CONNECTED)
                        dprobes.append(pd.Probe(probe.getId(), probe.getIp(), pd.statusFactory(status)))

                    message = pickle.dumps(dprobes)
                elif (getPath == cconsts.CmdSrvUrls.CMDSRV_RESULT_QUERY):
                    CommanderServer.logger.debug("Asked for results of tests")
                    # blocant!
                    message = CommanderServer.getResult().encode(Consts.POST_MESSAGE_ENCODING)
                    CommanderServer.logger.debug("Giving the results")
                else :
                    message = "Commander server running, state your command ...".encode(Consts.POST_MESSAGE_ENCODING)
                # answer with your id
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len(message))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write(message)

            
            def handleMessage(self, message):
                CommanderServer.logger.debug("Handling constructed message")
                if(isinstance(message, Add)):
                    CommanderServer.logger.info("Trying to add probe with ip " + str(message.targetIp))
                    probeId = self.getRemoteId(message.targetIp)

                    addMessage = m.Add("", probeId, message.targetIp)
                    selfAddMessage = copy.deepcopy(addMessage)
                    selfAddMessage.doHello = True
                    # Do broadcast before adding the probe so that it doesn't receive unnecessary message
                    # addMessage = m.Add(Identification.PROBE_ID, probeId, message.targetIp, hello=True)
                    Client.broadcast(addMessage)

                    Server.treatMessage(selfAddMessage)
                if(isinstance(message,Delete)):
                    CommanderServer.logger.info("Trying to delete probe with ID %s", message.targetId)
                    byeMessage = m.Bye(message.targetId, message.targetId)
                    Client.send(byeMessage)

                if(isinstance(message, Do)):
                    CommanderServer.logger.info("Trying to do a test : %s", message.test)
                    Server.addTask(a.Do(message.test, message.testOptions))


            def getRemoteId(self, targetIp):
                connection = http.client.HTTPConnection(targetIp, Consts.PORT_NUMBER);
                connection.connect()
                connection.request("GET", Urls.SRV_ID_QUERY, "", {})
                probeId = connection.getresponse().read().decode()
                CommanderServer.logger.info("Id of probe with ip " + str(targetIp) + " is " + str(probeId))
                connection.close()
                return probeId
