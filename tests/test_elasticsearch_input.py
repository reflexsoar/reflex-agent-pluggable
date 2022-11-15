import copy
import os

import pytest
from dotenv import load_dotenv

from reflexsoar_agent.input.core.es import ElasticInput

load_dotenv()

@pytest.fixture
def es_config():
    return {
        "hosts": ["https://localhost:9200"],
        "cafile": "",
        "cert_verification": "none",
        "check_hostname": False,
        "auth_method": "basic",
        "index": "winlogbeat-*",
        "search_period": "5m",
        "lucene_filter": "",
        "search_size": 10
    }

@pytest.fixture
def es_connection(es_config):
    credentials = (os.getenv("ES_USER"), os.getenv("ES_PASS"))
    return ElasticInput("test", config=es_config, credentials=credentials)

@pytest.fixture
def os_connection(es_config):
    os_config = copy.copy(es_config)
    os_config['distro'] = 'opensearch'
    credentials = (os.getenv("ES_USER"), os.getenv("ES_PASS"))
    return ElasticInput("test", config=os_config, credentials=credentials)


def test_es_connection(es_connection):
    assert es_connection is not None

def test_es_poll(es_connection):
    events = es_connection.poll()
    assert events is not None
    assert len(events) > 0

def test_es_bad_credentials(es_config):
    """Test that the connection fails with bad credentials. Expects that the
    connection will fail with a AuthenticationException and the number of
    events that return will be 0."""

    bad_es_conn = ElasticInput("test", config=es_config, credentials=("test","badpassword"))

    events = bad_es_conn.poll()
    assert events is not None
    assert len(events) == 0

def test_es_bad_index(es_connection, es_config):
    """Test that the connection fails with a bad index. Expects that the
    connection will fail with a NotFoundError and the number of
    events that return will be 0."""

    es_connection.config['index'] = "badindex-*"

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 0

def test_es_bad_search_period(es_connection, es_config):
    """Test that the connection fails with a bad search period. Expects that the
    connection will fail with a RequestError and the number of
    events that return will be 0."""

    es_connection.config['search_period'] = "badperiod"

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 0

def test_es_bad_search_size(es_connection, es_config):
    """Test that the connection fails with a bad search size. Expects that the
    connection will fail with a RequestError and the number of
    events that return will be 0."""

    #bad_es_conn = ElasticInput("test", config=es_config, credentials=(os.getenv("ES_USER"), os.getenv("ES_PASS")))
    es_connection.config['search_size'] = "badsize"

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 0

def test_es_search_size_works(es_connection, es_config):
    """Checks to make sure that the search size parameter works as expected."""

    #es_conn = ElasticInput("test", config=es_config, credentials=(os.getenv("ES_USER"), os.getenv("ES_PASS")))
    es_connection.config['search_size'] = 1
    es_connection.config['search_period'] = "30s"
    es_connection.config['no_scroll'] = True

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 1

def test_es_search_max_hits(es_connection, es_config):
    """Checks to make sure that the search size parameter works as expected."""

    #es_conn = ElasticInput("test", config=es_config, credentials=(os.getenv("ES_USER"), os.getenv("ES_PASS")))
    es_connection.config['search_size'] = 10
    es_connection.config['search_period'] = "30s"
    es_connection.config['max_hits'] = 10

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 10

def test_es_search_lucene_filter(es_connection, es_config):
    """Checks to make sure that the search size parameter works as expected."""

    es_connection.config['search_size'] = 10
    es_connection.config['lucene_filter'] = "event.code:1"

    events = es_connection.poll()
    assert events is not None
    assert len(events) > 0

    es_connection.config['search_size'] = 10
    es_connection.config['lucene_filter'] = "event.code:1 AND user.name: IDONTEXIST"

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 0


def test_es_search_with_api_key(es_config):
    """Checks to make sure that the search size parameter works as expected."""

    es_config['auth_method'] = 'api_key'
    es_connection = ElasticInput("test", config=es_config, credentials=(os.getenv("ES_API_USER"), os.getenv("ES_API_KEY")))
    events = es_connection.poll()
    assert events is not None

def test_es_as_opensearch(os_connection):
    """Checks to make sure the opensearch variation of this input works correctly."""

    events = os_connection.poll()
    assert events is not None
    assert len(events) > 0


def test_es_search_no_index(es_connection):
    """Checks to make sure no data is returned when no index is specified."""

    es_connection.config['search_size'] = 10
    es_connection.config['index'] = None

    events = es_connection.poll()
    assert events is not None
    assert len(events) == 0

def test_es_search_unknown_distro_with_http_auth(es_config):
    """Checks to make sure that the search size parameter works as expected."""

    es_config2 = copy.copy(es_config)

    es_config2['distro'] = "bad_distro"
    es_config2['http_auth'] = ()

    es_connection = ElasticInput("test", config=es_config2, credentials=(os.getenv("ES_USER"), os.getenv("ES_PASS")))

    events = es_connection.poll()
    assert events is not None
    assert len(events) > 0

def test_es_search_retry(es_config):
    """Checks to make sure that the search size parameter works as expected."""

    bad_config = copy.copy(es_config)
    bad_config['hosts'] = ['https://localhost:9000']

    bad_connection = ElasticInput("test", config=bad_config, credentials=("test","badpassword"))

    events = bad_connection.poll()
    assert events is not None
    assert len(events) == 0
