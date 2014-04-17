'''
Created on 7 juin 2013

@author: francois
'''
from interface import Interface


class Cli(Interface):
    DISPLAY_WIDTH = 100
    HEADING = ("Probe Id \t Probe Ip \t Status\n")
    PROBE_TEMPLATE = "%s \t %s \t %s\n"
    CMD_PREFIX = "do"
    DISP_CMD = "disp"
    EXIT_CMD = "exit"


    def __init__(self, probeIp):
        Interface.__init__(self, probeIp)
        #         Thread.__init__(self)
        #         self.setName("Cli")
        self.prompt = probeIp + " > "
        self.isRunning = True
        # wins and boxes
        self.status = None
        self.commandInput = None
        # assures we end correctly
        # end session

    #         curses.endwin()

    def start(self):
        while (self.isRunning):
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
        self.isRunning = False


    def getCommands(self):
        return "cmd"

    def getProbes(self):
        probes = self.HEADING
        for probe in self.fetchProbes():
            probes += self.PROBE_TEMPLATE % (probe.getId(), probe.getIp(), probe.getStatus())
        return probes

    def updateStatus(self, status):
        print("Status : %s" % status)
