'''
Created on 7 juin 2013

@author: francois
'''

class Action(object):
    
    def __init__(self):
        self.priority = 1
    
    
class Add(Action):
    def __init__(self, ip, IdSonde):
        self.ip = ip
        self.IdSonde = IdSonde
    

class Transfert(Action):
    def __init__(self, message, IdSonde):
        self.message = message
        self.IdSonde = IdSonde
    

class Do(Action):
    priority = 2
    def __init__(self, codeTest, IP):
        self.ip = IP
        self.codeTest = codeTest
    
