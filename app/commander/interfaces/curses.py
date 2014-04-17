'''
Created on 7 juin 2013

@author: francois
'''
from threading import Thread
import curses
import time
from curses.textpad import Textbox

from interface import Interface


class Curses(Interface):
    DISPLAY_WIDTH = 100
    FIELDS_DISPLAY_WIDTH = [30 , 20]
    COMMAND_LINE_NUMBER = 3
    REFRESH_TIME = 5
    HEADING = ("Probe Id", "Probe Ip")

    def __init__(self, probeIp):
        Interface.__init__(self, probeIp)
#         Thread.__init__(self)
#         self.setName("Cli")
        self.isRunning = True
        # wins and boxes
        self.status = None
        self.commandInput = None
        self.text = None
        self.probesPanel = None
        # assures we end correctly
        # end session
#         curses.endwin()

    def start(self):
        try:
            curses.wrapper(self.main)
        finally:
            self.isRunning = False
           

    def initPanels(self, stdscr):
        self.DISPLAY_WIDTH = curses.COLS - 1;
    
        self.text = stdscr.subwin(1, self.DISPLAY_WIDTH, 0, 0)
        self.text.addstr(0, 0, "Enter a command :")
        self.text.refresh()

        self.commandInput = stdscr.subwin(self.COMMAND_LINE_NUMBER - 2, self.DISPLAY_WIDTH, 1, 0)
        self.commandInput.refresh()

        self.status = stdscr.subwin(1, self.DISPLAY_WIDTH, self.COMMAND_LINE_NUMBER - 1, 0)
        self.updateStatus("Waiting for command ...")

        self.probesPanel = stdscr.subwin(curses.LINES - 1 - self.COMMAND_LINE_NUMBER, self.DISPLAY_WIDTH, self.COMMAND_LINE_NUMBER, 0)
        self.probesPanel.refresh()

        # move the cursor at the right place
        stdscr.move(1, 0)

    def main(self, stdscr):
        try:
        #   stdscr = curses.initscr()
            # Clear screen
            stdscr.clear()
            # remove the cursor
            curses.curs_set(True)
            # remove echo from touched keys
            # curses.noecho()
            self.initPanels(stdscr)

            box = Textbox(self.commandInput)
        #     stdscr.refresh()
            th = Thread(target=self.refreshProbes, name="Probe-Refresh", daemon=True)
            th.start()
            stdscr.refresh()

            while(self.isRunning):
                stdscr.refresh()
                box.edit()
                self.doCommand(box.gather())
        #         commandInput.refresh()

            # listen without entering enter
            # curses.cbreak())
        finally:
            self.isRunning = False
            th.join()
            # let curses handle special keys
            stdscr.keypad(True)
            stdscr.refresh()
            stdscr.getkey()


    def refreshProbes(self):
        while(self.isRunning):
            self.drawProbes(self.fetchProbes())
            self.probesPanel.refresh()
            time.sleep(self.REFRESH_TIME)

    # get an area where all the probes can be painted
    def drawProbes(self, probes):
        i = 0
        self.probesPanel.addstr(i, 0, "-"*self.DISPLAY_WIDTH)
        i += 1
        x = 0
        for idx, val in enumerate(self.FIELDS_DISPLAY_WIDTH):
            self.probesPanel.addstr(i, x, "| " + self.HEADING[idx])
            x += val

        self.probesPanel.addstr(i, self.DISPLAY_WIDTH - 1, "|")
        i += 1

        self.probesPanel.addstr(i, 0, "-"*self.DISPLAY_WIDTH)
        i += 1

        for probe in probes:
            prid = str(probe.getId())
            ip = probe.getIp()
            self.probesPanel.addstr(i, 0, "| " + prid)
            self.probesPanel.addstr(i, self.FIELDS_DISPLAY_WIDTH[0], "| " + ip)
            self.probesPanel.addstr(i, self.DISPLAY_WIDTH - 1, "|")
            i += 1
        return self.probesPanel;

    def updateStatus(self, newStatus):
        self.status.addstr(0, 0, newStatus)
        self.status.clrtobot()
        self.status.refresh()
