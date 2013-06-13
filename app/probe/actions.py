'''
Created on 7 juin 2013

@author: francois
'''

class Action(object):
    
    def __init__(self):
        #low prioriy 
        self.priority = 1
    
class Add(Action):
    def __init__(self, ipSonde, idSonde):
        Action.__init__(self)
        self.ipSonde = ipSonde
        self.idSonde = idSonde
    
    def getIpSonde(self):
        return self.ipSonde

    def getIdSonde(self):
        return self.idSonde

class Transfer(Action):
    def __init__(self, message, idSonde):
        Action.__init__(self)
        self.message = message
        self.IdSonde = idSonde
    

class Do(Action):
    priority = 2
    def __init__(self, codeTest, IP):
        Action.__init__(self)
        self.ip = IP
        self.codeTest = codeTest
    
