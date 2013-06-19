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


def toTransfer(transferMessage):
    assert isinstance(transferMessage,m.Transfer)
    return Transfer()


def toDo(doMessage):
    return Do()


def toBye(byeMessage):
    assert isinstance(byeMessage, m.Bye)
    return Remove(byeMessage.myId)

def toHello(message):
    assert isinstance(message, m.Hello)
    return Add(message.getRemoteIp(), message.getRemoteId(), hello=False)
