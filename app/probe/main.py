'''
Created on 7 juin 2013

@author: francois
'''

from client import Client
from messages import Add
from server import Server

if __name__ == '__main__':
    pass

server = Server()
server.start()
server.isUp.wait()

c = Client()
c.start()
 
c.addProbe("localhost",  "moi" )
c.addProbe("localhost",  "aussiMoi" )
c.send( Add( "moi", "newProbe", "fakeIP" ) )


c.quit()
c.join()

# print("done")
