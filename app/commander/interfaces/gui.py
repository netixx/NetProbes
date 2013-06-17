'''
Created on 16 juin 2013

@author: francois
'''
from threading import Thread
from tkinter import *
from interface import Interface
from tkinter.ttk import Treeview
import time

class Gui(Interface):
    PROBE_REFRESH = 10
    TREE_COLUMNS = ("Probe id", "Probe ip")
    
    def __init__(self, ip):
        self.mainWin = Tk()
        self.command = StringVar(self.mainWin)
        self.status = StringVar(self.mainWin, value="Waiting for command ...")
        self.text = StringVar(self.mainWin, value="Enter a command :")
        self.probesDisplay = None
        Interface.__init__(self, ip)
        self.mainWin.title("Commander for probe with ip : " + ip)
        self.isRunning = True
        self.mainWin.protocol("WM_DELETE_WINDOW", self.quit)


    def start(self):
        self.mainWin.geometry('800x600')
        txtText = Label(self.mainWin, textvariable=self.text)
        txtText.grid(row=0, column=0, sticky=W)
#         txtText.pack(side=LEFT)
        txtInput = Entry(self.mainWin, textvariable=self.command, width=30)
#         txtInput.pack(expand=1, fill=X, side=LEFT)
        txtInput.grid(row=0, column=1, sticky=E + W)
        txtInput.bind("<Return>", self.doCommand)

        txtStatus = Label(self.mainWin, textvariable=self.status)
        txtStatus.grid(row=1, columnspan=2, sticky=N + S + E + W)
#         txtStatus.pack(expand=1, fill=X, side=TOP)
        self.probesDisplay = Treeview(self.mainWin, columns=Gui.TREE_COLUMNS, show="headings")
        self.probesDisplay.grid(row=2, columnspan=2, sticky=N + S + E + W)
#         self.probesDisplay.heading(1, text="Probe id")
#         self.probesDisplay.heading(2, text="Probe ip")
#         aProbes.pack(expand=1, fill=BOTH, side=TOP)
        self.mainWin.grid_rowconfigure(2, weight=1)
        self.mainWin.grid_columnconfigure(1, weight=1)
        
        th = Thread(target=self.updateProbes, name="Probe updater", daemon=True)
        th.start()
        self.mainWin.mainloop()
        self.isRunning=False
        th.join()

    def doCommand(self, event):
        return super().doCommand(self.command.get())

    def updateStatus(self, status):
        self.status.set(status)
        
    def updateProbes(self):
        while(self.isRunning):
            probes = self.probesToItems(self.fetchProbes())
            self.probesDisplay.set_children("")
            for item in probes:
                self.probesDisplay.insert('', 'end', values=item)
#             self.probesDisplay.set_children('', probes)
            time.sleep(Gui.PROBE_REFRESH)
    
    @classmethod
    def probesToItems(cls, probes):
        return [(probe.getId(), probe.getIp()) for probe in probes]


    def quit(self):
        self.isRunning = False
        self.mainWin.quit()
