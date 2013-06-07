'''
Created on 7 juin 2013

@author: francois
'''

class Message(object):
    '''
    classdocs
    Message sent from one probe to another
    '''
<<<<<<< Upstream, based on origin/master
    def __init__(self, targetId):
        self.targetId = targetId;
        
=======
    

>>>>>>> c1197e1 Client first commit

class Add(Message):
    '''
    classdocs
    '''
<<<<<<< Upstream, based on origin/master
=======
    def __init__(self, probeID, probeIP):
        self.probeID = probeID
        self.probeIP = probeIP

>>>>>>> c1197e1 Client first commit

class Transfer(Message):
    '''
    classdocs
    '''


class Hello(Message):
    '''
    classdocs
    '''


class Bye(Message):
    '''
    classdocs
    '''



class Prepare(Message):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    
    
class Ready(Message):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

class Abort(Message):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
        
class Over(Message):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''

class Result(Message):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
