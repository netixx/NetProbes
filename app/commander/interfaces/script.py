"""Command line interface for the commander

@author: francois
"""
from common.intfs.exceptions import ProbeConnectionFailed
from interface import Interface

class Script(Interface):
    """Not a real interface, interprets one command and shuts down"""

    def __init__(self, probeIp, command):
        Interface.__init__(self, probeIp)
        self.args = self.parseCommand(command)

    def start(self):
        """Start executing given command"""
        cmd = self.doCommand(self.args)
        cmd.join()

    def parseCommand(self, command):
        return command

    def quit(self):
        """Stop listening"""
        super().quit()

    def getProbes(self):
        """Get probe from remote commander server and prints them as string"""
        probes = ""
        try:
            p = self.fetchProbes()
            for probe in p:
                probes += "{id};{ip};{status};\n".format(id = probe.getId(), ip = probe.getIp(), status = probe.getStatus())
        except ProbeConnectionFailed:
            probes = "error"
        finally:
            return probes

    def updateStatus(self, status):
        """Update the status of this commander
        :param status: new status to apply
        """
        pass
