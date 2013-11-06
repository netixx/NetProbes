'''
Created on 7 juin 2013

@author: francois
@todo: catcher connexions impossibles
@todo: gérer les do
@todo: ecrire les tests
@todo: changer l'architecture démarrage
@todo: changer de full mesh à partial
@todo: contraintes de sécurité

'''


import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory)
sys.path.append(directory + "/../common")
sys.path.append(directory + "/../../lib")

from client import Client
from server import Server
from commanderServer import CommanderServer
from probe.consts import Params, Identification
from actionmanager import ActionMan
import argparse
import tools.logs as logs
import logging

LOGGER_NAME = "probe"

def addLogs():
    logger = logging.getLogger(LOGGER_NAME)
    logs.addStdoutAndStdErr(logger)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the commander for a probe')
    parser.add_argument('-id', '--probe-id', metavar='interface',
                   help='Enter an int that represent the id of the probe', default=11223344556677)
    debug = parser.add_mutually_exclusive_group()
    debug.add_argument('--debug',
                    help='Starts the app with debug on', action='store_true')
    debug.add_argument('--no-debug', action='store_true', help='Starts the app with debug off')

    commander = parser.add_mutually_exclusive_group()
    commander.add_argument('--commander',
                    help='Starts the app with debug on', action='store_true')
    commander.add_argument('--no-commander', action='store_true', help='Starts the app with debug off')
    args = parser.parse_args()

    Identification.PROBE_ID = args.probe_id

    if args.debug:
        Params.DEBUG = True
    elif args.no_debug:
        Params.DEBUG = False

    if args.commander:
        Params.COMMANDER = True
    elif args.no_commander:
        Params.COMMANDER = False

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

#     c.send(Add("id", "probeid", "probeip"))
#     c.quit()
#     c.join()
#     print("done")
