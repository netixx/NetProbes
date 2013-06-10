'''
Created on 7 juin 2013

@author: francois
'''
from consts import Consts
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread
from queue import PriorityQueue
from actions import *

class Server(Thread):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        #the list of actions to be done
        self.actionQueue = PriorityQueue()
        self.listener = __class__.Listener(self)
        #init the thread
        Thread.__init__(self)
        self.setName("Server")
        
    
    def addTask(self, action):
        assert isinstance(action, Action)
        print(action.priority)
        self.actionQueue.put_nowait((action.priority, action))
        
    def getTask(self):
        return self.actionQueue.get()[1]
    
    def taskDone(self):
        self.actionQueue.task_done()
    
    def run(self):
        self.listener.start();

    def quit(self):
        self.listener.server_close()



    class Listener(ThreadingMixIn,HTTPServer):
        
        def __init__(self, server):
            HTTPServer.__init__(self,("", Consts.PORT_NUMBER), __class__.RequestHandler)
            self.server = server
            
        def start(self):
            self.serve_forever();

        def close(self):
            self.server_close();
            
        def addTask(self,action):
            self.server.addTask(action)
        
        class RequestHandler(SimpleHTTPRequestHandler):
            
            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

            def do_POST(self):
                '''
                    Handle a request on our server
                '''
                print("handle request")
                self.server.server.addTask(Add("127.0.0.1", "id"));
#                 SimpleHTTPRequestHandler.do_POST(self);
            def do_GET(self):
                print("Get request")

                