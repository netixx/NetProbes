"""Messages used to command a probe remotely with the commander

@author: francois
"""


class CommanderMessage(object):
    """A basic message contains the ID of the probe to command"""

    def __init__(self, targetId):
        self.targetId = targetId


class Add(CommanderMessage):
    """Tell the target probe to add the probe located at this IP"""

    def __init__(self, targetId, targetIp):
        super().__init__(targetId)
        self.targetIp = targetIp


class Do(CommanderMessage):
    """Tell the target probe to perform a test"""

    def __init__(self, targetId, test, testOptions = None):
        super().__init__(targetId)
        self.test = test
        self.testOptions = testOptions


class Delete(CommanderMessage):
    """Tell the target probe to remove itself from the overlay"""

    def __init__(self, targetId):
        super().__init__(targetId)
