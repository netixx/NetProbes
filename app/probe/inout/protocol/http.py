"""
HTTP protocol uses http to encapsulate data and send it on the network
it is base on the http.* modules from python std library

@author: francois
"""

import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from http.client import HTTPConnection, HTTPException
from socketserver import ThreadingMixIn
from threading import Thread

import urllib

from consts import Params, Identification
from calls.messages import TestMessage
from interfaces.excs import NoSuchProbe, ProbeConnectionException
from managers.probes import ProbeStorage, ProbeConnections

class Parameters(object):
    """Class containing parameters for this protocol"""
    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    REPLY_MESSAGE_ENCODING = 'latin-1'
    HTTP_POST_REQUEST = "POST"
    HTTP_GET_REQUEST = "GET"
    URL_SRV_TESTS_QUERY = "/tests"
    URL_SRV_ID_QUERY = "/id"
    URL_SRV_STATUS_QUERY = "/status"
    GET_REMOTE_ID_CONNECT_TIMEOUT = 5.0
    CONNECT_TIMEOUT = 5.0


def createConnection(probe):
    """Creates a connection for this probe
    :param probe: the probe to create a connection for
    """
    return HTTPConnection(probe.getAddress(), Parameters.PORT_NUMBER, timeout=Parameters.CONNECT_TIMEOUT)


def connect(connection):
    """Connect this connection
    :param connection: connection object to connect
    """
    try:
        connection.connect()
    except Exception as e:
        raise ProbeConnectionException(e)


def disconnect(connection):
    """Disconnect this connection
    :param connection: connection object to disconnect
    """
    connection.close()


def getRemoteId(targetIp):
    """Get the remote ID of the probe at targetIp
    :param targetIp: the IP where we should ask for the id
    """
    try:
        connection = HTTPConnection(targetIp, Parameters.PORT_NUMBER, timeout=Parameters.GET_REMOTE_ID_CONNECT_TIMEOUT)
        connection.connect()
        connection.request(Parameters.HTTP_GET_REQUEST, Parameters.URL_SRV_ID_QUERY, "", {})
        probeId = connection.getresponse().read().decode(Parameters.REPLY_MESSAGE_ENCODING)
        #     logger.logger.info("Id of probe with ip " + str(targetIp) + " is " + str(probeId))
        connection.close()
        return probeId
    except Exception as e:
        raise ProbeConnectionException(e)


class Sender(object):
    """Object responsible for sending data"""
    def __init__(self, logger):
        self.logger = logger

    def send(self, message):
        """Send this message on the network
        :param message: Message instance to send
        """
        try:
            target = ProbeStorage.getProbeById(message.targetId)
            # serialize our message
            serializedMessage = Params.CODEC.encode(message)
            # put it in a dictionary
            params = {Parameters.POST_MESSAGE_KEYWORD: serializedMessage}
            # transform dictionary into string
            params = urllib.parse.urlencode(params, doseq = True, encoding = Parameters.POST_MESSAGE_ENCODING)
            # set the header as header for POST
            headers = {
                "Content-type": "application/x-www-form-urlencoded;charset=%s" % Parameters.POST_MESSAGE_ENCODING,
                "Accept": "text/plain"}
            urlQuery = ""
            if isinstance(message, TestMessage):
                urlQuery = Parameters.URL_SRV_TESTS_QUERY

            response = self._sendMessage(target, Parameters.HTTP_POST_REQUEST, urlQuery, params, headers)

            if response.status != 200:
                self.logger.warning("Wrong status received!")
                # self.send(message)
        except NoSuchProbe:
            self.logger.error("The probe you requested to send a message to : '%s', is currently unknown to me.",
                              message.targetId)
        except HTTPException as e:
            self.logger.error("Cannot send message to %s@%s", message.targetId, target.getAddress())
            self.logger.debug("Cannot send message", exc_info = 1)
            raise ProbeConnectionException(e)
            #TODO : raise exception
            # raise ProbeConnectionException(e)


    def _sendMessage(self, targetProbe, requestType, requestUrl, params, headers):
        try:
            disconnectOnCompletion = False
            if not targetProbe.connected:
                ProbeConnections.connectToProbe(targetProbe)
                disconnectOnCompletion = True
            conn = targetProbe.connection
            response = self.__sendRequest(conn, requestType, requestUrl, params, headers)

            if disconnectOnCompletion:
                # TODO: optimise if target is still in the stack
                ProbeConnections.disconnectProbe(targetProbe)
            return response
        except Exception as e:
            raise e

    def __sendRequest(self, connection, requestType, requestUrl = "", params = "", header = None):
        connection.request(requestType, requestUrl, params,
                           header if header is not None else {})
        self.logger.ddebug("Request %s @ %s has been sent", requestType, requestUrl)
        return connection.getresponse()


class Listener(ThreadingMixIn, HTTPServer, Thread):
    """
    Threaded listener that processes a request on the server
    Instantiate one thread RequestHandler per request

    """

    def __init__(self, helper):
        self.helper = helper
        HTTPServer.__init__(self, ("", Parameters.PORT_NUMBER), self.RequestHandler)
        Thread.__init__(self)
        self.setName("HTTP Listener")

    def run(self):
        """Run is simply serve forever"""
        self.serve_forever()

    def close(self):
        """Close is shutdown"""
        self.shutdown()

    class RequestHandler(SimpleHTTPRequestHandler):
        """
        Handler that does the actual work of parsing the request
        and adding it the the queue of action after transformation
    
        """

        def __init__(self, request, client_address, server_socket):
            SimpleHTTPRequestHandler.__init__(self, request, client_address, server_socket)

        def log_message(self, format, *args):
            self.server.helper.getLogger().ddebug("Process message : %s -- [%s] %s" % (self.address_string(),
                                                                                       self.log_date_time_string(),
                                                                                       format % args))

        def do_POST(self):
            """Handle a post request
            @see the sender for which request are post"""
            self.server.helper.getLogger().ddebug("Handling POST request from another probe")
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

            response = self.server.helper.handleResponse(self, message)

            self._reply(response)

            # give the message to our server so that it is treated
            self.server.helper.treatMessage(message)

        def do_GET(self):
            """Handles a get request
            @see the sender for which requests are get request"""
            query = urllib.parse.urlparse(self.path).path
            if query == Parameters.URL_SRV_ID_QUERY:
                self.giveId()
            elif query == Parameters.URL_SRV_STATUS_QUERY:
                self.giveStatus()
            else:
                self.giveId()

        def giveId(self):
            """Return the id of this probe when asked"""
            self.server.helper.getLogger().ddebug("Server : handling get request, giving my ID : %s",
                                                  Identification.PROBE_ID)
            self._reply(self.server.helper.getId())

        def giveStatus(self):
            """Returns the status of this probe"""
            self._reply(self.server.helper.getStatus())

        def _reply(self, message):
            msg = str(message).encode(Parameters.REPLY_MESSAGE_ENCODING)
            # answer with your id
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(msg))
            self.send_header("Last-Modified", str(datetime.datetime.now()))
            self.end_headers()
            self.wfile.write(msg)
