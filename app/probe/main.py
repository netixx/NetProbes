'''
Created on 7 juin 2013

@author: francois
'''

from client import Client
from messages import Add
from server import Server
from probes import ProbeStorage, Probe
from commanderServer import CommanderServer
from consts import Params
from actionmanager import ActionMan
import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory + "/../common")

if __name__ == '__main__':
    server = Server()
    server.start()
    server.isUp.wait()

    a = ActionMan()
    a.start()

    if Params.COMMANDER:
        commander = CommanderServer()
        commander.start();

    # ProbeStorage.addProbe( Probe("id", "10.0.0.1" ) )
    c = Client()
    c.start()
    c.isUp.wait()



    # c.send( Add("id", "probeid", "probeip") )
    # c.quit()
    # c.join()
    # print("done")
