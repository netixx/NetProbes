"""Scheduler that make the function which calls it wait for some amount of time"""

import math
import threading as th

from .probes import ProbeStorage

MAX_SCHED_DELAY=3.0

class Scheduler(object):
    """Scheduler makes people wait for a moment"""
    timers = []

    @classmethod
    def addToOverlay(cls):
        n = ProbeStorage.getNumberOfProbes()
        wait = min(MAX_SCHED_DELAY, math.log10(math.pow(n, 0.7) + 1)/2.0)
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
