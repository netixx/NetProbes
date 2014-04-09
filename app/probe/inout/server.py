'''
Server that listens to probe messages

@author: francois
'''
__all__ = ['Server']

from .client import Client
from calls.actions import Action
from calls.messages import Message, TesterMessage, TesteeAnswer, BroadCast, Hello, \
    TestMessage
import calls.messagetoaction as MTA
from consts import Consts, Identification, Urls
from managers.probes import ProbeStorage
from managers.tests import TestManager, TestResponder
from queue import PriorityQueue
from socketserver import ThreadingMixIn
from threading import Thread, Event
from http.server import HTTPServer, SimpleHTTPRequestHandler
import datetime, logging, pickle, urllib

class Server(Thread):
    '''
    Server thread listens on the given port to a POST request containing
    a serialization of a Message object
    It then transforms this Message into a corresponding Action
    that is added to the Queue of actions that the server must execute

    It also listens to get request an replies its id to whoever asks it!
    
    '''

    #the list of actions to be done
    actionQueue = PriorityQueue()
    logger = logging.getLogger()
    
    def __init__(self):
        self.listener = __class__.Listener(self)
        #init the thread
        Thread.__init__(self)
        self.setName("Server")
        self.isUp = Event()
        ProbeStorage.addSelfProbe()
    
    def run(self):
        self.logger.info("Starting Server")
        self.listener.start()
        self.isUp.set()

    @classmethod
    def addTask(cls, action):
        cls.logger.debug("Queued new Action %s", action.__class__.__name__)
        assert isinstance(action, Action)
        cls.actionQueue.put((action.priority, action))
    
    @classmethod
    def getTask(cls):
        cls.logger.debug("Polled new action from queue")
        result = cls.actionQueue.get(True)[1]
        return result
    
    @classmethod
    def taskDone(cls):
        cls.actionQueue.task_done()
        
    @classmethod
    def allTaskDone(cls):
        cls.actionQueue.join()
    
    def quit(self):
        self.logger.info("Closing Server")
        self.listener.close()
        self.actionQueue.join()

    @classmethod
    def treatMessage(cls, message):
        '''Handles the receptions of a Message (called by the listener)
        For regular actions, addTask is called after translation of the message
        For TesterMessages and TesteeMessages, treatTestMessage is called

        '''
        cls.logger.debug("Treating message %s", message.__class__.__name__)
        assert isinstance(message, Message)
        if isinstance(message, TestMessage):
            cls.treatTestMessage(message)
        elif isinstance(message, BroadCast):
            cls.logger.debug("Handling Broadcast")
            Server.addTask(MTA.toAction(message.getMessage()))
            Client.broadcast(message)
        else:
            Server.addTask(MTA.toAction(message))

    @classmethod
    def treatTestMessage(cls, message):
        cls.logger.debug("Handling Tester or Testee message")
        assert isinstance(message, TestMessage)
        # if probe is in test mode, give the message right to the TestManager!
        if (isinstance(message, TesteeAnswer)):
            cls.logger.debug("Handling TesteeAnswer")
            TestManager.handleMessage(message)
        elif (isinstance(message, TesterMessage)):
            cls.logger.debug("Handling TesterMessage")
            TestResponder.handleMessage(message)
        else:
            Server.addTask(MTA.toAction(message))



    class Listener(ThreadingMixIn,HTTPServer, Thread):
        '''
        Threaded listener that processes a request on the server

        '''
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
            '''
            Handler that does the actual work

            '''
            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)
            
            def log_message(self, format, *args):
                Server.logger.debug("Process message : %s -- [%s] %s" % (self.address_string(),
                                                                                    self.log_date_time_string(),
                                                                                    format % args))

            def do_POST(self):
                Server.logger.debug("Handling POST request from another probe")
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

                if (isinstance(message, Hello)):
                    message.setRemoteIp(self.client_address[0])

                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len("ok"))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write("ok".encode())

                # give the message to our server so that it is treated
                self.server.server.treatMessage(message)
            
            def do_GET(self):
                query = urllib.parse.urlparse(self.path).path
                if query == Urls.SRV_ID_QUERY:
                    self.giveId()
                elif query == Urls.SRV_STATUS_QUERY:
                    self.giveStatus()
                else:
                    self.giveId()

            def giveId(self):
                Server.logger.debug("Server : handling get request, giving my ID : %s", Identification.PROBE_ID)
                myId = str(Identification.PROBE_ID).encode(Consts.POST_MESSAGE_ENCODING)
                #answer with your id
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len(myId))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write(myId)

            def giveStatus(self):
                from managers.actions import ActionMan
#                 Server.logger.debug("Server : handling get request, giving my ID : " + str(Identification.PROBE_ID))
                status = str(ActionMan.getStatus()).encode(Consts.POST_MESSAGE_ENCODING)
                # answer with your id
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len(status))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write(status)
