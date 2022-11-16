import pytest
import requests
import requests_mock

from reflexsoar_agent.core.errors import (AgentHeartbeatFailed,
                                          ConnectionNotExist,
                                          ConsoleAlreadyPaired,
                                          ConsoleInternalServerError,
                                          DuplicateConnectionName)
from reflexsoar_agent.core.management import (HTTPConnection,
                                              ManagementConnection,
                                              add_management_connection,
                                              build_connection,
                                              build_http_connection,
                                              get_management_connection,
                                              remove_management_connection)


@pytest.fixture
def mock_host():
    return 'mock://localhost'

@pytest.fixture
def mocked_conn(mock_host):
    conn = HTTPConnection(f'{mock_host}', api_key='foo', name='mock-api')
    mocker = requests_mock.Mocker(session=conn._session)
    adapter = requests_mock.Adapter()
    adapter.register_uri('POST', f'{mock_host}/test', status_code=200, json={'success': True})
    adapter.register_uri('GET', f'{mock_host}/test', status_code=200, json={'success': True})
    adapter.register_uri('GET', f'{mock_host}/http_error', exc=requests.exceptions.HTTPError)
    adapter.register_uri('GET', f'{mock_host}/conn_error', exc=requests.exceptions.ConnectionError)
    conn._session.mount('mock://', adapter)
    return conn

@pytest.fixture
def mocked_mgmt_conn(mock_host):
    conn = ManagementConnection(f'{mock_host}', api_key='foo', name='mock-api')
    mocker = requests_mock.Mocker(session=conn._session)
    adapter = requests_mock.Adapter()
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/agent/heartbeat/123', status_code=200, json={'success': True})
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/agent/heartbeat/failed', status_code=401, json={'success': False})
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/agent', [
        {'status_code': 200, 'json': {'token': 'successtoken'}},
        {'status_code': 409},
        {'status_code': 500}])
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/event/_bulk', [
        {'status_code': 200, 'json': {'success': True}},
        {'status_code': 500}])
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/agent_409', status_code=409)
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/agent_500', status_code=500)
    adapter.register_uri('GET', f'{mock_host}/api/v2.0/agent/123', status_code=200, json={'policy': {'health_check_interval':10}})
    adapter.register_uri('GET', f'{mock_host}/api/v2.0/agent/456', status_code=404)
    adapter.register_uri('GET', f'{mock_host}/api/v2.0/agent/inputs', [
        {'status_code': 200, 'json': {'inputs': [{'uuid':'abc123'}]}},
        {'status_code': 404}])
    adapter.register_uri('GET', f'{mock_host}/api/v2.0/credential/123', status_code=200, json={'username':'foo'})
    adapter.register_uri('GET', f'{mock_host}/api/v2.0/credential/decrypt/123', status_code=200, json={'secret':'bar'})
    adapter.register_uri('GET', f'{mock_host}/http_error', exc=requests.exceptions.HTTPError)
    adapter.register_uri('GET', f'{mock_host}/conn_error', exc=requests.exceptions.ConnectionError)
    conn._session.mount('mock://', adapter)
    return conn

def test_http_connection_init(mocked_conn):
    """Tests the HTTPConnection initialization"""
    assert mocked_conn.name == 'mock-api'
    assert mocked_conn.api_key == 'foo'
    assert mocked_conn.url == 'mock://localhost'

def test_http_connection_set_header(mocked_conn):
    """Tests the HTTPConnection set_header method"""
    mocked_conn.update_header('foo', 'bar')
    assert mocked_conn._session.headers['foo'] == 'bar'

def test_http_call_api(mocked_conn):
    """Tests the HTTPConnection call_api method"""
    response = mocked_conn.call_api('GET', '/test')
    assert response is not None
    assert response.json() == {'success': True}

def test_http_call_api_slashed_endpoint(mocked_conn):
    """Tests to make sure any endpoint format is passed to the call_api method
    correctly"""

    response = mocked_conn.call_api('GET', 'test')
    assert response is not None
    assert response.json() == {'success': True}

    response = mocked_conn.call_api('GET', 'test/')
    assert response is not None
    assert response.json() == {'success': True}

    response = mocked_conn.call_api('GET', '/test')
    assert response is not None
    assert response.json() == {'success': True}

def test_http_call_api_post(mocked_conn):
    """Tests sending data via the HTTPConnection call_api POST method"""

    response = mocked_conn.call_api('POST', '/test', data={'foo':'bar'})
    assert response is not None
    assert response.json() == {'success': True}

def test_http_call_register_globally(mocked_conn):
    """Tests that the register_globally method works correctly"""

    xconn = HTTPConnection(f'{mock_host}', api_key='foo', name='mock-api', register_globally=True)
    conn = get_management_connection('mock-api')
    assert conn is not None

def test_http_config_view(mocked_conn):

    config = mocked_conn.config
    assert isinstance(config, dict)

def test_http_error(mocked_conn, caplog):

    response = mocked_conn.call_api('GET', '/http_error')
    assert "Failed to make a call to" in caplog.text

    response = mocked_conn.call_api('GET', '/conn_error')
    assert "Failed to connect to" in caplog.text

def test_management_connection_register():
    """Tests the helper functions for managing global connection registry"""

    conn = HTTPConnection('https://localhost', api_key="", name='test')
    add_management_connection(conn)

    # Test adding a connection that already exists
    with pytest.raises(DuplicateConnectionName):
        add_management_connection(conn)

    # Test getting a connection that doesn't exist
    assert get_management_connection('foo') is None

    # Test removing a connection then trying to remove it again
    remove_management_connection(conn)
    with pytest.raises(ConnectionNotExist):
        remove_management_connection(conn)

def test_build_helpers():
    """Tests the helper functions for building connections
    """

    mgmt_conn = build_connection('https://localhost', api_key="", name='test')
    assert isinstance(mgmt_conn, ManagementConnection)
    assert mgmt_conn.name == 'test'

    http_conn = build_http_connection('https://localhost', api_key="", name='http-test')
    assert isinstance(http_conn, HTTPConnection)
    assert http_conn.name == 'http-test'


def test_management_connection_agent_get_inputs(mocked_mgmt_conn):
    """Tests the ManagementConnection get_agent_inputs method"""

    inputs = mocked_mgmt_conn.agent_get_inputs()
    assert inputs is not None
    assert inputs == [{'uuid':'abc123'}]

    inputs = mocked_mgmt_conn.agent_get_inputs()
    assert inputs.status_code == 404


def test_management_connection_agent_get_input_credentials(mocked_mgmt_conn):
    """Tests the agent_get_input_credentials method"""

    creds = mocked_mgmt_conn.agent_get_input_credentials('123')
    assert creds is not None
    assert creds[0] == 'foo'
    assert creds[1] == 'bar'

def test_management_connection_agent_heartbeat(mocked_mgmt_conn):
    """Tests the agent_heartbeat method"""

    response = mocked_mgmt_conn.agent_heartbeat('123', {})
    assert response is not None
    assert response == {'success': True}

    with pytest.raises(AgentHeartbeatFailed):
        mocked_mgmt_conn.agent_heartbeat('failed', {})

def test_management_connection_agent_pair(mocked_mgmt_conn):
    """Tests the agent_pair method"""

    response = mocked_mgmt_conn.agent_pair({'foo':'bar'})
    assert response is not None
    assert response == {'token': 'successtoken'}
    assert mocked_mgmt_conn._session.headers['Authorization'] == 'Bearer successtoken'


    with pytest.raises(ConsoleAlreadyPaired):
        response = mocked_mgmt_conn.agent_pair({'foo':'bar'})


    with pytest.raises(ConsoleInternalServerError):
        response = mocked_mgmt_conn.agent_pair({'foo':'bar'})


def test_management_connection_agent_get_policy(mocked_mgmt_conn):
    """Tests the agent_get_policy method"""

    policy = mocked_mgmt_conn.agent_get_policy('123')
    assert policy is not None
    assert policy == {'health_check_interval': 10}

    policy = mocked_mgmt_conn.agent_get_policy('456')
    assert policy.status_code == 404

def test_management_connection_bulk_events(mocked_mgmt_conn):
    """Tests the bulk_events method"""

    response = mocked_mgmt_conn.bulk_events([{'foo':'bar'}])
    assert response is not None
    assert response == {'success': True}

    mocked_mgmt_conn.bulk_events([{'foo':'bar'}])
