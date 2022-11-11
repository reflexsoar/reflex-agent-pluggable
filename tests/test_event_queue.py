# noqa:

import os
from multiprocessing import Manager, Process

import pytest
from platformdirs import user_data_dir

from reflexsoar_agent.core.event import EventQueue


@pytest.fixture()
def db_path():
    return os.path.join(user_data_dir(appname='reflexsoar-agent',
                                      appauthor='reflexsoar'),
                        'agent-event-queue')


@pytest.fixture(autouse=True)
def db_teardown(db_path):
    yield
    if os.path.exists(db_path):
        os.remove(os.path.join(db_path, 'data.db'))


def test_event_queue_init(db_path):

    eq = EventQueue()
    eq.put('test')

    if os.path.exists(db_path):
        assert 1==1


def test_event_queue_put():

    eq = EventQueue()
    eq.put('test')
    assert eq.queue._count() > 0


def push_to_queue(value):
    eq = EventQueue()
    eq.put(value)


def pull_from_queue(check_value, success):
    eq = EventQueue()
    value = eq.get()
    if value == check_value:
        success.value = True
    return


def test_multiprocessing_event_queue(db_teardown):

    mpm = Manager()
    success = mpm.Value(bool, False)
    procs = []
    value = "foobar"

    # Push
    proc = Process(target=push_to_queue, args=(value,))
    procs.append(proc)
    proc.start()

    # Pull
    proc = Process(target=pull_from_queue, args=(value, success, ))
    procs.append(proc)
    proc.start()

    for proc in procs:
        proc.join()
    if success.value == True:
        assert 1==1
    assert success.value == True


def test_event_queue_put_and_get():

    eq = EventQueue()
    _id = eq.put('test')
    assert eq.get() == 'test'
