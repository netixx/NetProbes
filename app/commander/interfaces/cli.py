"""Command line interface for the commander

@author: francois
"""
from common.intfs.exceptions import ProbeConnectionFailed
from interface import Interface


class Cli(Interface):
    """Command line interface
    Displays a prompt that reads commands from user's keyboard input

    """
    COL_WIDTHS = (10, 20, 20)
    COL_NAMES = ("ProbeId", "ProbeIp", "Status")
    HEADING = "{names[0]:<{wi[0]}}{names[1]:<{wi[1]}}{names[2]:<{wi[2]}}\n"
    PROBE_TEMPLATE = "{names[0]:<{wi[0]}}{names[1]:<{wi[1]}}{names[2]:<{wi[2]}}\n"
    CMD_PREFIX = "do"
    DISP_CMD = "disp"
    EXIT_CMD = "exit"
    PROMPT = "%s (%s) > "


    def __init__(self, probeIp):
        Interface.__init__(self, probeIp)
        self.prompt = self.PROMPT % (self.targetId, self.targetIp)
        self.isRunning = True
        self.status = None
        self.commandInput = None

    def start(self):
        """Start reading and replying to commands"""
        while self.isRunning:
            try:
                cmd = input(self.prompt)
                if cmd.startswith(self.CMD_PREFIX):
                    self.doCommand(cmd)
                elif cmd == self.DISP_CMD:
                    print(self.getProbes())
                elif cmd == self.EXIT_CMD:
                    self.stop()
                else:
                    print("Command not recognized, commands are %s" % self.getCommands())
            except (KeyboardInterrupt, EOFError):
                self.stop()
            finally:
                print("\n")

    def stop(self):
        """Stop listening"""
        self.isRunning = False


    def getCommands(self):
        """Return available commands"""
        return "Commands : %s"% ', '.join([self.CMD_PREFIX, self.DISP_CMD, self.EXIT_CMD])


    def getProbes(self):
        """Get probe from remote commander server and prints them as string"""
        try:
            p = self.fetchProbes()
            probes = self.HEADING.format(wi = self.COL_WIDTHS, names = self.COL_NAMES)
            for probe in p:
                probes += self.PROBE_TEMPLATE.format(names = (probe.getId(), probe.getIp(), probe.getStatus()), wi = self.COL_WIDTHS)
            return probes
        except ProbeConnectionFailed:
            self.updateStatus("Cannot get the list of probes")
            self.logger.error("Connection failed", exc_info = 1)

    def updateStatus(self, status):
        """Update the status of this commander
        :param status: new status to apply
        """
        print("Status : %s" % status)
