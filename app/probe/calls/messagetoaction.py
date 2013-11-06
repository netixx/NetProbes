'''
Transforms a Message into an Action

@author: francois
'''
from . import messages as m
from probe import consts
from .actions import Add, Quit, Remove, Prepare, treatedAction, UpdateProbes

'''
Matches message class to its corresponding method

'''
messages = {"Add" : "toAdd",
            "Connect" : "toConnect",
            "Bye" : "toBye",
            "Hello" : "toHello",
            "Prepare" : "toPrepare"}

def toAction(message):
    consts.debug("Message to Action : transforming message into action")
    assert isinstance(message, m.Message)
    treatedAction += 1
    return globals()[messages.get(message.__class__.__name__)](message)


def toAdd(addMessage):
    assert isinstance(addMessage,m.Add)
    return Add(addMessage.probeIP, addMessage.probeID, addMessage.getNextTargets())

def toConnect(connectMessage):
    pass

def toBye(byeMessage):
    assert isinstance(byeMessage,m.Bye)
    if byeMessage.getLeavingID() == consts.Identification.PROBE_ID:
        consts.debug("Message to Action : Probe quit message")
        return Quit()
    else:
        consts.debug("Message to Action : remove probe message")
        return Remove( byeMessage.getLeavingID() )


def toHello(message):
    assert isinstance(message, m.Hello)
    return UpdateProbes(message.getProbeList())


def toPrepare(message):
    assert isinstance(message, m.Prepare)
    return Prepare(message.getTestId(), message.getSourceId(), message.getTestOptions())

