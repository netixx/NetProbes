'''
Created on 7 juin 2013

@author: francois
'''
import consts
from consts import Consts, Identification
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread, Event
from messages import Message
import messagetoaction as MTA
from probes import Probe, ProbeStorage
import pickle
import urllib
from actions import Action
from queue import PriorityQueue
import datetime
'''
    Server thread listens on the given port to a POST request containing a serialisation of a Message object
    It then transforms this Message into a corresponding Action that is added to the Queue of actions that the server must execute
'''
class Server(Thread):
    
    #the list of actions to be done
    actionQueue = PriorityQueue()
    
    def __init__(self):
        self.listener = __class__.Listener(self)
        #init the thread
        Thread.__init__(self)
        self.setName("Server")
        self.isUp = Event()
        ProbeStorage.addProbe(Probe(Identification.PROBE_ID, "localhost"))
    
    
    @classmethod
    def addTask(cls, action):
        consts.debug("Server : Queued new Action " + action.__class__.__name__)
        assert isinstance(action, Action)
        cls.actionQueue.put((action.priority, action))
    
    @classmethod
    def getTask(cls):
        consts.debug("Server : Polled new action from queue")
        result = cls.actionQueue.get(True)[1]
        cls.actionQueue.task_done()
        return result
    
    
    def run(self):
        consts.debug("Server : starting server")
        self.listener.start()
        self.isUp.set()

    def quit(self):
        consts.debug("Server : closing server")
        self.listener.close()
        self.actionQueue.join()

    def treatMessage(self, message):
        consts.debug("Server : treating message " + message.__class__.__name__)
        assert isinstance(message, Message)
        Server.addTask(MTA.toAction(message))

    class Listener(ThreadingMixIn,HTTPServer, Thread):
        
        def __init__(self, server):
            HTTPServer.__init__(self,("", Consts.PORT_NUMBER), __class__.RequestHandler)
            self.server = server
            Thread.__init__(self)
            
        def run(self):
            self.serve_forever();

        def close(self):
            self.server_close();
            
        def addTask(self,action):
            Server.addTask(action)
        
        class RequestHandler(SimpleHTTPRequestHandler):
            
            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)
            
            def do_POST(self):
                consts.debug("Server : handling POST request from another probe")
                contentLength = self.headers.get("content-length")
                #read content
                args = self.rfile.read(int(contentLength))
                #convert from bytes to string
                args = str(args,Consts.POST_MESSAGE_ENCODING)
                # parse our string to a dictionary
                args = urllib.parse.parse_qs(args, keep_blank_values = True, strict_parsing=True, encoding=Consts.POST_MESSAGE_ENCODING)
                # get our object as string and transform it to bytes
                message = bytes(args.get(Consts.POST_MESSAGE_KEYWORD)[0], Consts.POST_MESSAGE_ENCODING)
                # transform our bytes into an object
                message = pickle.loads(message)
                # give the message to our server so that it is treated
                self.server.server.treatMessage(message)
            
            def do_GET(self):
                consts.debug("Server : handling get request, giving my ID : " + str(Identification.PROBE_ID))
                myId = str(Identification.PROBE_ID).encode(Consts.POST_MESSAGE_ENCODING)
                #answer with your id
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len(myId))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write(myId)
