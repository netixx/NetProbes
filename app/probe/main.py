'''
Created on 7 juin 2013

@author: francois
'''

from client import Client
from messages import Add
from server import Server
from probes import ProbeStorage, Probe


if __name__ == '__main__':
    pass

server = Server()
server.start()
server.isUp.wait()

c = Client()
c.start()
input("envoyer les messages");

p = Probe("gaspard", "10.0.0.148")
ProbeStorage.addProbe(p)
c.send(Add("gaspard", "nouveau", "10.0.0.142"))

# c.quit()
# c.join()

# print("done")
