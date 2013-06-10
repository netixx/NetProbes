
'''
A simple server that read and display anything received on port 5000
'''




import socket, sys
HOST = 'localhost'
PORT = 5000
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    mySocket.bind((HOST, PORT))
except socket.error:
    print("La liaison du socket a l'adresse choisie a echoue.")
    sys.exit()
    
print ("Serveur pret, en attente de requetes ...")
mySocket.listen(5)
connexion, adresse = mySocket.accept()
print ("Client connecte, adresse IP %s, port %s" % (adresse[0], adresse[1]))
msgClient = connexion.recv(1024)
while 1:
    if msgClient != "" and msgClient != b'':
        print ("C>", msgClient)
    msgClient = connexion.recv(1024)

print ("Connexion interrompue.")
connexion.close()