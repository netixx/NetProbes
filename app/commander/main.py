#!/usr/bin/python3
"""The commander enables control of a remote probe
It allows the user to send specific queries to a remote probe
in order to manipulate the probe overlay or execute tests

@author: francois
"""
import argparse
import importlib
import os
import sys
import logging
from logging import Formatter

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory)
sys.path.append(os.path.abspath(os.path.join(directory, "..")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib", 'tools')))

from common.intfs.exceptions import ProbeConnectionFailed
import tools.logs as logs
import consts


def interfaceFactory(interfaceName):
    """Return interface instance from name
    :param interfaceName: the name of the interface to load
    """
    mod = importlib.import_module("interfaces." + interfaceName)
    return getattr(mod, interfaceName.capitalize())

def addLogs():
    """Add basic logging to STDOUT"""
    logger = logging.getLogger()
    formatter = Formatter(consts.DEFAULT_LOG_FORMAT)

    logs.addStdoutAndStdErr(consts.Params.VERBOSE, logger, formatter)


# executed when called but not when imported
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Starts the commander for a probe')
    parser.add_argument('-i',
                        '--interface-type',
                        metavar = 'interface',
                        dest = 'interface_type',
                        help = 'Choose which interface you which to use this commander with',
                        default = "gui")
    parser.add_argument('-ip',
                        '--ip-probe',
                        metavar = 'ip',
                        dest = 'ip_probe',
                        help = 'The ip of the probe you which to command',
                        default = "127.0.0.1")
    parser.add_argument('-v', '--verbose',
                        dest = 'verbose',
                        action = 'count',
                        default = 0,
                        help = "Set verbosity")
    args = parser.parse_args()

    if args.verbose >= 2:
        consts.Params.VERBOSE = 10
    elif args.verbose == 1:
        consts.Params.VERBOSE = 20
    else:
        consts.Params.VERBOSE = 30

    from common.consts import Params as cParams
    from common.protocols import http
    from common.codecs import serialize

    cParams.CODEC = serialize
    cParams.PROTOCOL = http
    #add logs here to that the interface may modify the logging facility
    addLogs()
    try:

        commander = interfaceFactory(args.interface_type)(args.ip_probe)
        commander.start()
    except ProbeConnectionFailed as e:
        logging.getLogger().error("Could not connect to probe %s : (%s)", args.ip_probe, e, exc_info = 1)
    except Exception as e:
        logging.getLogger().critical("Could not start commander : %s", e, exc_info = 1)
