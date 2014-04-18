"""Gui interface for the commander

@author: francois
"""
from threading import Thread
from tkinter import *
from tkinter.ttk import Treeview

from interface import Interface
import consts


class Gui(Interface):
    """The GUI interface uses the tkinter module to generate
    a window using tk
    """

    TREE_COLUMNS = ("Probe id", "Probe ip", "Status")
    RESULT_DIPLAY_HEIGHT = 10

    def __init__(self, ip):
        Interface.__init__(self, ip)
        self.commandHistory = []
        self.mainWin = Tk()
        self.command = StringVar(self.mainWin)
        self.status = StringVar(self.mainWin, value = "Waiting for command ...")
        self.text = StringVar(self.mainWin, value = "Enter a command :")
        self.result = None
        self.probesDisplay = None
        self.mainWin.title("Commander for probe with ip : " + ip)
        self.isRunning = True
        self.mainWin.protocol("WM_DELETE_WINDOW", self.quit)

        # define the threads
        self.thProbe = Thread(target = self.updateProbes, name = "Probe updater", daemon = True)
        self.thResults = Thread(target = self.updateResults, name = "Results Updater", daemon = True)

    def start(self):
        """Starts (opens) the commander window"""
        self.mainWin.geometry('800x600')
        txtText = Label(self.mainWin, textvariable = self.text)
        txtText.grid(row = 0, column = 0, sticky = W)

        txtInput = Entry(self.mainWin, textvariable = self.command, width = 30)
        txtInput.grid(row = 0, column = 1, sticky = E + W)
        txtInput.bind("<Return>", self.doCommand)
        txtInput.bind("<Up>", self.recallCommand)

        button = Button(self.mainWin, text = "Refresh", fg = "blue", command = self.triggerFetchProbes)
        button.grid(row = 1, column = 0, sticky = N + S + E + W)

        txtStatus = Label(self.mainWin, textvariable = self.status, wraplength = 600, justify = CENTER)
        txtStatus.grid(row = 1, column = 1, sticky = N + S + E + W)

        self.probesDisplay = Treeview(self.mainWin, columns = Gui.TREE_COLUMNS, show = "headings")
        self.probesDisplay.grid(row = 2, columnspan = 2, sticky = N + S + E + W)

        self.result = Text(self.mainWin, textvariable = self.result, height = self.RESULT_DIPLAY_HEIGHT, wrap = WORD)
        self.result.configure(state = DISABLED)
        self.result.grid(row = 3, columnspan = 2, sticky = N + S + E + W)
        self.addResult("Awaiting results .... ")

        self.mainWin.grid_rowconfigure(2, weight = 1)
        self.mainWin.grid_columnconfigure(1, weight = 1)

        self.probeFetcherScheduler()
        self.thProbe.start()

        self.resultFetcherScheduler()
        self.thResults.start()

        self.logger.info("Commander : Starting main window")

        self.mainWin.mainloop()

        self.logger.debug("Commander : mainloop over")

    def recallCommand(self, event):
        """Function to rewrite previous command in box"""
        if len(self.commandHistory) != 0:
            self.command.set(self.commandHistory[-1])
        return "break"

    def doCommand(self, event):
        """Executes user command"""
        self.commandHistory.append(self.command.get())
        self.logger.info("Commander : executing command")
        super().doCommand(self.command.get())
        self.command.set("")

    def updateStatus(self, status):
        """Update status of the probe in status label
        :param status: new status"""
        self.status.set(status)
        self.mainWin.update_idletasks()

    def addResult(self, result):
        """Add (prepend) a result in the result test area
        :param result: the result to add
        """
        self.result.configure(state = NORMAL)
        self.result.insert('1.0', result + "\n")
        self.result.configure(state = DISABLED)

    def setResult(self, result):
        """Put this result in the result area
        :param result: result to put
        """
        self.result.configure(state = NORMAL)
        self.result.set(result)
        self.result.configure(state = DISABLED)


    def updateProbes(self):
        """Update the list of probes in the Treeview"""
        while self.isRunning:
            probes = self.probesToItems(self.fetchProbes())
            self.probesDisplay.set_children("")
            for item in probes:
                self.probesDisplay.insert('', 'end', values = item)
            #             self.probesDisplay.set_children('', probes)
            self.doFetchProbes.wait()

    @staticmethod
    def probesToItems(probes):
        """Transform probe object into lists for display
        :param probes: list of probes to transform
        """
        return [(str(probe.getId()), probe.getIp(), probe.getStatus()) for probe in probes]

    def updateResults(self):
        """Update the results is the box"""
        while self.isRunning:
            result = self.fetchResults()
            self.addResult(result)
            self.doFetchResults.wait()


    def quit(self):
        """Exit and close the commander window"""
        self.logger.info("Commander : exiting commander")
        self.isRunning = False
        self.triggerFetchProbes()
        self.thProbe.join()
        super().quit()
        # no join because answer is blocking...
        #         self.thResults.join()
        self.mainWin.quit()