'''
Created on 7 juin 2013

@author: francois
'''

class Action(object):
    priority = 1
    
    
class Add(Action):
    def __init__(self, ip):
        self.ip = ip
    
class Transfert(Action):
    def __init__(self, code):
        self.codeAction = code
    


