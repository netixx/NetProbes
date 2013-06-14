'''
Created on 11 juin 2013

@author: francois
'''
from actions import *
import messages as m

messages = {"Add" : "toAdd",
            "Transfer" : "toTransfer",
            "Do" : "toDo",
            "Bye" : "toBye"}

def toAction(message):
    assert isinstance(message, m.Message)
    return globals()[messages.get(message.__class__.__name__)](message)


def toAdd(addMessage):
    assert isinstance(addMessage,m.Add)
    return Add(addMessage.probeIP, addMessage.probeID)


def toTransfer(transferMessage):
    assert isinstance(transferMessage,m.Transfer)
    return Transfer()


def toDo(doMessage):
    return Do()


def toBye(byeMessage):
    assert isinstance(byeMessage, m.Bye)
    return Remove(byeMessage.myId)