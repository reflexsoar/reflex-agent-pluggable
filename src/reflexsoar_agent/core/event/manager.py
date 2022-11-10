import os

import persistqueue
from platformdirs import user_data_dir

from .encoders import JSONSerializable


class Observable(JSONSerializable):
    """Observable class for handling individual observables. Observables are
    attached to Events for shipping to the Management Console.
    """


class Event(JSONSerializable):
    """Creates a Event class for working with individual events"""

    def __init__(self):
        pass


class EventManager:
    """Defines the EventManager class. The EventManager provides common funcitonality
    for parsing new Events to an Event object from a dictionary when provided a
    list of fields to extract, fields to map to observables, signature fields, etc.
    """

    def __init__(self, *args, **kwargs):
        pass


class EventQueue:
    """Defines the EventQueue class.  The EventQueue class is utilized by
    every EventManager to store and process Events before sending them to the
    connection defined in the EventManager
    """

    def __init__(self, *args, **kwargs):
        self.file_path = kwargs.get('file_path', user_data_dir(
            appname='reflexsoar-agent', appauthor='reflexsoar'))
        self.db_name = kwargs.get('db_name', 'agent-event-queue')

        database_path = os.path.join(self.file_path, self.db_name)

        self.q = persistqueue.SQLiteQueue(database_path, auto_commit=True)

    def get(self):
        return self.q.get()

    def put(self, item):
        self.q.put(item)

    def close(self):
        self.q.__del__()
