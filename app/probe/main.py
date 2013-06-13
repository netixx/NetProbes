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

p = Probe("id", "127.0.0.1")
ProbeStorage.addProbe(p)
c.send(Add("id", "newProbe", "fakeIP"))

# c.quit()
# c.join()

# print("done")
