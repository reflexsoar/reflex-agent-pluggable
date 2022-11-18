import pytest

from reflexsoar_agent.core.event import Event


@pytest.fixture
def test_event():
    event = Event(**{
        'title': 'Test Event',
        'description': 'A test event from pylint',
        'severity': 'low',
        'tlp': 3,
        'tags': ['test', 'pytest'],
        'source': 'pytest',
        'observables': [
            {
                'value': 'test',
                'data_type': 'hostname',
                'tags': ['test', 'pytest'],
                'tlp': 3,
                'spotted': False,
                'safe': False,
                'ioc': False,
                'source_field': 'host.hostname',
                'original_source_field': 'host.hostname'
            }
        ],
        'reference': 'abc-pytest-1234',
        'raw_log': "foobar",
        'detection_id': '1234',
        'risk_score': 1000,
        'original_data': '2022-11-14T00:00:00.000',
    })
    return event
