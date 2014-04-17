"""Constants for use by the commander and the commander server

@author: francois
"""
import common.intfs.codec as codec
import common.intfs.protocol as protocol


class Params(object):
    """Common params, including commander server protocol and codecs"""
    PROTOCOL = protocol
    CODEC = codec
    
