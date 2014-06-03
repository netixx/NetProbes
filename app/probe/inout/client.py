"""
Sends Message instances to other probes
    Thread that waits for a message to be added to the messageStack
    and sends message as soon as one is added

It also implements a mechanism to broadcast a message to all probes

@author: francois

"""
__all__ = ['Client']

from queue import Queue
from threading import Thread, Event
import logging
import copy

from calls.messages import Message, BroadCast
from consts import Consts, Identification, Params
from managers.probes import ProbeStorage
from interfaces.excs import NoSuchProbe, SendError, ClientError, ProbeConnectionException


class Client(Thread):
    """
    Client Thread : talks to the Server through Params.PROTOCOL class
    Server can be local (localhost) or remote
    
    """

    messageStack = Queue()
    stop = False
    logger = logging.getLogger()

    def __init__(self):
        Thread.__init__(self)
        self.setName("Client")
        self.isUp = Event()
        self.sender = Params.PROTOCOL.Sender(self.logger)

    def run(self):
        """Start listening to message added to the stack"""
        self.isUp.set()
        self.logger.info("Starting the Client")
        while not self.stop or not self.messageStack.empty():
            message = Client.messageStack.get()
            try:
                if message is None:
                    self.stop = True
                    return

                #                 if isinstance(message, StatusMessage):
                #                     self.sendStatusMessage(message)
                #                 else:
                self.sendMessage(message)
            except ClientError as e:
                self.logger.warning("Error while sending message to %s: %s", message.targetId, e)
            except Exception as e:
                self.logger.error("Unexpected error while sending message to %s : %s", message.targetId, e, exc_info = 1)
            finally:
                self.messageStack.task_done()


    @classmethod
    def _terminate(cls):
        #wait until all messages are treated before stopping to listen
        cls.messageStack.join()
        cls.messageStack.put(None)

    @classmethod
    def quit(cls):
        """Terminate this instance properly"""
        cls.logger.info("Stopping the Client")
        cls._terminate()
        ProbeStorage.closeAllConnections()

    @classmethod
    def getRemoteId(cls, targetIp):
        return Params.PROTOCOL.getRemoteId(targetIp)

    @classmethod
    def send(cls, message):
        """Send message to target probe
        :param message: Message instance to send (contains the targetId of the probe to send the message to)

        """
        cls.logger.ddebug("Adding a message %s to the client stack", message.__class__.__name__)
        assert isinstance(message, Message)
        cls.messageStack.put(message)
        cls.logger.debug("Message %s added to the stack", message.__class__.__name__)

    @classmethod
    def broadcast(cls, message, toMyself = False):
        """If called with a Broadcast message, the method will send
        messages to all targets listed in the broadcast
        If called with a Message instance, the method will send a message
        to all known probes
        :param message: Message to broadcast, can also be an Broadcast message to propagate
        :param toMyself: Should the broadcast be sent to the local server as well ?

        """
        cls.logger.debug("Broadcasting the message : %s", message.__class__.__name__)
        if isinstance(message, BroadCast):
            cls._propagateBroadcast(message)
        else:
            cls._initiateBroadcast(message, toMyself)

    @classmethod
    def _propagateBroadcast(cls, broadcast):
        assert isinstance(broadcast, BroadCast)
        prop = broadcast.getNextTargets()
        payload = broadcast.getMessage()
        cls.logger.debug("Propagating message %s to %s", broadcast.__class__.__name__, repr(prop))

        #Only do something if there is something to do
        if len(prop) > 0:
            if len(prop) <= Consts.PROPAGATION_RATE:
                #in the end, send the actual message
                for p in prop:
                    mes = copy.deepcopy(payload)
                    mes.targetId = p
                    mes.recipientId = p
                    #if we know the target, send the message
                    if ProbeStorage.isKnownId(p):
                        cls.send(mes)
                    elif ProbeStorage.isKnownId(broadcast.sourceId):
                        #try to avoid breaking the chain during broadcasts
                        #send back the payload to the initial source of the broadcast if we don't know this recipient
                        # (forwarding at initial host will work)
                        mes.recipientId = broadcast.sourceId
                        cls.send(mes)
                    else:
                        mes.recipientId = ProbeStorage.getOtherRandomId()
                        cls.send(mes)
            else:
                pRate = Consts.PROPAGATION_RATE
                # take targets for first hop out of the list
                sendTo = prop[0:pRate]
                pt = prop[pRate:]
                propTargets = [pt[i::pRate] for i in range(pRate)]
                for i, firstHop in enumerate(sendTo):
                    nextHops = propTargets[i]
                    #copy the sourceId of the original message when chaining
                    m = BroadCast(firstHop, broadcast.sourceId, payload, nextHops)
                    if ProbeStorage.isKnownId(firstHop):
                        cls.send(m)
                    elif ProbeStorage.isKnownId(broadcast.sourceId):
                        m.recipientId = broadcast.sourceId
                        cls.send(m)
                    else:
                        m.recipientId = ProbeStorage.getOtherRandomId()
                        cls.send(m)

    @classmethod
    def _initiateBroadcast(cls, message, toMyself):
        cls.logger.debug("Initiating broadcast message %s", message.__class__.__name__)
        # propagation phase
        prop = ProbeStorage.getIdAllOtherProbes()
        if toMyself:
            # make sure we are the first on our list
            prop.insert(0, Identification.PROBE_ID)

        #Only do something if there is something to do
        if len(prop) > 0:
            if len(prop) <= Consts.PROPAGATION_RATE:
                for p in prop:
                    mes = copy.deepcopy(message)
                    mes.targetId = p
                    mes.recipientId = p
                    cls.send(mes)
            else:
                pRate = Consts.PROPAGATION_RATE
                # take targets for first hop out of the list
                sendTo = prop[0:pRate]
                pt = prop[pRate:]
                propTargets = [pt[i::pRate] for i in range(pRate)]
                for i, firstHop in enumerate(sendTo):
                    cls.send(BroadCast(firstHop, Identification.PROBE_ID, message, propTargets[i]))


    @classmethod
    def allMessagesSent(cls):
        """Method that returns when all messages in the stack are sent"""
        cls.messageStack.join()

    ### Inner functions

    def sendMessage(self, message):
        """Send this message using the Params.PROTOCOL
        :param message: The message to send
        """
        if not ProbeStorage.isKnownId(message.recipientId):
            self.logger.warning("The probe %s is not currently known to me, message will not be sent", message.targetId)
            return
        self.logger.debug("Sending the message : %s to %s with ip %s",
                          message.__class__.__name__,
                          message.getTarget(),
                          ProbeStorage.getProbeById(message.getTarget()).getIp())
        try:
            self.sender.send(message)
        except ProbeConnectionException as e:
            raise SendError(e)

#     def sendStatusMessage(self, statusMessage):
#         try :
#             target = ProbeStorage.getProbeById(statusMessage.targetId)
#             response = self._sendMessage(target, Consts.HTTP_GET_REQUEST, Urls.SRV_STATUS_QUERY)
#
#             contentLength = response.headers.get("content-length")
#             # read content
#             args = self.rfile.read(int(contentLength))
#             # convert from bytes to string
#             args = str(args, Consts.POST_MESSAGE_ENCODING)
#             # parse our string to a dictionary
#             args = urllib.parse.parse_qs(args, keep_blank_values = True, strict_parsing = True, encoding = Consts.POST_MESSAGE_ENCODING)
#             # get our object as string and transform it to bytes
#             probeStatus = bytes(args.get(Consts.POST_MESSAGE_KEYWORD)[0], Consts.POST_MESSAGE_ENCODING)
#             # transform our bytes into an object
#             probeStatus = Params.CODEC.decode(probeStatus)
#             return probeStatus
#         except NoSuchProbe:
#             pass
