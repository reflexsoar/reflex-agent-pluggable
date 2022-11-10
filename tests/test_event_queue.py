import os
import pytest
from platformdirs import user_data_dir
from reflexsoar_agent.role.core.event import EventQueue

@pytest.fixture(autouse=True)
def db_path():
    return os.path.join(user_data_dir(appname='reflexsoar-agent', appauthor='reflexsoar'), 'agent-event-queue')

@pytest.fixture(autouse=True)
def db_teardown():
    yield
    db_path = os.path.join(user_data_dir(appname='reflexsoar-agent', appauthor='reflexsoar'), 'agent-event-queue')
    if os.path.exists(db_path):
        os.remove(os.path.join(db_path, 'data.db'))

def test_event_queue_init(db_path):

    eq = EventQueue()
    eq.put('test')   
    assert os.path.exists(db_path) == True
    
def test_event_queue_put(db_path):

    eq = EventQueue()
    eq.put('test')
    assert eq.q._count() > 0

def test_event_queue_put_and_get(db_path):

    eq = EventQueue()
    _id = eq.put('test')
    assert eq.get() == 'test'
