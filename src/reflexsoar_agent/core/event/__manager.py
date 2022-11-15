import time
from itertools import islice
from multiprocessing import Queue

from reflexsoar_agent.core.event.base import Event
from reflexsoar_agent.core.event.errors import EventManagedInitializedError
from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.core.management import ManagementConnection


class EventManager:
    """Defines the EventManager class. The EventManager provides common funcitonality
    for parsing new Events to an Event object from a dictionary when provided a
    list of fields to extract, fields to map to observables, signature fields, etc.
    """

    def __init__(self, conn: ManagementConnection = None, *args, **kwargs) -> None:
        """Initializes the EventManager class.
        Args:
            conn (ManagementConnection): ManagementConnection object for
                                         interacting with the Management Console.
            signature_fields (list): List of fields for generating an event signature
            observable_mapping (dict): Dictionary of fields to map to observables
        """

        self._initialized = False
        self.back_pressure = 1
        self._max_spooled_events = 10000
        self._bulk_size = 100

        # A ManagementConnection is required
        if conn is None:
            self.management_conn = None
        else:
            self.management_conn = conn
            self._initialized = True

        self.event_queue = Queue()

        if self._initialized:
            self._init_spooler(start=True)

    def _init_spooler(self):
        """Initializes the EventSpooler"""
        if self.management_conn:
            logger.info("EventSpooler initialized")

    def initialize(self, conn):
        """Initializes the EventManager"""
        if self._initialized is False:
            self.management_conn = conn
            self._init_spooler()
            logger.info("EventManager initialized")
            self._initialized = True

    @property
    def is_initialized(self):
        return self._initialized

    @is_initialized.setter
    def is_initialized(self, value):
        raise ValueError("Cannot set the is_initialized property")

    def _send_events(self, events):
        """Sends the events to the API and receives a job ID
        The job ID is stored in an awaiting_ack dict with the events that
        need to be removed from the shelve when done
        """

        response = self.management_conn.bulk_events(events)
        if response:
            logger.info(f"Sent {len(events)} to {self.management_conn.url}")
        else:
            logger.info(f"Failed to send {len(events)} to {self.management_conn.url}")

    def _process_events(self):
        """Grabs events from the processing queue and pushes them to the API
        """

        while not self.event_queue.empty():
            events = []
            while len(events) < self._bulk_size and not self.event_queue.empty():
                events.append(self.event_queue.get())
            self._send_events(events)
        time.sleep(1)

    def _take(self, size, iterable):
        return list(islice(iterable, size))

    def parse_event(self, event: dict) -> Event:
        """Parses a dictionary into an Event object"""

        # TODO: Add all the Event parsing logic here
        return event

    def prepare_events(self, *events):

        # Makes sure the EventManager is fully initialized
        if self._initialized is False:
            raise EventManagedInitializedError(
                "The EventManager has not been initialized")

        # Check the spooler health before preparing any events
        # self._check_spooler_health()

        """Prepares an Event for sending to the Management Console"""
        while self.event_queue.qsize() > self._max_spooled_events:
            self.back_pressure += 1
            logger.warning("Event queue is full."
                           "Holding events for until queue is free")
            time.sleep(self.back_pressure)

        self.back_pressure = 1

        for event in events:
            if isinstance(event, Event):
                self.event_queue.put(event)

        self._process_events()
        return None
