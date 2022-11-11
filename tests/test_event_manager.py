# noqa:

import os

import pytest

from reflexsoar_agent.core.event import EventManager
from reflexsoar_agent.core.management import ManagementConnection


@pytest.fixture(autouse=True)
def management_connection():
    return ManagementConnection(url="https://localhost", api_key="test", name="foo", register_globally=False)


@pytest.fixture()
def signature_fields():
    return ['test']


@pytest.fixture()
def observable_mapping():
    return {'test': 'test'}


@pytest.fixture()
def event_manager(observable_mapping, signature_fields):
    return EventManager(conn=management_connection, signature_fields=signature_fields, observable_mapping=observable_mapping)


def test_event_manager_init():

    em = EventManager(conn=management_connection, no_persistence=True)

    assert em is not None


def test_event_manager_init_with_args():

    em = EventManager(conn=management_connection, signature_fields=[
                      'test'], observable_mapping={'test': 'test'}, no_persistence=True)

    assert em is not None
    assert em.signature_fields == ['test']
    assert em.observable_mapping == {'test': 'test'}


def test_event_manager_dedicated_persistence_without_name():

    with pytest.raises(ValueError):
        em = EventManager(conn=management_connection, dedicated_persistent_queue=True)


def test_event_manager_dedicated_persistence_with_name():

    em = EventManager(conn=management_connection,
                      dedicated_persistent_queue=True, dedicated_queue_name='test')

    assert em is not None
    assert em._dedicated_persistent_queue == True
    assert em._dedicated_queue_name == 'test'


def test_event_manager_custom_db_path():

    FILE_PATH = "./tests/"
    DB_NAME = "test-db-path/data.db"

    em = EventManager(conn=management_connection, persistence_queue_file_path=FILE_PATH,
                      dedicated_persistent_queue=True, dedicated_queue_name=DB_NAME)
    path_exists = os.path.exists(os.path.join(FILE_PATH, DB_NAME))
    assert path_exists == True


def test_event_manager_prepare_events(event_manager):

    EVENTS = ({'id': 1, 'name': 'test'},)

    count = event_manager.prepare_events(EVENTS)
    assert count == len(EVENTS)
