'''
Created on 14 juin 2013

@author: francois
'''

from consts import Consts, Identification
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread, Event
from commanderMessages import CommanderMessage,Add
import pickle
import urllib
import datetime
import http.client
import messages as m
from client import Client
class CommanderServer(Thread):
    '''
    classdocs
    '''


    def __init__(self):
        Thread.__init__(self)

    def run(self):
        pass


    class Listener(ThreadingMixIn, HTTPServer, Thread):

        def __init__(self, server):
            HTTPServer.__init__(self, ("", Consts.PORT_NUMBER), __class__.RequestHandler)
            self.server = server
            Thread.__init__(self)

        def run(self):
            self.serve_forever();

        def close(self):
            self.server_close();

        class RequestHandler(SimpleHTTPRequestHandler):

            def __init__(self, request, client_address, server_socket):
                SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

            def do_POST(self):
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
                self.handle(message)

            def do_GET(self):
                message = "Commander server running, state your command ...".encode(Consts.POST_MESSAGE_ENCODING)
                # answer with your id
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.send_header("Content-Length", len(message))
                self.send_header("Last-Modified", str(datetime.datetime.now()))
                self.end_headers()
                self.wfile.write(message)

            
            def handle(self, message):
                assert isinstance(message, CommanderMessage)
                if( isinstance(message, Add)):
                    connection = http.client.HTTPConnection(message.getIp(), Consts.PORT_NUMBER);
                    connection.connect()
                    connection.request("GET", "", "", "")
                    probeId = connection.getresponse().read()
                    connection.close()
                    addMessage = m.Add(Identification.PROBE_ID, probeId, message.getIp())
                    Client.broadcast(addMessage)
                    
class CommanderMessage(object):
    def __init__(self):
        pass

