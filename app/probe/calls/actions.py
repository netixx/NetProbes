'''
Actions that our probes can perform
    Internal representations of the task at hand
Each Action has a priority, the lower the priority, the faster the action will be executed
Action class and subclasses are not sent over the network, only messages are (cf messages.py)

'''
__all__ = ['Action', 'Add', 'AddPrefix', 'UpdateProbes', 'Remove',
           'Do', 'Prepare', 'Quit', ]

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

    def __str__(self):
        return "%s action no %d" % (self.__class__.__name__, self.actionNumber)


class Add(Action):
    '''Add action : adds a probe to the overlay of probes'''

    def __init__(self, ipSonde, idSonde, hello=False):
        super().__init__()
        self.ipSonde = ipSonde
        self.idSonde = idSonde
        self.doHello = hello
        self.priority = 3

    def getIpSonde(self):
        return self.ipSonde

    def getIdSonde(self):
        return self.idSonde


class AddPrefix(Action):
    ''' Adds probes contained in given prefix, once prefix parsing is done,
    task is redirected to Add action'''

    def __init__(self, addPrefix):
        self.addPrefix = addPrefix
    
    def getPrefix(self):
        return self.addPrefix


class UpdateProbes(Action):
    '''Add the given list of probes to the hashtable (probestorage)'''
    def __init__(self, probeList):
        super().__init__()
        self.probeList = probeList
        self.priority = 3

    def getProbeList(self):
        return self.probeList


class Remove(Action):
    '''Tells the probe to remove another probe from the overlay'''
    def __init__(self, idSonde):
        super().__init__()
        self.idSonde = idSonde
        self.priority = 5

    def getIdSonde(self):
        return self.idSonde
      


class Do(Action):
    '''Do action : does a test'''

    priority = 2
    def __init__(self, testClass, testOptions, resultCallback, errorCallback):
        super().__init__()
        self.testClass = testClass
        self.testOptions = testOptions
        self.resultCallback = resultCallback
        self.errorCallback = errorCallback
        self.priority = 4
        self.testId = None

    def getTestName(self):
        return self.testClass

    def getTestOptions(self):
        return self.testOptions

    def getResultCallback(self):
        return self.resultCallback

    def getErrorCallback(self):
        return self.errorCallback

    def setTestId(self, testId):
        self.testId = testId

    def getTestId(self):
        return self.testId



class Prepare(Action):
    '''Prepare action : prepare for a test '''

    def __init__(self, testName, testId, testOptions, sourceId):
        super().__init__()
        self.testId = testId
        self.testName = testName
        self.sourceId = sourceId
        self.testOptions = testOptions
        self.priority = 1

    def getTestId(self):
        return self.testId

    def getTestName(self):
        return self.testName

    def getSourceId(self):
        return self.sourceId

    def getTestOptions(self):
        return self.testOptions


class Quit(Action):
    '''Tells this probe to quit the overlay,
    closing all connections to other probes

    '''
    def __init__(self):
        super().__init__()
        self.priority = 10
