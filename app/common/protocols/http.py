'''
Created on 9 avr. 2014

@author: francois
'''

import urllib, logging, datetime, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread
from http.client import HTTPConnection, CannotSendRequest, HTTPException
from common.intfs.exceptions import ProbeConnectionFailed
from common.consts import Params

class Parameters(object):
    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000
    HTTP_POST_REQUEST = "POST"
    HTTP_GET_REQUEST = "GET"
    URL_RESULT_QUERY = "/results"
    URL_PROBES_QUERY = "/probes"
    URL_SRV_ID_QUERY = "/id"
    MAX_SEND_TRY = 4
    REPLY_MESSAGE_ENCODING = 'latin-1'

logger = logging.getLogger()

def createConnection(ip):
    return HTTPConnection(ip, Parameters.COMMANDER_PORT_NUMBER)

def connect(connection):
    try:
        connection.connect()
    except HTTPException as e:
        raise ProbeConnectionFailed(e)

def disconnect(connection):
    connection.close()

def getRemoteId(ip):
    try:
        connection = HTTPConnection(ip, Parameters.PORT_NUMBER);
        connection.connect()
        connection.request("GET", Parameters.URL_SRV_ID_QUERY, "", {})
        probeId = connection.getresponse().read().decode(Parameters.REPLY_MESSAGE_ENCODING)
    #     logger.logger.info("Id of probe with ip " + str(targetIp) + " is " + str(probeId))
        connection.close()
        return probeId
    except Exception as e:
        raise ProbeConnectionFailed(e)


class Sender(object):
    def send(self, connection, message):
        i = 0
        tryAgain = True
        while(tryAgain and i < Parameters.MAX_SEND_TRY):
            try :
                # serialize our message
                serializedMessage = Params.CODEC.encode(message)
                # put it in a dictionnary
                params = {Parameters.POST_MESSAGE_KEYWORD : serializedMessage}
                # transform dictionnary into string
                params = urllib.parse.urlencode(params, doseq = True, encoding = Parameters.POST_MESSAGE_ENCODING)
                # set the header as header for POST
                headers = {"Content-type": "application/x-www-form-urlencoded;charset=" + Parameters.POST_MESSAGE_ENCODING, "Accept": "text/plain"}

                connection.request("POST", "", params, headers)
                connection.getresponse()
                tryAgain = False
            except CannotSendRequest:
                # retry later
                tryAgain = True
                time.sleep(2)
            finally:
                i += 1

    def requestProbes(self, connection):
        connection.request("GET", "/probes", "", {})
        response = connection.getresponse()
        pi = response.read(int(response.getheader('content-length')))
        return Params.CODEC.decode(pi)

    def requestResults(self, connection):
        connection.request("GET", "/results", "", {})
        response = connection.getresponse()
        return response.read(int(response.getheader('content-length'))).decode()


class Listener(ThreadingMixIn, HTTPServer, Thread):

    def __init__(self, helper):
        HTTPServer.__init__(self, ("", Parameters.COMMANDER_PORT_NUMBER), __class__.RequestHandler)
        Thread.__init__(self)
        self.setName('Common listener')
        self.helper = helper

    def run(self):
        self.serve_forever()

    def close(self):
        self.shutdown()

    class RequestHandler(SimpleHTTPRequestHandler):

        def __init__(self, request, client_address, server_socket):
            SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

        def log_message(self, format, *args):
            self.server.helper.getLogger().ddebug("Process message : %s -- [%s] %s" % (self.address_string(),
                                                                                self.log_date_time_string(),
                                                                                format % args))

        def do_POST(self):
            self.server.helper.getLogger().debug("Handling a command")
            contentLength = self.headers.get("content-length")
            # read content
            args = self.rfile.read(int(contentLength))
            # convert from bytes to string
            args = str(args, Parameters.POST_MESSAGE_ENCODING)
            # parse our string to a dictionary
            args = urllib.parse.parse_qs(args, keep_blank_values = True, strict_parsing = True, encoding = Parameters.POST_MESSAGE_ENCODING)
            # get our object as string and transform it to bytes
            message = bytes(args.get(Parameters.POST_MESSAGE_KEYWORD)[0], Parameters.POST_MESSAGE_ENCODING)
            # transform our bytes into an object
            message = Params.CODEC.decode(message)

            response = self.server.helper.handleResponse(self, message)

            self._reply(response.encode(Parameters.POST_MESSAGE_ENCODING))

            self.server.helper.treatMessage(message)


        def do_GET(self):
            self.server.helper.getLogger().ddebug("Handling get Request")
            getPath = urllib.parse.urlparse(self.path).path

            if (getPath == Parameters.URL_PROBES_QUERY):
                self.server.helper.getLogger().debug("Giving the list of probes")
                message = self.server.helper.handleProbeQuery()

            elif (getPath == Parameters.URL_RESULT_QUERY):
                self.server.helper.getLogger().debug("Asked for results of tests")
                message = self.server.helper.handleResultQuery()
            else :
                message = self.server.helper.handleGet()
            # answer with your id
            self._reply(message)

        def _reply(self, message):
            if type(message) is not bytes:
                message = message.encode(Parameters.POST_MESSAGE_ENCODING)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(message))
            self.send_header("Last-Modified", str(datetime.datetime.now()))
            self.end_headers()
            self.wfile.write(message)
