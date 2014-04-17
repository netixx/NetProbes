"""Module regrouping everything needed in a test to perform a test
Sort of API for tests

"""
from subprocess import Popen, PIPE
import shlex

from managers.probes import ProbeStorage


class TestServices(object):
    """Provides services for tests

    """

    @staticmethod
    def getProbeIpById(probeId):
        """Returns the Ip of a probe given it's Id
        :param probeId: ID of the probe"""
        return ProbeStorage.getProbeById(probeId).getIp()

    @staticmethod
    def getIdAllOtherProbes():
        """Returns the Ids of all the other known probes"""
        return ProbeStorage.getIdAllOtherProbes()

    @staticmethod
    def runCmd(cmd, **popenParams):
        """Run a command and return stdout and stdin to communicate with it
        Uses the Popen methods
        :param cmd : command string to run
        :param popenParams : param to merge with Popen params
        """
        defaultPopenParams = {'stdout': PIPE}
        defaultPopenParams.update(popenParams)
        process = Popen(shlex.split(cmd), **defaultPopenParams)
        return process.communicate()
