import json
import time
from itertools import islice
from multiprocessing import Event as mpEvent
from multiprocessing import Process, Queue
from typing import Any, Dict, List, Optional

from reflexsoar_agent.core.event.base import Event
from reflexsoar_agent.core.event.errors import EventManagedInitializedError
from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.core.management import ManagementConnection


class EventSpooler(Process):

    def __init__(self, conn, event_queue):

        super().__init__()

        self._bulk_size = 100
        self._running = False
        self._awaiting_ack = {}
        self._event_queue = event_queue
        self._event_queue_poll_period = 1
        self.conn = conn
        self._should_stop = mpEvent()

    def _listen_for_acks(self):
        """Listens to a pub/sub channel with the API and waits for ACKs
        that a collection of events has been processed
        """
        pass

    def _send_events(self, events):
        """Sends the events to the API and receives a job ID
        The job ID is stored in an awaiting_ack dict with the events that
        need to be removed from the shelve when done
        """
        _events = []
        [_events.append(json.loads(e.jsonify())) for e in events]

        response = self.conn.bulk_events(_events)
        if response:
            logger.info(f"Sent {len(events)} to {self.conn.url}")
        else:
            logger.info(f"Failed to send {len(events)} to {self.conn.url}")

    def _process_events(self):
        """Grabs events from the processing queue and pushes them to the API
        """

        while not self._event_queue.empty():
            if self._running is False:
                break
            events = []
            while len(events) < self._bulk_size and not self._event_queue.empty():
                events.append(self._event_queue.get())
            self._send_events(events)
        time.sleep(1)

    def _take(self, size, iterable):
        return list(islice(iterable, size))

    def run(self):
        try:
            self._running = True
            logger.info("EventSpooler started")
            while self._running:
                if self._should_stop.is_set():
                    self._running = False
                    break
                self._process_events()
        except KeyboardInterrupt:
            logger.info("EventSpooler stopped")
            self._running = False

    def stop(self, from_self=False):
        logger.info(f"Stop of {self.__class__.__name__} requested")
        self._running = False
        self._should_stop.set()
        if not from_self:
            self.join()


class EventManager:
    """Defines the EventManager class. The EventManager provides common funcitonality
    for parsing new Events to an Event object from a dictionary when provided a
    list of fields to extract, fields to map to observables, signature fields, etc.
    """

    def __init__(self, conn: Optional[ManagementConnection] = None,
                 event_queue: Optional[Queue] = None, *args, **kwargs) -> None:
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

        if conn is None:
            self.management_conn = None
        else:
            self.management_conn = conn
            self._initialized = True

        if event_queue:
            self.event_queue = event_queue
        else:
            self.event_queue = Queue()

    def _init_spooler(self):
        """Initializes the EventSpooler"""
        if self.management_conn:
            self.spooler = EventSpooler(self.management_conn, self.event_queue)
            self.spooler.start()
            logger.info("EventSpooler initialized")

    def initialize(self, conn):
        """Initializes the EventManager"""
        if self._initialized is False:
            self.management_conn = conn
            self._init_spooler()
            logger.info("EventManager initialized")
            self._initialized = True
        else:
            raise EventManagedInitializedError(
                "The EventManager has already been initialized")

    @property
    def is_initialized(self):
        return self._initialized

    @is_initialized.setter
    def is_initialized(self, value):
        raise ValueError("Cannot set the is_initialized property")

    def prepare_events(self, *events, base_fields: Optional[Dict[Any, Any]] = None,
                       signature_fields: Optional[List[str]] = None,
                       observable_mapping: Optional[List[Dict[Any, Any]]] = None,
                       source_field: Optional[str] = None,
                       source: Optional[str] = None):
        """Prepares events for sending to the API by converating them to Event objects

        Args:
            events (list): List of events to prepare
            base_fields (dict): Dictionary of fields to add to all events
            signature_fields (list): List of fields to use for generating an event signature
            observable_mapping (list): List of fields to map to observables
        """

        if signature_fields is None:
            signature_fields = []

        if observable_mapping is None:
            observable_mapping = []

        if source is None:
            source = "Unknown"

        # Makes sure the EventManager is fully initialized
        if self._initialized is False:
            raise EventManagedInitializedError(
                "The EventManager has not been initialized")

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
            else:
                event = Event(event, base_fields=base_fields,
                              signature_fields=signature_fields,
                              observable_mapping=observable_mapping,  # type: ignore
                              source_field=source_field,
                              source=source)
                self.event_queue.put(event)
        return None
