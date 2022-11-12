import time
from itertools import islice
from multiprocessing import Process, Queue

from reflexsoar_agent.core.event.base import Event
from reflexsoar_agent.core.event.errors import EventManagedInitializedError
from reflexsoar_agent.core.logging import logger
from reflexsoar_agent.core.management import ManagementConnection


class EventSpooler(Process):

    def __init__(self, conn, event_queue):

        super().__init__()

        self._max_spooled_events = 10000
        self._bulk_size = 100
        self._running = False
        self._awaiting_ack = {}
        self._event_queue = event_queue
        self._event_queue_poll_period = 1
        self.conn = conn

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

        response = self.conn.bulk_events(events)
        if response:
            logger.info(f"Sent {len(events)} to {self.conn.url}")
        else:
            logger.info(f"Failed to send {len(events)} to {self.conn.url}")

    def _process_events(self):
        """Grabs events from the processing queue and pushes them to the API
        """

        while True:
            while not self._event_queue.empty():
                events = []
                while len(events) < self._bulk_size and not self._event_queue.empty():
                    events.append(self._event_queue.get())
                self._send_events(events)
            time.sleep(1)

    def _take(self, size, iterable):
        return list(islice(iterable, size))

    def run(self):
        self._running = True
        logger.info("EventSpooler started")
        while self._running:
            self._process_events()


class EventManager:
    """Defines the EventManager class. The EventManager provides common funcitonality
    for parsing new Events to an Event object from a dictionary when provided a
    list of fields to extract, fields to map to observables, signature fields, etc.
    """

    def __init__(self, conn: ManagementConnection = None, signature_fields: list = None,
                 observable_mapping: dict = None, *args, **kwargs) -> None:
        """Initializes the EventManager class.
        Args:
            conn (ManagementConnection): ManagementConnection object for
                                         interacting with the Management Console.
            signature_fields (list): List of fields for generating an event signature
            observable_mapping (dict): Dictionary of fields to map to observables
        """

        self._initialized = False
        self.back_pressure = 1

        # A ManagementConnection is required
        if conn is None:
            self.management_conn = None
        else:
            self.management_conn = conn
            self._initialized = True

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

        self.event_queue = Queue()

        if self._initialized:
            self._init_spooler(start=True)

    def _init_spooler(self):
        """Initializes the EventSpooler"""
        if self.management_conn:
            logger.info("Initializing EventSpooler")
            self.spooler = EventSpooler(self.management_conn, self.event_queue)
            self.spooler.start()

    def init_event_manager(self, conn):
        """Initializes the EventManager"""
        if self._initialized is False:
            self.management_conn = conn
            self._init_spooler()
            self._initialized = True
        else:
            raise EventManagedInitializedError(
                "The EventManager has already been initialized")

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

    def parse_event(self, event: dict) -> Event:
        """Parses a dictionary into an Event object"""

        # TODO: Add all the Event parsing logic here
        return event

    def _check_spooler_health(self):
        if self.spooler.is_alive() is False:
            logger.error("EventSpooler is not alive.  Restarting...")
            try:
                self._init_spooler()
            except Exception as e:
                logger.error(f"Unable to restart EventSpooler: {e}")

    def prepare_events(self, *events):

        # Makes sure the EventManager is fully initialized
        if self._initialized is False:
            raise EventManagedInitializedError(
                "The EventManager has not been initialized")

        # Check the spooler health before preparing any events
        self._check_spooler_health()

        """Prepares an Event for sending to the Management Console"""
        while self.event_queue.qsize() > self.spooler._max_spooled_events:
            self.back_pressure += 1
            logger.warning("Event queue is full."
                           "Holding events for until queue is free")
            time.sleep(self.back_pressure)

        self.back_pressure = 1

        for event in events:
            if isinstance(event, Event):
                self.event_queue.put(event)
            else:
                parsed_event = self.parse_event(event)
                self.event_queue.put(parsed_event)
        return None


if __name__ == "__main__":

    from threading import Thread

    conn = ManagementConnection(url='http://localhost:5000',
                                api_key='1234', ignore_tls=False, name='test-conn')
    em = EventManager(signature_fields=[
                      'timestamp', 'source', 'source_ip', 'destination', 'destination_ip'])
    em.init_event_manager(conn=conn)

    def send_fake_events(em, thread_id):
        for i in range(0, 500):
            e = {f"test-{i}": "test", "thread_id": thread_id}
            em.prepare_events(e)

    threads = []
    for _ in range(0, 5):
        t = Thread(target=send_fake_events, args=(em, _, ))
        threads.append(t)

    [t.start() for t in threads]
