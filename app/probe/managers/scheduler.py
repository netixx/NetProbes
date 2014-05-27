import math
import threading as th

from .probes import ProbeStorage


class Scheduler(object):
    timers = []

    @classmethod
    def addToOverlay(cls):
        n = ProbeStorage.getNumberOfProbes()
        wait = math.log10(math.pow(n, 1.0 / 3.0) + 1)
        cls._wait(wait)


    @classmethod
    def _wait(cls, time):
        t = Waiter(time)
        cls.timers.append(t)
        t.wait()
        cls.timers.remove(t)

    @classmethod
    def quit(cls):
        for t in cls.timers:
            t.cancel()


class Waiter(th.Thread):
    def __init__(self, interval):
        super().__init__()
        self.interval = interval
        self.finished = th.Event()

    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()

    def run(self):
        self.finished.wait(self.interval)

    def wait(self):
        self.start()
        self.join()
