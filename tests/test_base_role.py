import time
import pytest

from reflexsoar_agent.role.base import BaseRole
from reflexsoar_agent.core.management import ManagementConnection

@pytest.fixture
def mock_connection():
    return ManagementConnection('https://localhost', api_key='test', name='test')

def test_base_role():
    """Tests that importing worked"""
    assert BaseRole

def test_base_role_shortname():
    """Tests that the shortname is set"""
    assert BaseRole.shortname == 'base'

def test_base_role_guard():
    """Tests that the role guard works"""

    with pytest.raises(TypeError):
        class NewRole(BaseRole):
            def set_config():
                super().set_config()

        n = NewRole()

def test_new_role_from_base():
    """Tests that a new role can be created from the base role"""
    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({}, connections={})

    assert new_role.shortname == 'new'


def test_base_role_get_connections(mock_connection):
    """Tests all the different connection helpers for getting new
    http and management connections"""

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({}, connections={'test': mock_connection})

    assert new_role.get_connection('test') == mock_connection

    nc = ManagementConnection('https://localhost', api_key='test', name='shared')

    new_role.share_connection(nc)
    assert new_role.get_connection('shared') == nc

    new_role.unshare_connection('shared')
    assert new_role.get_connection('shared') == None

def test_base_role_load_inputs():
    """Tests to see if the load_inputs method works"""

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({}, connections={})

    new_role.load_inputs()
    assert len(new_role.loaded_inputs) > 0


def test_base_role_main(caplog):

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole(config={'wait_interval': 10}, connections={})

    new_role.main()
    assert 'Hello World from new' in caplog.text

def test_base_role_without_config():

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({}, connections={})
    assert new_role.config['wait_interval'] == 10


def test_base_role_with_wait_interval_missing():

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({'random': 'abc'}, connections={})
    assert new_role.config['wait_interval'] == 10


def test_base_role_repr():
    """Tests the __repr__ method"""

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({}, connections={})
    assert 'NewRole' in str(new_role)

def test_base_role_start_stop():
    """Makes sure that the start and stop functions work correctly"""

    new_role = BaseRole({}, connections={})
    new_role.start()
    assert new_role.is_alive() == True
    new_role.stop()
    assert new_role.is_alive() == False

def test_base_role_run():

    class NewRole(BaseRole):
        shortname = 'new'

    new_role = NewRole({}, connections={})
    new_role.disable_run_loop = True
    new_role.run()

    new_role.disable_run_loop = False
    new_role.max_loop_count = 1
    new_role.run()
    assert new_role._should_stop.is_set() == True


