"""
Actions that our probes can perform
    Internal representations of the task at hand
Each Action has a priority, the lower the priority, the faster the action will be executed
Action class and subclasses are not sent over the network, only messages are (cf messages.py)

"""
__all__ = ['Action', 'Add', 'AddPrefix', 'UpdateProbes', 'Remove',
           'Do', 'Prepare', 'Quit', ]


class Action(object):
    """General class, defining priority of the actions"""

    def __init__(self):
        # low priority
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
    """Add action : adds a probe to the currently known probes"""

    def __init__(self, probeIp, probeId, hello = None):
        super().__init__()
        self.probeIp = probeIp
        self.probeId = probeId
        self.hello = hello
        #must ABSOLUTELY be lower than AddToOverlay
        self.priority = 3

    def getIpSonde(self):
        """Returns the Ip of the probe to add"""
        return self.probeIp

    def getIdSonde(self):
        """Returns the Id of the probe to add"""
        return self.probeId


class AddToOverlay(Action):
    def __init__(self, probeIp, mergeOverlays = False):
        super().__init__()
        self.priority = 4
        self.probeIp = probeIp
        self.mergeOverlays = mergeOverlays


class AddPrefix(Action):
    """ Adds probes contained in given prefix, once prefix parsing is done,
    task is redirected to Add action"""

    def __init__(self, addPrefix):
        super().__init__()
        self.addPrefix = addPrefix

    def getPrefix(self):
        """Returns the prefix = set of addresses to add"""
        return self.addPrefix


class UpdateProbes(Action):
    """Add the given list of probes to the hash table (ProbeStorage)"""

    def __init__(self, probeList, echo = None):
        super().__init__()
        self.probeList = probeList
        self.echo = echo
        self.priority = 2

    def getProbeList(self):
        """Returns the list of probes to add"""
        return self.probeList


class Remove(Action):
    """Tells the probe to remove another probe from the overlay"""

    def __init__(self, idSonde):
        super().__init__()
        self.idSonde = idSonde
        self.priority = 5

    def getIdSonde(self):
        """Returns the Id of the probe to remove"""
        return self.idSonde


class Do(Action):
    """Do action : does a test"""

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
        """Returns the name of the test as returned by the getName method of tests"""
        return self.testClass

    def getTestOptions(self):
        """Returns the options of the test as an array"""
        return self.testOptions

    def getResultCallback(self):
        """Returns the function to call to process the results"""
        return self.resultCallback

    def getErrorCallback(self):
        """Returns the function to call to process the errors"""
        return self.errorCallback

    def setTestId(self, testId):
        """Sets the Id of the test (known only once it has started
        :param testId: The id of the test as string
        """
        self.testId = testId

    def getTestId(self):
        """Returns the id of the test (once it has started) or None if it hasn't"""
        return self.testId


class Prepare(Action):
    """Prepare action : prepare for a test """

    def __init__(self, testName, testId, testOptions, sourceId):
        super().__init__()
        self.testId = testId
        self.testName = testName
        self.sourceId = sourceId
        self.testOptions = testOptions
        self.priority = 1

    def getTestId(self):
        """Returns the Id of the test to prepare for"""
        return self.testId

    def getTestName(self):
        """Return the name of the test to prepare for"""
        return self.testName

    def getSourceId(self):
        """Return the Id of the probe who asks for the test"""
        return self.sourceId

    def getTestOptions(self):
        """Return the options for this test as an array"""
        return self.testOptions


class Quit(Action):
    """Tells this probe to quit the overlay,
    closing all connections to other probes

    """

    def __init__(self):
        super().__init__()
        self.priority = 10
