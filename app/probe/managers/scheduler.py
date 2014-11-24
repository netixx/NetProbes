"""Scheduler that make the function which calls it wait for some amount of time"""

import math
import threading as th

from .probes import ProbeStorage


MAX_SCHED_DELAY = 3.0

DEFAULT_RETRY=3
DEFAULT_RETRY_INTERVAL=3
_LOG_POWER_ADD = 2

class Scheduler(object):
    """Scheduler makes people wait for a moment"""
    timers = []

    @classmethod
    def addToOverlay(cls):
        n = ProbeStorage.getNumberOfProbes()
        wait = min(MAX_SCHED_DELAY, math.log(n + 1, _LOG_POWER_ADD))
        cls._wait(wait)

    @classmethod
    def forward(cls):
        cls._wait(MAX_SCHED_DELAY * 2)

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


class Retry(object):

    @classmethod
    def retry(cls, times = DEFAULT_RETRY, interval = DEFAULT_RETRY_INTERVAL, failure = Exception, eraise = Exception):
        def tryIt(func):
            def f(*args, **kwargs):
                fail = None
                attempts = 0
                while attempts < times:
                    try:
                        return func(*args, **kwargs)
                    except failure as curfail:
                        fail = curfail
                        if interval > 0:
                            Scheduler._wait(interval)
                        attempts += 1
                if type(fail) is Exception:
                    message = fail.getMessage()
                else:
                    message = "Retry loop ended"
                raise eraise(message)

            return f
        return tryIt
