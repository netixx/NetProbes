'''
Module gathering the constants of the probe

@author: francois
'''

class Consts(object):
    '''
    The 'real' consts
    '''

    PORT_NUMBER = 5000
    POST_MESSAGE_KEYWORD = "@message"
    POST_MESSAGE_ENCODING = "latin-1"
    COMMANDER_PORT_NUMBER = 6000
    PROPAGATION_RATE = 5
    LOCAL_IP_ADDR = "localhost"
    HTTP_POST_REQUEST = "POST"
    HTTP_GET_REQUEST = "GET"

class Urls(object):
    SRV_TESTS_QUERY = "/tests"
    SRV_ID_QUERY = "/id"
    SRV_STATUS_QUERY = "/status"

class Params(object):
    '''
    Parameters for the runtime
    '''
    DEBUG = False
    COMMANDER = False


class Identification(object):
    '''
    Identification elements of the probe
    '''
    PROBE_ID = "1122334455667788"

    @staticmethod
    def randomId():
        import random
        return '%05x' % random.randrange(16 ** 5)
