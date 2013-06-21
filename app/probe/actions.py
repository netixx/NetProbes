'''
Created on 7 juin 2013

@author: francois

Add
Remove
Tranfer
Do
Quit
'''

class Action(object):
    
    def __init__(self):
        #low prioriy 
        self.priority = 1
    

class Add(Action):
    def __init__(self, ipSonde, idSonde, hello=False):
        Action.__init__(self)
        self.ipSonde = ipSonde
        self.idSonde = idSonde
        self.doHello = hello
    
    def getIpSonde(self):
        return self.ipSonde

    def getIdSonde(self):
        return self.idSonde
    
    def setHello(self, doHello):
        self.doHello = doHello
    
    def getHello(self):
        return self.doHello


    

class Do(Action):
    priority = 2
    def __init__(self, testClass, testOptions):
        Action.__init__(self)
        self.testClass = testClass
        self.testOptions = testOptions

    def getTest(self):
        return self.testClass

    def getOptions(self):
        return self.testOptions


class Prepare(Action):
    priority = 0
    def __init__(self, testId, sourceId):
        super().__init__(self)
        self.testId = testId
        self.sourceId = sourceId

    def getTestId(self):
        return self.testId
    
    def getSourceId(self):
        return self.sourceId


class Quit(Action):
    def __init__(self):
        Action.__init__(self)
        self.priority = 0  # high priority


class Remove(Action):
    def __init__(self, idSonde):
        Action.__init__(self)
        self.idSonde = idSonde
    
    def getIdSonde(self):
        return self.idSonde
