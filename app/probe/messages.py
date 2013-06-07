'''
Created on 7 juin 2013

@author: francois
'''

class Message(object):
    '''
    classdocs
    Message sent from one probe to another
    '''
    def __init__(self):
        pass

class Add(Message):
    '''
    classdocs
    '''


    def __init__(self, sourceIp):
        '''
        Constructor
        '''
        self.sourceIp = sourceIp

class Transfer(Message):
    '''
    classdocs
    '''


    def __init__(self, source):
        '''
        Constructor
        '''
        self.source = source
        
class Hello(Message):
    '''
    classdocs
    '''


    def __init__(self, source):
        '''
        Constructor
        '''
        self.source = source

class Do(Message):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        
        
class Bye(Message):
    '''
    classdocs
    '''


    def __init__(self, source):
        '''
        Constructor
        '''
        self.source = source
        
        

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
