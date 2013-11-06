'''
Created on 14 juin 2013

@author: francois
'''

from probe.consts import Consts
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread
from common.commanderMessages import Add, Delete, Do
import calls.actions as a
import pickle
import datetime
import http.client
import calls.messages as m
from client import Client
import consts
import urllib.parse
from probes import ProbeStorage
import common.probedisp as pd
from server import Server
from queue import Queue
import copy

class CommanderServer(Thread):

    resultsQueue = Queue()

    def __init__(self):
        Thread.__init__(self)
        self.listener = CommanderServer.Listener()

    def run(self):
        self.listener.start()

    @classmethod
    def addResult(cls, result):
        cls.resultsQueue.put(result)

    @classmethod
    def getResult(cls):
        return cls.resultsQueue.get()

    class Listener(ThreadingMixIn, HTTPServer, Thread):

        def __init__(self):
            HTTPServer.__init__(self, ("", Consts.COMMANDER_PORT_NUMBER), __class__.RequestHandler)
            Thread.__init__(self)

        def run(self):
            self.serve_forever();

        def close(self):
            self.server_close();

        class RequestHandler(SimpleHTTPRequestHandler):

            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

            def do_POST(self):
                consts.debug("CommanderServer : Handling a command")
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
                consts.debug("CommanderServer : handling get Request")
                getPath = urllib.parse.urlparse(self.path).path
                if (getPath == "/probes"):
                    consts.debug("CommanderServer : Giving the probes")
                    probes = ProbeStorage.getAllProbes()
                    dprobes = []
                    for probe in probes:
                        status= []
                        status.append(pd.ProbeStatus.ADDED)
                        if probe.connected :
                            status.append(pd.ProbeStatus.CONNECTED)
                        pd.Probe(probe.getId(), probe.getIp(), pd.statusFactory(status))

                    message = pickle.dumps(dprobes)
                elif (getPath == "/results"):
                    consts.debug("CommanderServer : Asked for results")
                    # blocant!
                    message = CommanderServer.getResult().encode(Consts.POST_MESSAGE_ENCODING)
                    consts.debug("CommanderServer : Giving the results")
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
                consts.debug("CommanderServer : handling constructed message")
                if(isinstance(message, Add)):
                    consts.debug("CommanderServer : trying to add probe with ip " + str(message.targetIp))
                    connection = http.client.HTTPConnection(message.targetIp, Consts.PORT_NUMBER);
                    connection.connect()
                    connection.request("GET", "", "", {})
                    probeId = connection.getresponse().read().decode()
                    consts.debug("CommanderServer : Id of probe with ip " + str(message.targetIp) + " is " + str(probeId))
                    connection.close()
                    
                    addMessage = m.Add("", probeId, message.targetIp)
                    selfAddMessage = copy.deepcopy(addMessage)
                    selfAddMessage.doHello = True
                    Server.treatMessage(selfAddMessage)

                    #addMessage = m.Add(Identification.PROBE_ID, probeId, message.targetIp, hello=True)
                    Client.broadcast(addMessage)

                    
                if(isinstance(message,Delete)):
                    consts.debug("CommanderServer : trying to delete probe with ID " + str(message.targetId))
                    byeMessage = m.Bye(message.targetId, message.targetId)
                    Client.send(byeMessage)

                if(isinstance(message, Do)):
                    consts.debug("CommanderServer : trying to do a test : " + message.test)
                    Server.addTask(a.Do(message.test, message.testOptions))



