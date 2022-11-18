import os
import re
import json
import pytest
import uuid
import requests
import requests_mock

from reflexsoar_agent.agent import Agent, cli
from reflexsoar_agent.core.management import ManagementConnection, remove_management_connection


@pytest.fixture
def agent_config():
    return {
        "uuid": "test",
        "roles": [
            "poller"
        ],
        "role_configs": {
            "poller_config": {
                "wait_interval": 10
            }
        },
        "console_info": {
            "url": "mock://localhost",
            "api_key": "foobar"
        },
        "name": "BRIAN-PC",
        "policy_revision": 0,
        "policy_uuid": "",
        "event_cache_key": "signature",
        "event_cache_ttl": 30,
        "disable_event_cache_check": False,
        "health_check_interval": 30
    }


@pytest.fixture
def agent_policy():
    return {}


@pytest.fixture
def mock_host():
    return 'mock://localhost'


@pytest.fixture
def agent_matcher(mock_host):
    return re.compile(f'{mock_host}/api/v2.0/agent(/.*|)')


@pytest.fixture
def mocked_mgmt_conn(mock_host):
    conn = ManagementConnection
    mocker = requests_mock.Mocker(session=conn._session)
    adapter = requests_mock.Adapter()
    adapter.register_uri(
        'POST', f'{mock_host}/api/v2.0/agent/heartbeat/test', status_code=200, json={'success': True})
    adapter.register_uri('POST', f'{mock_host}/api/v2.0/agent',
                         status_code=200, json={'access_token': 'foobar'})
    conn._session.mount('mock://', adapter)


@pytest.fixture
def agent(agent_config):
    return Agent(agent_config, persistent_config_path='tests/agent_test_config')


def test_agent_clear_pairing(mock_host, agent_matcher):

    with requests_mock.Mocker() as m:
        m.post(agent_matcher, status_code=200, json={
               'token': 'foo', 'uuid': str(uuid.uuid4())})
        cli(['--pair', '--pair-skip-start', '--console', mock_host,
            '--token', 'foobar', '--config-path', 'tests/agent_test_config'])
        cli(['--reset-console-pairing', mock_host,
            '--config-path', 'tests/agent_test_config'])
        remove_management_connection('default')
        agent = Agent(persistent_config_path='tests/agent_test_config')
        assert agent.config.console_info == {}


def test_agent_set_value():

    cli(['--set-config-value', 'roles:', '--config-path', 'tests/agent_test_config'])
    cli(['--set-config-value', 'health_check_interval:10',
        '--config-path', 'tests/agent_test_config'])
    cli(['--set-config-value',
        'role_configs:{"poller_config":{"wait_interval":10}}', '--config-path', 'tests/agent_test_config'])
    cli(['--set-config-value', 'disable_event_cache_check:true',
        '--config-path', 'tests/agent_test_config'])
    agent = Agent(persistent_config_path='tests/agent_test_config')
    assert agent.config.roles == []
    assert agent.config.health_check_interval == 10
    assert agent.config.role_configs['poller_config']['wait_interval'] == 10
    assert agent.config.disable_event_cache_check == True

def test_agent_view_config(capsys):

    cli(['--view-config', '--config-path', 'tests/agent_test_config'])
    out,err = capsys.readouterr()
    assert "Configuration Preview" in out

def test_agent_init(agent_matcher, mock_host):

    with requests_mock.Mocker() as m:
        m.post(agent_matcher, status_code=200, json={
               'token': 'foo', 'uuid': str(uuid.uuid4())})
        m.get(agent_matcher, status_code=200, json={'inputs': []})
        cli(['--pair', '--pair-skip-start', '--console', mock_host,
            '--token', 'foobar', '--config-path', 'tests/agent_test_config'])


def test_agent_clear_persistent_config():

    cli(['--clear-persistent-config', '--config-path', 'tests/agent_test_config'])
    assert not os.path.exists('tests/agent_test_config/persistent-config.json')
