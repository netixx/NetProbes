'''
Created on 7 juin 2013

@author: francois
'''
from consts import Consts
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread,Event,RLock
from queue import PriorityQueue
from actions import *
from messages import Message
import messagetoaction as MTA
from probes import Probe
import pickle
import urllib


'''
    Server thread listens on the given port to a POST request containing a serialisation of a Message object
    It then transforms this Message into a corresponding Action that is aded to the Queue of actions that the server must execute
'''
class Server(Thread):

    def __init__(self):
        #the list of actions to be done
        self.actionQueue = PriorityQueue()
        self.listener = __class__.Listener(self)
        #init the thread
        Thread.__init__(self)
        self.setName("Server")
        self.isUp = Event()

    def addTask(self, action):
        assert isinstance(action, Action)
        self.actionQueue.put_nowait((action.priority, action))
        
    def getTask(self):
        return self.actionQueue.get()[1]
    
    def taskDone(self):
        self.actionQueue.task_done()
    
    def run(self):
        self.listener.start()
        self.isUp.set()

    def quit(self):
        self.listener.close()

    def treatMessage(self, message):
        assert isinstance(message, Message)
        self.addTask(MTA.toAction(message))

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
            self.server.addTask(action)
        
        class RequestHandler(SimpleHTTPRequestHandler):
            
            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)
            
            def do_POST(self):
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
