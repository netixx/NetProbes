#!/usr/bin/python3
'''
Created on 14 juin 2013

@author: francois
@todo: refresh à volonté
'''

import argparse
import importlib
import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory)
sys.path.append(os.path.abspath(os.path.join(directory, "..")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib")))
sys.path.append(os.path.abspath(os.path.join(directory, "..", "..", "lib", 'tools', 'tools')))

from exceptions import ProbeConnectionFailed

def interfaceFactory(intOption, ip):
    mod = importlib.import_module("interfaces." + intOption)
    return getattr(mod, intOption.capitalize())(ip)
                                
# executed when called but not when imported
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the commander for a probe')
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

    args = parser.parse_args()

    from common.consts import Params as cParams
    from common.protocols import http
    from common.codecs import serialize
    cParams.CODEC = serialize
    cParams.PROTOCOL = http

    try :
        commander = interfaceFactory(args.interface_type, args.ip_probe)
        commander.start()
    except ProbeConnectionFailed as e:
        print("Could not connect to probe %s : (%s)" % (args.ip_probe, e))
    except Exception as e:
        print("Could not start commander : %s" % e)
