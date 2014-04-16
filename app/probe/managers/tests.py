from managers.probes import ProbeStorage
from subprocess import Popen, PIPE
import shlex

class TestServices(object):
    '''
    Provides services for tests
    
    '''
    @staticmethod
    def getProbeIpById(probeId):
        '''Returns the Ip of a probe given it's Id'''
        return ProbeStorage.getProbeById(probeId).getIp()

    @staticmethod
    def getIdAllOtherProbes():
        '''Returns the Ids of all the other known probes'''
        return ProbeStorage.getIdAllOtherProbes()
    
    @staticmethod
    def runCmd(cmd, **popenParams):
        defaultPopenParams = {'stdout' : PIPE}
        defaultPopenParams.update(popenParams)
        process = Popen(shlex.split(cmd), **defaultPopenParams)
        return process.communicate()
