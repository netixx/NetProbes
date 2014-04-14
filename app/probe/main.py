#!/usr/bin/python3
# coding=UTF-8
'''
Main launcher for the probe.
    Sets the global variable (constants and variables read from the command line)

Created on 7 juin 2013

@author: francois
@todo: catcher connexions impossibles
@todo: gerer les do
@todo: ecrire les tests
@todo: changer l'architecture demarrage
@todo: contraintes de securite

'''

import os
import sys
from calls import actions
from interfaces.watcher import WatcherError

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory)
sys.path.append(os.path.abspath(os.path.join(directory, "..")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib", 'tools')))

DATA_DIR = os.path.join(directory, "..", "..", "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

LOG_FORMAT = "%(levelname)s\t%(asctime)s %(threadName)s (%(module)s)\t: %(message)s"
TEST_LOG_FORMAT = "%(levelname)s\t%(asctime)s %(name)s (%(module)s)\t: %(message)s"

from managers.tests import LOGGER_NAME as TESTS_LOGGER_NAME
from managers.actions import ActionMan
from inout.client import Client
from inout.server import Server
from inout.commanderServer import CommanderServer
from managers.watchers import WatcherManager
from consts import Params, Identification
import argparse
import tools.logs as logs
import logging

from logging import Formatter

def addLogs():
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    if not os.path.exists(LOGS_DIR):
        os.mkdir(LOGS_DIR)

    DDEBUG = 9
    logging.addLevelName(DDEBUG, "DDEBUG")
    def ddebug(logger, msg, *args, **kwargs):
        logger.log(DDEBUG, msg, *args, **kwargs)

    logging.Logger.ddebug = ddebug

    logger = logging.getLogger()
    logLevel = logging.INFO
    if Params.DEBUG:
        logLevel = logging.DEBUG

    formatter = Formatter(LOG_FORMAT)

    logs.addStdoutAndStdErr(logLevel, logger, formatter)

    # TODO: readd file logs when tests are done
#     logs.addDailyRotatingHandler(os.path.join(LOGS_DIR, "probe.log"), 30, logger, formatter)

    testLogger = logging.getLogger(TESTS_LOGGER_NAME);
    testFormatter = Formatter(TEST_LOG_FORMAT)

#     logs.addDailyRotatingHandler(os.path.join(LOGS_DIR, "tests.log"), 30, testLogger, testFormatter)
    testLogger.propagate = True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the commander for a probe')
    parser.add_argument('-id', '--probe-id',
                        dest = 'probe_id',
                        metavar = 'probeId',
                        help = 'Enter an string that represent the id of the probe',
                        default = Identification.randomId())

    parser.add_argument('--debug',
                    dest = 'debug',
                    action = 'store_true',
                    help = "Enable debug mode.")

    parser.add_argument('--commander',
                    dest = 'commander',
                    action = 'store_true',
                    help = "Start the commander server with this probe.")
    
    parser.add_argument('--watchers',
                        dest = 'watchers',
                        action = 'append',
                        default = [],
                        help = 'Daemon to start with the probe for background monitoring purposes')

    parser.add_argument('--add-prefix',
                        dest = 'add_prefix',
                        action = 'append',
                        default = [],
                        help = 'Prefix to scan to add probes automatically')


    args = parser.parse_args()

    Identification.PROBE_ID = args.probe_id

    if args.debug:
        Params.DEBUG = True

    if args.commander:
        Params.COMMANDER = True

    if len(args.watchers) > 0:
        Params.WATCHERS = True

    from inout.codec import serialize
    from inout.protocol import http

    Params.PROTOCOL = http
    Params.COMMANDER_PROTOCOL = http
    Params.CODEC = serialize

    from common.codecs import serialize as cserialize
    from common.protocols import http as chttp
    from common.consts import Params as cParams
    cParams.PROTOCOL = chttp
    cParams.CODEC = cserialize

    addLogs()

    try :
        server = None
        a = None
        c = None
        commander = None
        logging.getLogger().info("Starting probe with id : %s, pid : %s", Identification.PROBE_ID, os.getpid())
        server = Server()
        server.start()
        server.isUp.wait()
    
        a = ActionMan()
        a.start()
    
        if Params.COMMANDER:
            commander = CommanderServer()
            commander.start();

        if Params.WATCHERS:
            for watcher in args.watchers:
                parts = watcher.partition('=')
                try:
                    WatcherManager.registerWatcher(parts[0], parts[2])
                except WatcherError as e:
                    logging.getLogger().warning("Starting watcher failed : %s", e, exc_info = 1)
    
        # ProbeStorage.addProbe( Probe("id", "10.0.0.1" ) )
        c = Client()
        c.start()
        c.isUp.wait()
        logging.getLogger().info("Startup Done")

        for prefix in args.add_prefix:
            logging.getLogger().info("Adding probes in prefix %s", prefix)
            ActionMan.manageAddPrefix(actions.AddPrefix(prefix))
            logging.getLogger().info("Probe(s) in prefix %s added", prefix)

        if Params.WATCHERS:
            WatcherManager.startWatchers()
        server.join()
        c.join()
        a.join()

    except KeyboardInterrupt:
        logging.getLogger().info("Caught keyboard interrupt")
    except :
        logging.getLogger().critical("Critical error in probe", exc_info = 1)
    finally:
        if Params.COMMANDER and commander is not None:
            commander.quit()
        from calls.actions import Quit
        if Params.WATCHERS:
            WatcherManager.stopWatchers()
        ActionMan.addTask(Quit())
        if server is not None:
            server.quit()
        if c is not None:
            c.quit()
        if a is not None:
            a.quit()
        logging.getLogger().info("Shutdown complete")

