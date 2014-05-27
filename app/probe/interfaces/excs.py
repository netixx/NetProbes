"""
Customized exceptions for the probe program

"""
__all__ = ['NoSuchProbe', 'ProbeConnection', 'ToManyTestsInProgress',
           'TestInProgress', 'ActionError', 'TestArgumentError',
           'TestError', 'TestAborted']


class NoSuchProbe(Exception):
    """The probe asked for is unknown to this probe = the id does not exist in storage"""
    pass


class ProbeConnectionException(Exception):
    """Problem while connecting to the probe, could be a problem creating the connection, connection or
    disconnecting. The probe is not available somehow

    """
    pass


class ToManyTestsInProgress(Exception):
    """Maximum number of allowed test has been reached"""
    pass


class ActionError(Exception):
    """Generic error during the processing of an action"""
    tpl = "Error occurred while performing action %s : %s"

    def __init__(self, message, action):
        self.action = action
        self.message = message

    def __str__(self):
        if type(self.action) == ActionError:
            return self.action.__str__()
        return self.tpl % (self.action, self.message)


class TestError(ActionError):
    """Error occurred during a test, usually recoverable error"""

    def __init__(self, reason):
        self.action = "Test"
        self.message = reason

    def getReason(self):
        """Returns the reason for failure"""
        return self.message

class TestArgumentError(TestError):
    """The arguments supply for this test are not recognised by the test/parser"""

    def __init__(self, usage):
        self.usage = usage

    def getUsage(self):
        """Return the supported syntax for options"""
        return "Wrong argument : " + self.usage

class TestAborted(TestError):
    """The test was aborted early"""
    pass

class ClientError(Exception):
    pass

class SendError(ClientError):
    pass
