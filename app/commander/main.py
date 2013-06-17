'''
Created on 14 juin 2013

@author: francois
'''

import argparse
import importlib
import os
import sys

directory = os.path.dirname(os.path.abspath(__file__))
sys.path.append(directory + "/../common")

def interfaceFactory(intOption, ip):
    mod = importlib.import_module("interfaces." + intOption)
    return getattr(mod, intOption.capitalize())(ip)
                                

# executed when called but not when imported
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the commander for a probe')
    parser.add_argument('-i', '--interface-type', metavar='interface', nargs=1,
                   help='Choose which interface you which to use this commander with', default=["gui"])
    parser.add_argument('-ip', '--ip-probe', metavar='ip', nargs=1, help='The ip of the probe you which to command', default=["127.0.0.1"])

    args = parser.parse_args()
    commander = interfaceFactory(args.interface_type[0], args.ip_probe[0])
    commander.start()
