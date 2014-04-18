"""Exceptions that can occur in the commander

"""


class NoSuchCommand(Exception):
    """The command you requested does not exist"""

    def __init__(self):
        pass