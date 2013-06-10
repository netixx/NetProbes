'''
Created on 7 juin 2013

@author: francois
'''

import pickle

class Message(object):
    '''
    classdocs
    Message sent from one probe to another
    '''
    
    def __init__(self, targetId):
        self.targetId = targetId;
    


class Add(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId, probeID, probeIP):
        Message.__init__(self, targetId)
        self.probeID = probeID
        self.probeIP = probeIP



class Transfer(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId, message):
        Message.__init__(self, targetId)
        self.message = pickle.dumps( message )


class Hello(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)
    
    

class Bye(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)



class Prepare(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)
    


    

class Ready(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)






class Abort(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)





class Over(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)






class Result(Message):
    '''
    classdocs
    '''
    def __init__(self, targetId):
        Message.___init__(self, targetId)




