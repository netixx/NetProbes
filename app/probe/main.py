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

if __name__ == '__main__':
    pass

server = Server()
server.start()
server.isUp.wait()

c = Client()
c.start()

if Params.COMMANDER:
    commander = CommanderServer()
    commander.start();

# c.quit()
# c.join()

# print("done")
