'''
Created on 7 juin 2013

@author: francois
'''

from probe.client import *

if __name__ == '__main__':
    pass

from server import Server

server = Server();

c = Client()
c.start()
c.quit()
c.join()
print("test")
