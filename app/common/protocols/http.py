"""HTTP protocol implementation based on the http.* python modules
Uses http POST and GET request to send data

@author: francois
"""

import datetime
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from threading import Thread
from http.client import HTTPConnection, CannotSendRequest, HTTPException
import urllib

from common.intfs.exceptions import ProbeConnectionFailed
from common.consts import Params


class Parameters(object):
    """Parameters for this protocol"""
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000
    HTTP_POST_REQUEST = "POST"
    HTTP_GET_REQUEST = "GET"
    URL_RESULT_QUERY = "/results"
    URL_PROBES_QUERY = "/probes"
    URL_ID_QUERY = "/id"
    MAX_SEND_TRY = 4
    REPLY_MESSAGE_ENCODING = 'latin-1'


def createConnection(ip):
    """Create HTTP connection object for this ip address
    :param ip : ip to connect to
    """
    return HTTPConnection(ip, Parameters.COMMANDER_PORT_NUMBER)


def connect(connection):
    """Connection given http connection
    :param connection : http connection to call connect on
    """
    try:
        connection.connect()
    except HTTPException as e:
        raise ProbeConnectionFailed(e)


def disconnect(connection):
    """Close given connection
    :param connection : http connection to close"""
    connection.close()


def getRemoteId(ip):
    """Send a GET request to given IP and return its id
    :param ip : ip to send the request to
    """
    try:
        connection = HTTPConnection(ip, Parameters.COMMANDER_PORT_NUMBER)
        connection.connect()
        connection.request(Parameters.HTTP_GET_REQUEST, Parameters.URL_ID_QUERY, "", {})
        probeId = connection.getresponse().read().decode(Parameters.REPLY_MESSAGE_ENCODING)
        #     logger.logger.info("Id of probe with ip " + str(targetIp) + " is " + str(probeId))
        connection.close()
        return probeId
    except Exception as e:
        raise ProbeConnectionFailed(e)


class Sender(object):
    """HTTP request maker
    Uses http.client request method to create outgoing requests
    """

    @staticmethod
    def send(connection, message):
        """Send the message via http on given connection
        :param message: message to send
        :param connection: connection to use to send the message
        """
        i = 0
        tryAgain = True
        while tryAgain and i < Parameters.MAX_SEND_TRY:
            try:
                # serialize our message
                serializedMessage = Params.CODEC.encode(message)
                # put it in a dictionary
                params = {Parameters.POST_MESSAGE_KEYWORD: serializedMessage}
                # transform dictionary into string
                params = urllib.parse.urlencode(params, doseq = True, encoding = Parameters.POST_MESSAGE_ENCODING)
                # set the header as header for POST
                headers = {
                    "Content-type": "application/x-www-form-urlencoded;charset=" + Parameters.POST_MESSAGE_ENCODING,
                    "Accept": "text/plain"}

                connection.request(Parameters.HTTP_POST_REQUEST, "", params, headers)
                connection.getresponse()
                tryAgain = False
            except CannotSendRequest:
                # retry later
                tryAgain = True
                time.sleep(2)
            except HTTPException as e:
                raise ProbeConnectionFailed("Cannot send the message %s"%e)
            finally:
                i += 1

    @staticmethod
    def requestProbes(connection):
        """Request list of probes on given connection
        :param connection: connection to use to send request
        """
        try:
            connection.request("GET", "/probes", "", {})
            response = connection.getresponse()
            pi = response.read(int(response.getheader('content-length')))
            return Params.CODEC.decode(pi)
        except HTTPException as e:
            raise ProbeConnectionFailed("Error while getting list of probes %s"%e)

    @staticmethod
    def requestResults(connection):
        """Request results on given connection

        :param connection: connection to use
        """
        try:
            connection.request("GET", "/results", "", {})
            response = connection.getresponse()
            return response.read(int(response.getheader('content-length'))).decode()
        except HTTPException as e:
            raise ProbeConnectionFailed("Error while getting results %s"%e)


class Listener(ThreadingMixIn, HTTPServer, Thread):
    """Listen to HTTP request on dedicated CommanderServer port"""

    def __init__(self, helper):
        ThreadingMixIn.daemon_threads = True
        HTTPServer.__init__(self, ("", Parameters.COMMANDER_PORT_NUMBER), self.RequestHandler)
        Thread.__init__(self)
        self.setName('Common listener')
        self.helper = helper

    def run(self):
        """Listen forever"""
        self.serve_forever()

    def close(self):
        """Stop listening to requests"""
        self.shutdown()

    class RequestHandler(SimpleHTTPRequestHandler):
        """Handler instantiated for each request which is received"""

        def __init__(self, request, client_address, server_socket):
            SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

        def log_message(self, format, *args):
            self.server.helper.getLogger().ddebug("Process message : %s -- [%s] %s" % (self.address_string(),
                                                                                       self.log_date_time_string(),
                                                                                       format % args))

        def do_POST(self):
            """Handle an HTTP POST request"""
            self.server.helper.getLogger().debug("Handling a command")
            contentLength = self.headers.get("content-length")
            # read content
            args = self.rfile.read(int(contentLength))
            # convert from bytes to string
            args = str(args, Parameters.POST_MESSAGE_ENCODING)
            # parse our string to a dictionary
            args = urllib.parse.parse_qs(args, keep_blank_values = True, strict_parsing = True,
                                         encoding = Parameters.POST_MESSAGE_ENCODING)
            # get our object as string and transform it to bytes
            message = bytes(args.get(Parameters.POST_MESSAGE_KEYWORD)[0], Parameters.POST_MESSAGE_ENCODING)
            # transform our bytes into an object
            message = Params.CODEC.decode(message)

            response = self.server.helper.handleResponse(message)

            self._reply(response.encode(Parameters.POST_MESSAGE_ENCODING))

            self.server.helper.treatMessage(message)


        def do_GET(self):
            """Handle an HTTP Get request"""
            self.server.helper.getLogger().ddebug("Handling get Request")
            getPath = urllib.parse.urlparse(self.path).path

            if getPath == Parameters.URL_PROBES_QUERY:
                self.server.helper.getLogger().debug("Giving the list of probes")
                message = self.server.helper.handleProbeQuery()

            elif getPath == Parameters.URL_RESULT_QUERY:
                self.server.helper.getLogger().debug("Asked for results of tests")
                message = self.server.helper.handleResultQuery()
            elif getPath == Parameters.URL_ID_QUERY:
                message = self.server.helper.handleIdQuery()
            else:
                message = self.server.helper.handleDefaultQuery()
            # answer with your id
            self._reply(message)

        def _reply(self, message):
            """Reply to given request"""
            if type(message) is not bytes:
                message = message.encode(Parameters.POST_MESSAGE_ENCODING)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(message))
            self.send_header("Last-Modified", str(datetime.datetime.now()))
            self.end_headers()
            self.wfile.write(message)
