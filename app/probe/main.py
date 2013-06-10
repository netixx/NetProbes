'''
Created on 7 juin 2013

@author: francois
'''

from client import Client
from messages import Add

if __name__ == '__main__':
    pass


c = Client()
c.start()
 
c.addProbe("localhost",  "moi" )
c.addProbe("localhost",  "aussiMoi" )

c.send( Add( "moi", "newProbe", "fakeIP" ) )


c.quit()
c.join()
print("fin")

# 
# from server import Server
# try :
#     server = Server()
#     server.start()
#     
# #     c = Client()
# #     c.start()
# except KeyboardInterrupt :
#     server.quit()
# #     c.quit()

