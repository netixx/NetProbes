"""Command line interface for the commander

@author: francois
"""
from common.intfs.exceptions import ProbeConnectionFailed
from interface import Interface

class Script(Interface):
    """Not a real interface, interprets one command and shuts down"""

    error = "error"
    def __init__(self, probeIp, command):
        Interface.__init__(self, probeIp)
        self.args = self.parseCommand(command)
        self.out = ""

    def start(self):
        """Start executing given command"""
        cmd = self.doCommand(self.args)
        if cmd is not None:
            cmd.join()
        else:
            self.out = self.error

    def parseCommand(self, command):
        return command

    def quit(self):
        """Terminate action"""
        print(self.out)
        super().quit()

    def getProbes(self):
        """Get probe from remote commander server and prints them as string"""
        probes = ""
        try:
            p = self.fetchProbes()
            for probe in p:
                probes += "{id};{ip};{status};\n".format(id = probe.getId(), ip = probe.getIp(), status = probe.getStatus())
        except ProbeConnectionFailed:
            probes = self.error
        finally:
            return probes

    def updateStatus(self, status):
        """Update the status of this commander
        :param status: new status to apply
        """
        pass
