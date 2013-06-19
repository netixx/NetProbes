'''
Created on 11 juin 2013

@author: francois
'''
from actions import *
import messages as m
import consts

messages = {"Add" : "toAdd",
            "Transfer" : "toTransfer",
            "Do" : "toDo",
            "Bye" : "toBye",
            "Hello" : "toHello"}

def toAction(message):
    consts.debug("Message to Action : transforming message into action")
    assert isinstance(message, m.Message)
    return globals()[messages.get(message.__class__.__name__)](message)


def toAdd(addMessage):
    assert isinstance(addMessage,m.Add)
    return Add(addMessage.probeIP, addMessage.probeID, hello=addMessage.getHello())


def toBye(byeMessage):
    assert isinstance(byeMessage,m.Bye)
    if byeMessage.getLeavingID() == consts.Identification.PROBE_ID:
        consts.debug("Message to Action : Probe quit message")
        return Quit()
    else:
        consts.debug("Message to Action : remove probe message")
        return Remove( byeMessage.getLeavingID() )


def toDo(doMessage):
    return Do()


def toHello(message):
    assert isinstance(message, m.Hello)
    return Add(message.getRemoteIP(), message.getRemoteID(), hello=False)
