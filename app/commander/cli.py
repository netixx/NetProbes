'''
Created on 7 juin 2013

@author: francois
'''

import curses
from curses import wrapper
import time
from curses.textpad import Textbox
from threading import Thread

DISPLAY_WIDTH = 100
COMMAND_LINE_NUMBER = 3
REFRESH_TIME = 5
probes = []
isRunning = True

# wins and boxes
status = None
commandInput = None
text = None
probesPanel = None

def initPanels(stdscr):
    global DISPLAY_WIDTH
    DISPLAY_WIDTH = curses.COLS - 1;

    global text
    text = stdscr.subwin(1, DISPLAY_WIDTH, 0, 0)
    text.addstr(0, 0, "Enter a command :")
    text.refresh()
    
    global commandInput
    commandInput = stdscr.subwin(COMMAND_LINE_NUMBER - 2, DISPLAY_WIDTH, 1, 0)
    commandInput.refresh()
    
    global status
    status = stdscr.subwin(1, DISPLAY_WIDTH, COMMAND_LINE_NUMBER - 1, 0)
    updateStatus("Waiting for command ...")

    global probesPanel
    probesPanel = stdscr.subwin(curses.LINES - 1 - COMMAND_LINE_NUMBER, DISPLAY_WIDTH, COMMAND_LINE_NUMBER, 0)
    probesPanel.refresh()

    # move the cursor at the right place
    stdscr.move(1, 0)

def main(stdscr):
    try:
        global isRunning
        global commandInput
    #   stdscr = curses.initscr()
        # Clear screen
        stdscr.clear()
        # remove the cursor
        curses.curs_set(True)
        # remove echo from touched keys
        # curses.noecho()
        initPanels(stdscr)

        box = Textbox(commandInput)
    #     stdscr.refresh()
        th = Thread(target=refreshProbes)
        th.start()
        stdscr.refresh()

        while(True):
            stdscr.refresh()
            box.edit()
            doCommand(box.gather())
    #         commandInput.refresh()

        # listen without entering enter
        # curses.cbreak())
    finally:
        isRunning = False
        th.join()
        # let curses handle special keys
        stdscr.keypad(True)
        stdscr.refresh()
        stdscr.getkey()

def refreshProbes():
    global probesPanel
    global isRunning
    while(isRunning):
        drawProbes(fetchProbes())
        probesPanel.refresh()
        time.sleep(REFRESH_TIME)

def fetchProbes():
    return []

# get an area where all the probes can be painted
def drawProbes(probes):
    global probesPanel
    i = COMMAND_LINE_NUMBER + 1
    for probe in probes:
        probesPanel.addstr(i, 0, probe)
        probesPanel.cleartoeol()
        i += 1
    return probesPanel;

def updateStatus(newStatus):
    global status
    status.addstr(0, 0, newStatus)
    status.clrtobot()
    status.refresh()

def doCommand(command):
    updateStatus("Executing command : " + command)
#     print(command)
    time.sleep(10)
    updateStatus("Command done...")

# assures we end correctly
wrapper(main)
isRunning = False
# end session
# curses.endwin()

