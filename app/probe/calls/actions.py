'''
Actions that our probes can perform
'''
treatedAction = 0

'''General class, defining priority of the actions'''
class Action(object):
    def __init__(self):
        # low prioriy
        self.priority = 10
        self.actionNumber = treatedAction

    def __lt__(self, other):
        selfPriority = (self.priority, self.actionNumber)
        otherPriority = (other.priority, other.actionNumber)
        return selfPriority < otherPriority


'''Add action : adds a probe to the network'''
class Add(Action):
    def __init__(self, ipSonde, idSonde, hello=False):
        Action.__init__(self)
        self.ipSonde = ipSonde
        self.idSonde = idSonde
        self.doHello = hello
        self.priority = 3

    def getIpSonde(self):
        return self.ipSonde

    def getIdSonde(self):
        return self.idSonde

    def setHello(self, doHello):
        self.doHello = doHello

    def getHello(self):
        return self.doHello

'''Removes a probe from the network'''
class Remove(Action):
    def __init__(self, idSonde):
        Action.__init__(self)
        self.idSonde = idSonde
        self.priority = 3

    def getIdSonde(self):
        return self.idSonde
      

'''Do action : does a test'''
class Do(Action):
    priority = 2
    def __init__(self, testClass, testOptions):
        Action.__init__(self)
        self.testClass = testClass
        self.testOptions = testOptions
        self.priority = 1

    def getTest(self):
        return self.testClass

    def getOptions(self):
        return self.testOptions

'''Prepare action : prepare for a test'''
class Prepare(Action):

    def __init__(self, testId, sourceId, testOptions):
        super().__init__()
        self.testId = testId
        self.sourceId = sourceId
        self.testOptions = testOptions
        self.priority = 1

    def getTestId(self):
        return self.testId

    def getSourceId(self):
        return self.sourceId

    def getTestOptions(self):
        return self.testOptions

'''Tells the probe to quit the network, closing all connections'''
class Quit(Action):
    def __init__(self):
        Action.__init__(self)
        self.priority = 2
