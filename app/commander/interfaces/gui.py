'''
Created on 16 juin 2013

@author: francois
'''
from threading import Thread
from tkinter import *
from interface import Interface
from tkinter.ttk import Treeview
import consts

class Gui(Interface):

    TREE_COLUMNS = ("Probe id", "Probe ip")
    RESULT_DIPLAY_HEIGHT = 10
    def __init__(self, ip):
        self.commandHistory = []
        self.mainWin = Tk()
        self.command = StringVar(self.mainWin)
        self.status = StringVar(self.mainWin, value="Waiting for command ...")
        self.text = StringVar(self.mainWin, value="Enter a command :")
        self.result = None
        self.probesDisplay = None
        self.mainWin.title("Commander for probe with ip : " + ip)
        self.isRunning = True
        self.mainWin.protocol("WM_DELETE_WINDOW", self.quit)
        Interface.__init__(self, ip)
        # define the threads
        self.thProbe = Thread(target=self.updateProbes, name="Probe updater", daemon=True)
        self.thProbeTrigger = Thread(target=self.probeFetcherScheduler, name="Probe Scheduler", daemon=True)
        self.thResults = Thread(target=self.updateResults, name="Results Updater", daemon=True)
        self.thResultsTrigger = Thread(target=self.resultFetcherScheduler, name="Results Scheduler", daemon=True)


    def start(self):
        self.mainWin.geometry('800x600')
        txtText = Label(self.mainWin, textvariable=self.text)
        txtText.grid(row=0, column=0, sticky=W)

        txtInput = Entry(self.mainWin, textvariable=self.command, width=30)
        txtInput.grid(row=0, column=1, sticky=E + W)
        txtInput.bind("<Return>", self.doCommand)
        txtInput.bind("<Up>", self.recallCommand)
        
        button = Button(self.mainWin, text="Refresh", fg="blue", command=self.triggerFetchProbes)
        button.grid(row=1, column=0, sticky=N + S + E + W)
        
        txtStatus = Label(self.mainWin, textvariable=self.status, wraplength=600, justify=CENTER)
        txtStatus.grid(row=1, column=1, sticky=N + S + E + W)
        
        self.probesDisplay = Treeview(self.mainWin, columns=Gui.TREE_COLUMNS, show="headings")
        self.probesDisplay.grid(row=2, columnspan=2, sticky=N + S + E + W)

        self.result = Text(self.mainWin, textvariable=self.result, height=self.RESULT_DIPLAY_HEIGHT, wrap=WORD)
        self.result.configure(state=DISABLED)
        self.result.grid(row=3, columnspan=2, sticky=N + S + E + W)
        self.addResult("Awaiting results .... ")


        self.mainWin.grid_rowconfigure(2, weight=1)
        self.mainWin.grid_columnconfigure(1, weight=1)
        
        self.thProbeTrigger.start()
        self.thProbe.start()

        self.thResultsTrigger.start()
        self.thResults.start()

        consts.debug("Commander : Starting main window")

        self.mainWin.mainloop()

        consts.debug("Commander : mainloop over")

    def recallCommand(self, event):
        if (self.commandHistory != None):
            self.command.set(self.commandHistory[-1])
        return "break"

    def doCommand(self, event):
        self.commandHistory.append(self.command.get())
        consts.debug("Commander : executing command")
        super().doCommand(self.command.get())
        self.command.set("")

    def updateStatus(self, status):
        self.status.set(status)
        self.mainWin.update_idletasks()
        
    def addResult(self, result):
        self.result.configure(state=NORMAL)
        self.result.insert(END, result + "\n")
        self.result.configure(state=DISABLED)

    def setResult(self, result):
        self.result.configure(state=NORMAL)
        self.result.set(result)
        self.result.configure(state=DISABLED)


    def updateProbes(self):
        while(self.isRunning):
            probes = self.probesToItems(self.fetchProbes())
            self.probesDisplay.set_children("")
            for item in probes:
                self.probesDisplay.insert('', 'end', values=item)
#             self.probesDisplay.set_children('', probes)
            self.doFetchProbes.wait()

    @staticmethod
    def probesToItems(probes):
        return [(str(probe.getId()), probe.getIp()) for probe in probes]

    def updateResults(self):
        while(self.isRunning):
            print("fetching results")
            result = self.fetchResults()
            self.addResult(result)
            print("results fetched")
            self.doFetchResults.wait()
            print("going for another loop")


    def quit(self):
        consts.debug("Commander : exiting commander")
#         self.mainWin.quit()
        self.isRunning = False
        # terminate fetch threads
        self.triggerFetchProbes()
        self.triggerFetchResult()
        self.thProbe.join()
        # no joint because answer is blocking...
#         self.thResults.join()
        # closing connection etc...
        super().quit()
        self.mainWin.quit()
        # no join because triggers might be sleeping...
#         self.thProbeTrigger.join()
#         self.thResultsTrigger.join()

