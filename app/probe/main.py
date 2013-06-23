'''
Created on 7 juin 2013

@author: francois
@todo: catcher connexions impossibles
@todo : gérer les do
@todo :ecrire les tests
'''
import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory + "/../common")

from client import Client
from messages import Add
from server import Server
from probes import ProbeStorage, Probe
from commanderServer import CommanderServer
from consts import Params, Identification
from actionmanager import ActionMan
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the commander for a probe')
    parser.add_argument('-id', '--probe-id', metavar='interface',
                   help='Enter an int that represent the id of the probe', default=11223344556677)
    debug = parser.add_mutually_exclusive_group()
    debug.add_argument('--debug',
                    help='Starts the app with debug on', action='store_true')
    debug.add_argument('--no-debug', action='store_true', help='Starts the app with debug off')
    args = parser.parse_args()

    Identification.PROBE_ID = args.probe_id

    if args.debug:
        Params.DEBUG = True
    elif args.no_debug:
        Params.DEBUG = False

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
