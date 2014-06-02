# !/usr/bin/python3
# coding=UTF-8
"""A probe is a program that can be used to perform test between nodes
running the same program. It provides synchronisation needed to perform tests
and can be commanded remotely if the --commander option is given

Main launcher for the probe
    Sets the global variables (constants and variables read from the command line)
    Initialises the logging facilities
    Starts the different threads

@author: francois
todo: catcher connexions impossibles
todo: security
todo: Do availability index with : current queue sizes, current number of tests
@todo: overlay id (take part to multiple overlays)
"""

import os
import sys

from calls import actions
from consts import Consts


directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory)
sys.path.append(os.path.abspath(os.path.join(directory, "..")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib", 'tools')))

DATA_DIR = os.path.join(directory, "..", "..", "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
WATCHERS_LOGS_DIR = os.path.join(LOGS_DIR, "watchers")

LOG_FORMAT = Consts.DEFAULT_LOG_FORMAT
TEST_LOGS_FORMAT = "%(levelname)s\t%(asctime)s %(name)s (%(module)s)\t: %(message)s"

from threading import Lock
import signal
import time
from interfaces.watcher import WatcherError
from managers.probetests import TEST_LOGGER
from managers.actions import ActionMan
from inout.client import Client
from inout.server import Server
from inout.commanderServer import CommanderServer
from managers.watchers import WatcherManager
from consts import Params, Identification
import argparse
import tools.logs as logs
import logging
from managers.watchers import WATCHER_LOGGER
from logging import Formatter
from managers.scheduler import Scheduler

DDEBUG = 9

wlogger = logging.getLogger(WATCHER_LOGGER)
# tlogger = logging.getLogger()
def addLogs():
    """Add logs to the program"""
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    if not os.path.exists(LOGS_DIR):
        os.mkdir(LOGS_DIR)
    if not os.path.exists(WATCHERS_LOGS_DIR):
        os.mkdir(WATCHERS_LOGS_DIR)

    if Params.WATCHERS:
        wlogger.propagate = False
        wlogger.setLevel(logging.DEBUG)
        wlogger.addHandler(
            logging.FileHandler(os.path.join(WATCHERS_LOGS_DIR, Identification.PROBE_ID + 'watcher.log'), mode = 'w'))

    logging.addLevelName(DDEBUG, "DDEBUG")

    def ddebug(logger, msg, *args, **kwargs):
        """Verbose debugging function"""
        logger.log(DDEBUG, msg, *args, **kwargs)

    logging.Logger.ddebug = ddebug

    logger = logging.getLogger()
    logLevel = Params.VERBOSE

    formatter = Formatter(LOG_FORMAT)

    logs.addStdoutAndStdErr(logLevel, logger, formatter)

    # TODO: readd file logs when tests are done
    logs.addDailyRotatingHandler(os.path.join(LOGS_DIR, Identification.PROBE_ID + "_probe.log"), 30, logger, formatter, logLevel = logLevel)

    testLogger = logging.getLogger(TEST_LOGGER)
    testFormatter = Formatter(TEST_LOGS_FORMAT)

    logs.addDailyRotatingHandler(os.path.join(LOGS_DIR, Identification.PROBE_ID + "_tests.log"), 30, testLogger, testFormatter, logLevel = logLevel)
    testLogger.propagate = True


if __name__ == '__main__':
    stopped = False
    stopLock = Lock()

    def printStacks(*args):
        from tools.debugger import strStacks

        out = strStacks()
        out += "Action queue : %s\n" % repr(ActionMan.actionQueue.queue)
        out += "Message queue : %s\n" % repr(Client.messageStack.queue)
        logging.getLogger().info(out)

    def shutdown(signum = None, frame = None):
        with stopLock:
            global stopped
            if stopped:
                return
            else:
                stopped = True
        logging.getLogger().info("Shutting down probe")
        Scheduler.quit()
        if Params.COMMANDER and commander is not None:
            commander.quit()
        from calls.actions import Quit

        if Params.WATCHERS:
            WatcherManager.stopWatchers()
        from managers.probetests import TestManager, TestResponder

        TestManager.stopTests()
        TestResponder.stopTests()
        if actionMan is not None:
            ActionMan.addTask(Quit())
        if server is not None:
            server.quit()
        if actionMan is not None:
            actionMan.quit()
        #everybody might need the client so stop it last
        if client is not None:
            client.quit()

    def catchSignals():
        # other catchable signals : SIGFPE, SIGILL, SIGSEGV
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT, signal.SIGABRT]:
            signal.signal(sig, shutdown)
        #catch SIGUSR1 for debugging
        signal.signal(signal.SIGUSR1, printStacks)


    parser = argparse.ArgumentParser(description = 'Starts the commander for a probe')
    parser.add_argument('-id', '--probe-id',
                        dest = 'probe_id',
                        metavar = 'probeId',
                        help = 'Enter an string that represent the id of the probe',
                        default = Identification.randomId())

    parser.add_argument('-v', '--verbose',
                        dest = 'verbose',
                        action = 'count',
                        default = 0,
                        help = "Set verbosity.")

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

    parser.add_argument('-w', '--wait',
                        dest = 'wait',
                        default = 0,
                        type = int,
                        help = 'Seconds to wait before starting')

    args = parser.parse_args()

    Identification.PROBE_ID = args.probe_id

    if args.verbose >= 3:
        Params.VERBOSE = DDEBUG
    elif args.verbose == 2:
        Params.VERBOSE = logging.DEBUG
    elif args.verbose <= 1:
        Params.VERBOSE = logging.INFO

    if args.commander:
        Params.COMMANDER = True

    if len(args.watchers) > 0:
        Params.WATCHERS = True

    from inout.codec import deflate_serialize
    from inout.protocol import http

    Params.PROTOCOL = http
    Params.CODEC = deflate_serialize

    from common.codecs import serialize as cserialize
    from common.protocols import http as chttp
    from common.consts import Params as cParams

    cParams.PROTOCOL = chttp
    cParams.CODEC = cserialize

    addLogs()
    server = None
    actionMan = None
    client = None
    commander = None
    catchSignals()
    try:
        time.sleep(args.wait)
        logging.getLogger().info("Starting probe with id : %s, pid : %s", Identification.PROBE_ID, os.getpid())
        server = Server()
        server.start()
        server.isUp.wait()

        actionMan = ActionMan()
        actionMan.start()

        if Params.COMMANDER:
            commander = CommanderServer()
            commander.start()

        if Params.WATCHERS:
            for watcher in args.watchers:
                parts = watcher.partition('=')
                try:
                    WatcherManager.registerWatcher(parts[0], parts[2], wlogger)
                except WatcherError as e:
                    logging.getLogger().warning("Starting watcher failed : %s", e, exc_info = 1)

        # ProbeStorage.addProbe( Probe("id", "10.0.0.1" ) )
        client = Client()
        client.start()
        client.isUp.wait()
        logging.getLogger().info("Startup Done")

        for prefix in args.add_prefix:
            logging.getLogger().info("Adding probes in prefix %s", prefix)
            ActionMan.manageAddPrefix(actions.AddPrefix(prefix))
            logging.getLogger().info("Probe(s) in prefix %s committed for addition", prefix)

        if Params.WATCHERS:
            WatcherManager.startWatchers()
        server.join()
        client.join()
        actionMan.join()

    except KeyboardInterrupt:
        logging.getLogger().info("Caught keyboard interrupt")
    except:
        logging.getLogger().critical("Critical error in probe", exc_info = 1)
    finally:
        shutdown()
        logging.getLogger().info("Shutdown complete")

