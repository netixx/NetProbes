'''
Created on 7 juin 2013

@author: francois
'''
import heapq
from consts import Consts
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread

class Server(Thread):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.actionQueue = []
        self.listener = __class__.Listener()
        Thread.__init__(self)
        self.setName("Server")
    
    def addTask(self, task):
        heapq.heappush(self.actionQueue, (task.priority, task))
        
    def getTask(self):
        return heapq.heappop(self.actionQueue);
    
    def run(self):
        self.listener.start();

    def quit(self):
        self.listener.server_close()
        
    class Listener(ThreadingMixIn,HTTPServer):
        
        def __init__(self):
            HTTPServer.__init__(self,("", Consts.PORT_NUMBER), __class__.RequestHandler)
        
        def start(self):
            self.serve_forever();

        def close(self):
            self.server_close();
        
        class RequestHandler(SimpleHTTPRequestHandler):
            
            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

            def do_POST(self):
                '''
                    Handle a request on our server
                '''
                print("handle request")
#                 SimpleHTTPRequestHandler.do_POST(self);
                