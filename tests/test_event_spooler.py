import time
from multiprocessing import Queue

import pytest
import requests
import requests_mock
from requests import HTTPError

from reflexsoar_agent.core.event import EventSpooler
from reflexsoar_agent.core.management import ManagementConnection


@pytest.fixture
def event_queue():
    return Queue()

@pytest.fixture
def mock_host():
    return 'mock://pytest'

@pytest.fixture
def mocked_conn(mock_host):
    conn = ManagementConnection(f'{mock_host}', api_key='foo', name='mock-api')
    mocker = requests_mock.Mocker(session=conn._session)
    adapter = requests_mock.Adapter()
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/event/_bulk', status_code=200, json={'success': True})
    conn._session.mount('mock://', adapter)
    return conn

@pytest.fixture
def event_spooler(event_queue, mocked_conn):

    spooler = EventSpooler(conn=mocked_conn, event_queue=event_queue)
    return spooler

def test_event_spooler_init(event_spooler, event_queue):
    """Tests the EventSpooler initialization and makes sure the objects passed
    in at initialization persisted"""

    assert event_spooler._event_queue == event_queue
    assert event_spooler.conn.name == 'mock-api'

def test_event_spooler_send_event(event_spooler, event_queue, test_event):
    """Checks to see if the EventSpooler is consuming and sending Events
    correctly"""

    event_spooler.start()

    time.sleep(2)
    if event_spooler.is_alive():
        event_queue.put(test_event)
        while not event_queue.empty():
            time.sleep(1)
        assert event_queue.qsize() == 0
        event_spooler.stop()


def test_event_spooler_graceful_stop(event_spooler, event_queue):
    """Tests to see if the EventSpooler can be stopped with a keyboard
    interupt"""

    event_spooler.start()
    time.sleep(1)
    event_spooler.stop()
    assert event_spooler.is_alive() == False
