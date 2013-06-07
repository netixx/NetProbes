'''
Created on 7 juin 2013

@author: francois
'''
import threading
import heapq
from consts import Consts
import http.server
import socketserver
import sys

class Server():
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.actionQueue = []
        self.listener = __class__.Listener()
    
    
    def addTask(self, task):
        heapq.heappush(self.actionQueue, (task.priority, task))
        
    def getTask(self):
        return heapq.heappop(self.actionQueue);
    
    
    class Listener():
        
        def __init__(self):
            self.server = socketserver.TCPServer(("", Consts.PORT_NUMBER), __class__.RequestHandler)
            self.server.serve_forever();
            
        class RequestHandler(http.server.SimpleHTTPRequestHandler):
            
            def __init__(self, request, client_address, server_socket):
                http.server.SimpleHTTPRequestHandler(request, client_address, server_socket)

            def handle(self):
                '''
                    Handle a request on our server
                '''
                print("handle request")
                