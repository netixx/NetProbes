'''
Sends Message instances to other probes
    Thread that waits for a message to be added to the messageStack
    and sends message as soon as one is added

It also implements a mechanism to broadcast a message to all probes

@author: francois

'''
__all__ = ['Client']

import urllib, pickle
from threading import Thread, Event
from queue import Queue
import logging

from consts import Consts, Identification, Urls
from calls.messages import Message, BroadCast, TestMessage, StatusMessage
from managers.probes import ProbeStorage
from exceptions import NoSuchProbe

class Client(Thread):
    '''
    Client Thread : talks to the Server through http
    Server can be local (localhost) or remote
    
    '''

    messageStack = Queue()
    stop = False
    logger = logging.getLogger()
    
    def __init__(self):
        Thread.__init__(self)
        self.setName("Client")
        self.isUp = Event()

    def run(self):
        self.isUp.set()
        self.logger.info("Starting the Client")
        while not Client.stop or not Client.messageStack.empty():
            message = Client.messageStack.get()
            try:
                if isinstance(message, StatusMessage):
                    self.sendStatusMessage(message)
                else:
                    self.sendMessage(message)
            finally:
                Client.messageStack.task_done()

    @classmethod
    def quit(cls):
        cls.logger.info("Stopping the Client")
        cls.stop = True
        ProbeStorage.closeAllConnections()
    
    @classmethod
    def send(cls, message):
        '''
        Send message to target probe
        message : message to send (contains the targetId)
        
        '''
        cls.logger.debug("Adding a message %s to the client stack", message.__class__.__name__)
        assert isinstance(message, Message)
        cls.messageStack.put(message)
    
    @classmethod
    def broadcast(cls, message, toMyself = False):
        '''
        If called with a Broadcast message, the method will send
        messages to all targets listed in the broadcast
        If called with a Message instance, the method will send a message
        to all known probes

        '''
        cls.logger.debug("Broadcasting the message : %s", message.__class__.__name__)
        # propagation phase
        if isinstance(message, BroadCast):
            prop = message.getNextTargets()
        else:
            prop = ProbeStorage.getIdAllOtherProbes()
            if toMyself:
                prop.append(Identification.PROBE_ID)
            
        if len(prop) > 0:
            splitSize = min(Consts.PROPAGATION_RATE, len(prop))
            j = 0
            step = (int) (len(prop) / splitSize)
            while j < len(prop):
                propIds = prop[j:(j + step)]
                j += step
                cls.send(BroadCast(message, propIds))
            # be sure to propagate to all probes
            cls.send(BroadCast(message, prop[j:]))

    @classmethod
    def allMessagesSent(cls):
        cls.messageStack.join()
        
    '''Inner functions'''
    def __sendRequest(self, connection, requestType, requestUrl = "", params = "", header = {}):
        connection.request(requestType, requestUrl, params, header)
        self.logger.debug("Request %s @ %s has been sent", requestType, requestUrl)
        return connection.getresponse()

    def _sendMessage(self, targetProbe, requestType, requestUrl, params, headers):
        try :
            disconnectOnCompletion = False
            if not targetProbe.connected :
                targetProbe.connect()
                disconnectOnCompletion = True
            conn = targetProbe.getConnection()

            response = self.__sendRequest(conn, requestType, requestUrl, params, headers)

            if disconnectOnCompletion:
                # TODO: optimise if target is still in the stack
                targetProbe.disconnect()
            return response
        except :
            pass

    def sendMessage(self, message):
        self.logger.debug("Sending the message : %s to %s with ip %s",
                          message.__class__.__name__ ,
                          message.targetId,
                          ProbeStorage.getProbeById(message.targetId).getIp())
        try :
            target = ProbeStorage.getProbeById(message.targetId)
            # serialize our message
            serializedMessage = pickle.dumps(message, 3)
            # put it in a dictionnary
            params = {Consts.POST_MESSAGE_KEYWORD : serializedMessage}
            # transform dictionnary into string
            params = urllib.parse.urlencode(params, doseq = True, encoding = Consts.POST_MESSAGE_ENCODING)
            # set the header as header for POST
            headers = {"Content-type": "application/x-www-form-urlencoded;charset=%s" % Consts.POST_MESSAGE_ENCODING, "Accept": "text/plain"}
            urlQuery = ""
            if isinstance(message, TestMessage):
                urlQuery = Urls.SRV_TESTS_QUERY

            response = self._sendMessage(target, Consts.HTTP_POST_REQUEST, urlQuery, params, headers)

            if response.status != 200 :
                self.logger.warning("Wrong status received! Trying to resend message.")
                self.send(message)
        except NoSuchProbe:
            self.logger.error("The probe you requested to send a message to : '%s', is currently unknown to me.", message.targetId)
       
    def sendStatusMessage(self, statusMessage):
        try :
            target = ProbeStorage.getProbeById(statusMessage.targetId)
            response = self._sendMessage(target, Consts.HTTP_GET_REQUEST, Urls.SRV_STATUS_QUERY)
    
            contentLength = response.headers.get("content-length")
            # read content
            args = self.rfile.read(int(contentLength))
            # convert from bytes to string
            args = str(args, Consts.POST_MESSAGE_ENCODING)
            # parse our string to a dictionary
            args = urllib.parse.parse_qs(args, keep_blank_values = True, strict_parsing = True, encoding = Consts.POST_MESSAGE_ENCODING)
            # get our object as string and transform it to bytes
            probeStatus = bytes(args.get(Consts.POST_MESSAGE_KEYWORD)[0], Consts.POST_MESSAGE_ENCODING)
            # transform our bytes into an object
            probeStatus = pickle.loads(probeStatus)
            return probeStatus
        except NoSuchProbe:
            pass
