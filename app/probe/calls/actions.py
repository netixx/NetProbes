'''
Actions that our probes can perform
    Internal representations of the task at hand
Each Action has a priority, the lower the priority, the faster the action will be executed
Action class and subclasses are not sent over the network, only messages are (cf messages.py)

'''

class Action(object):
    '''General class, defining priority of the actions'''

    def __init__(self):
        # low prioriy
        self.priority = 10
        from .messagetoaction import treatedAction
        self.actionNumber = treatedAction

    def __lt__(self, other):
        selfPriority = (self.priority, self.actionNumber)
        otherPriority = (other.priority, other.actionNumber)
        return selfPriority < otherPriority

class Add(Action):
    '''Add action : adds a probe to the overlay of probes'''

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


class UpdateProbes(Action):
    '''Add the given list of probes to the hashtable (probestorage)'''
    def __init__(self, probeList):
        Action.__init__(self)
        self.probeList = probeList

    def getProbeList(self):
        return self.probeList


class Remove(Action):
    '''Tells the probe to remove another probe from the overlay'''
    def __init__(self, idSonde):
        Action.__init__(self)
        self.idSonde = idSonde
        self.priority = 3

    def getIdSonde(self):
        return self.idSonde
      


class Do(Action):
    '''Do action : does a test'''

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


class Prepare(Action):
    '''Prepare action : prepare for a test'''

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


class Quit(Action):
    '''Tells this probe to quit the overlay,
    closing all connections to other probes

    '''
    def __init__(self):
        Action.__init__(self)
        self.priority = 2
