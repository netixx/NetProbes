
class NoSuchCommand(Exception):
    def __init__(self):
        pass

class ProbeConnectionFailed(Exception):

    def __init__(self, consequence):
        self.consequence = consequence

    def getConsequence(self):
        return self.consequence
