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

    @classmethod
    def runCmd(cls, cmd, **popenParams):
        """Run a command and return stdout and stdin to communicate with it
        Uses the Popen methods
        :param cmd : command string to run
        :param popenParams : param to merge with Popen params
        """
        process = cls.popen(cmd, **popenParams)
        out, err = process.communicate()
        exitcode = process.wait()
        return out, err, exitcode

    @staticmethod
    def popen(cmd, **popenParams):
        defaultPopenParams = {'stdout': PIPE}
        defaultPopenParams.update(popenParams)
        return Popen(shlex.split(cmd), **defaultPopenParams)
