'''
Transforms a Message into an Action
Mapping is done by the messages dict
@author: francois

'''
__all__ = ['toAction']

from . import messages as m
from consts import Identification
from .actions import Add, Quit, Remove, Prepare, UpdateProbes, Do
import logging
from managers.probes import Probe

treatedAction = 0

'''Matches message class to its corresponding method'''
messages = {
            "Add" : "_toAdd",
            "Bye" : "_toBye",
            "Hello" : "_toHello",
            "Prepare" : "_toPrepare",
            "Do" : '_toDo'
            }

logger = logging.getLogger()

def toAction(message):
    logger.debug("Transforming message %s into action", message.__class__.__name__)
    assert isinstance(message, m.Message)
    global treatedAction
    treatedAction += 1
    # calls the right method
    return globals()[messages.get(message.__class__.__name__)](message)

def _toAdd(addMessage):
    assert isinstance(addMessage,m.Add)
    return Add(addMessage.probeIP, addMessage.probeID, addMessage.doHello)

def _toBye(byeMessage):
    assert isinstance(byeMessage,m.Bye)
    if byeMessage.getLeavingID() == Identification.PROBE_ID:
        logger.debug("Making Quit action from Bye message")
        return Quit()
    else:
        logger.debug("Making Remove action from Bye message")
        return Remove( byeMessage.getLeavingID() )


def _toHello(message):
    logger.debug("Making Hello action from Hello message")
    assert isinstance(message, m.Hello)
    probes = message.getProbeList()
    probes.append(Probe(message.sourceId, message.remoteIp))
    return UpdateProbes(probes)


def _toPrepare(message):
    logger.debug("Making Prepare action from Prepare message")
    assert isinstance(message, m.Prepare)
    return Prepare(message.getTestName(), message.getTestId(), message.getTestOptions(), message.getSourceId())

def _toDo(message):
    logger.debug("Making Do action from Do message")
    assert isinstance(message, m.Do)
    return Do(message.getTestName(), message.getTestOptions(), message.getResultCallback(), message.getErrorCallback())

