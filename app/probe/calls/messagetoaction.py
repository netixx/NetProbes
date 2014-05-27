"""
Transforms a Message into an Action
Mapping is done by the messages dict
@author: francois

"""
__all__ = ['toAction']

import logging

from . import messages as m
from consts import Identification
from .actions import Add, Quit, Remove, Prepare, UpdateProbes, Do, AddToOverlay, Broadcast
from managers.probes import Probe


treatedAction = 0

"""Matches message class to its corresponding method"""
prefix = '_to'
logger = logging.getLogger()


def toAction(message):
    """Transform given message into an action
    :param message: Message instance to transform"""
    logger.debug("Transforming message %s into action", message.__class__.__name__)
    assert isinstance(message, m.Message)
    global treatedAction
    treatedAction += 1
    # calls the right method
    return globals()[prefix + message.__class__.__name__](message)


def _toAdd(addMessage):
    assert isinstance(addMessage, m.Add)
    return Add(addMessage.probeIP, addMessage.probeID, addMessage.hello)


def _toBye(byeMessage):
    assert isinstance(byeMessage, m.Bye)
    if byeMessage.getLeavingID() == Identification.PROBE_ID:
        logger.ddebug("Making Quit action from Bye message")
        return Quit()
    else:
        logger.ddebug("Making Remove action from Bye message")
        return Remove(byeMessage.getLeavingID())


def _toHello(message):
    logger.ddebug("Making Hello action from Hello message")
    assert isinstance(message, m.Hello)
    probes = message.getProbeList()
    probes.append(Probe(message.sourceId, message.remoteIp))
    return UpdateProbes(probes, echo = message.echo)


def _toPrepare(message):
    logger.ddebug("Making Prepare action from Prepare message")
    assert isinstance(message, m.Prepare)
    return Prepare(message.getTestName(), message.getTestId(), message.getTestOptions(), message.getSourceId())


def _toDo(message):
    logger.ddebug("Making Do action from Do message")
    assert isinstance(message, m.Do)
    return Do(message.getTestName(), message.getTestOptions(), message.getResultCallback(), message.getErrorCallback())


def _toAddToOverlay(message):
    assert isinstance(message, m.AddToOverlay)
    return AddToOverlay(message.getProbeIp(), mergeOverlays = message.mergeOverlays)


def _toBroadcast(message):
    assert isinstance(message, m.BroadCast)
    return Broadcast(broadcast = message)
