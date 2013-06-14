'''
Created on 7 juin 2013

@author: francois
'''

import curses
from curses import wrapper
import time
from curses.textpad import Textbox
from threading import Thread
from commands import Parser, Command

class Cli(Thread):
    DISPLAY_WIDTH = 100
    COMMAND_LINE_NUMBER = 3
    REFRESH_TIME = 5


    def __init___(self):
        self.probes = []
        self.isRunning = True
        # wins and boxes
        self.status = None
        self.commandInput = None
        self.text = None
        self.probesPanel = None
        Thread.__init__(self)
        # assures we end correctly

        # end session
        # curses.endwin()
    
    def run(self):
        try:
            wrapper(self.main)
        finally:
            self.isRunning = False

    def initPanels(self, stdscr):
        Cli.DISPLAY_WIDTH = curses.COLS - 1;
    
        self.text = stdscr.subwin(1, Cli.DISPLAY_WIDTH, 0, 0)
        self.text.addstr(0, 0, "Enter a command :")
        self.text.refresh()

        self.commandInput = stdscr.subwin(Cli.COMMAND_LINE_NUMBER - 2, Cli.DISPLAY_WIDTH, 1, 0)
        self.commandInput.refresh()

        self.status = stdscr.subwin(1, Cli.DISPLAY_WIDTH, Cli.COMMAND_LINE_NUMBER - 1, 0)
        self.updateStatus("Waiting for command ...")

        self.probesPanel = stdscr.subwin(curses.LINES - 1 - Cli.COMMAND_LINE_NUMBER, Cli.DISPLAY_WIDTH, Cli.COMMAND_LINE_NUMBER, 0)
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
            th = Thread(target=self.refreshProbes)
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
            time.sleep(Cli.REFRESH_TIME)

    def fetchProbes(self):
        return []

    # get an area where all the probes can be painted
    def drawProbes(self, probes):
        i = Cli.COMMAND_LINE_NUMBER + 1
        for probe in probes:
            self.probesPanel.addstr(i, 0, probe)
            self.probesPanel.cleartoeol()
            i += 1
        return self.probesPanel;

    def updateStatus(self, newStatus):
        self.status.addstr(0, 0, newStatus)
        self.status.clrtobot()
        self.status.refresh()

    def doCommand(self, command):
        self.updateStatus("Executing command : " + command)
    #     print(command)
        time.sleep(3)
        cmd = Command(Parser(command))
        cmd.start()
        cmd.join()
        self.updateStatus("Command done...")
