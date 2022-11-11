import os

import persistqueue
from platformdirs import user_data_dir

from reflexsoar_agent.core.management import ManagementConnection

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

    def __init__(self, conn: ManagementConnection, signature_fields: list = None,
                 observable_mapping: dict = None, *args, **kwargs) -> None:
        """Initializes the EventManager class.
        Args:
            conn (ManagementConnection): ManagementConnection object for
                                         interacting with the Management Console.
            signature_fields (list): List of fields for generating an event signature
            observable_mapping (dict): Dictionary of fields to map to observables
        """

        # A ManagementConnection is required
        if conn is None:
            raise ValueError(
                "EventManager requires a ManagementConnection, conn cannot be None")

        # Set defaults for signature_fields
        if signature_fields is None:
            self.signature_fields = []
        else:
            self.signature_fields = signature_fields

        # Set defaults for observable_mapping
        if observable_mapping is None:
            self.observable_mapping = {}
        else:
            self.observable_mapping = observable_mapping

        self._no_persistence = kwargs.get('no_persistence', False)
        if self._no_persistence is False:

            # If set the EventManager will use its own EventQueue for storing
            # persistent Events, this setting requires a name be provided for
            # the EventQueue
            self._dedicated_persistent_queue = kwargs.get(
                'dedicated_persistent_queue', False)
            self._dedicated_queue_name = kwargs.get('dedicated_queue_name', None)
            self._persistence_queue_file_path = kwargs.get(
                'persistence_queue_file_path', None)
            if self._dedicated_persistent_queue and self._dedicated_queue_name is None:
                raise ValueError("dedicated_queue_name cannot be None"
                                 " if dedicated_persistent_queue is True")

            # Create the persistence queue
            self.persistent_queue = self._init_persistence_queue()

        # Store all the _ids of the Events currently in the queue and what
        # time they were stored there
        self._prepared_event_ids = {}

        # The maximum number of prepared events that can reside in
        # _prepared_event_ids.  Raise an exception if this limit is reached and
        # do not except new Events
        self.max_queue_size = kwargs.get('max_queue_size', 10000)

        # The maximum number of seconds that the EventManager should wait
        # for new Events to be prepared before sending them to the Management
        # Console
        self.send_after_seconds = kwargs.get('send_after_seconds', 60)

    @property
    def signature_fields(self):
        return self._signature_fields

    @signature_fields.setter
    def signature_fields(self, value):
        if isinstance(value, list):
            self._signature_fields = value
        else:
            raise ValueError("signature_fields must be a list")

    @property
    def observable_mapping(self):
        return self._observable_mapping

    @observable_mapping.setter
    def observable_mapping(self, value):
        if isinstance(value, dict):
            self._observable_mapping = value
        else:
            raise ValueError("observable_mapping must be a dict")

    def _init_persistence_queue(self) -> "EventQueue":
        """Initializes a persistqueue for storing Events"""
        return EventQueue(db_name=self._dedicated_queue_name,
                          file_path=self._persistence_queue_file_path)

    def send_events(self):
        """Sends events to the Management Console"""
        pass

    def prepare_events(self, *events):
        """Prepares an Event for sending to the Management Console"""
        return len(events)


class EventQueue:
    """Defines the EventQueue class.  The EventQueue class is utilized by
    every EventManager to store and process Events before sending them to the
    connection defined in the EventManager
    """

    def __init__(self, *args, **kwargs):
        """Initializes the EventQueue class"""

        self.file_path = kwargs.get('file_path', user_data_dir(
            appname='reflexsoar-agent', appauthor='reflexsoar'))
        self.db_name = kwargs.get('db_name', 'agent-event-queue')

        if self.file_path and self.db_name:
            database_path = os.path.join(self.file_path, self.db_name)
            self._queue = persistqueue.SQLiteQueue(database_path, auto_commit=True)
        else:
            self._queue = None

    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, value):
        raise AttributeError("Cannot set the queue attribute")

    def get(self):
        """Retrieves an item from the queue"""
        return self._queue.get()

    def put(self, item):
        """Places an item into the queue"""
        self._queue.put(item)

    def close(self):
        self._queue.__del__()
