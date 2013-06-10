'''
Created on 7 juin 2013

@author: francois
'''

from client import *
from server import Server
from messages import *

if __name__ == '__main__':
    pass



c = Client()
c.start()
c.addProbe("localhost",  "moi" )

msg = Add( "moi", "newProbe", "fakeIP" );
c.

c.quit()
c.join()
print("test")
