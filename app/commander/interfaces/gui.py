'''
Created on 16 juin 2013

@author: francois
'''

from tkinter import *
from interface import Interface
from tkinter.ttk import Treeview

class Gui(Interface):

    def __init__(self, ip):
        self.mainWin = Tk()
        self.command = StringVar(self.mainWin)
        self.status = StringVar(self.mainWin, value="Waiting for command ...")
        self.text = StringVar(self.mainWin, value="Enter a command :")
        self.probesDisplay = []
        Interface.__init__(self, ip)
        self.mainWin.title("Commander for probe with ip : " + ip)


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
        aProbes = Treeview(self.mainWin)
        aProbes.grid(row=2, columnspan=2, sticky=N + S + E + W)
#         aProbes.pack(expand=1, fill=BOTH, side=TOP)
        self.mainWin.grid_rowconfigure(2, weight=1)
        self.mainWin.grid_columnconfigure(1, weight=1)

        self.mainWin.mainloop()

    def doCommand(self, event):
        return super().doCommand(self.command.get())

    def updateStatus(self, status):
        self.status.set(status)
